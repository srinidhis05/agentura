package main

import (
	"context"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/internal/adapter/postgres"
	"github.com/agentura-ai/agentura/gateway/internal/config"
	ghtoken "github.com/agentura-ai/agentura/gateway/internal/github"
	"github.com/agentura-ai/agentura/gateway/internal/handler"
	"github.com/agentura-ai/agentura/gateway/internal/service"
)

func main() {
	// Load config
	cfgPath := "config/config.yaml"
	if envPath := os.Getenv("CONFIG_PATH"); envPath != "" {
		cfgPath = envPath
	}

	cfg, err := config.Load(cfgPath)
	if err != nil {
		slog.Error("failed to load config", "error", err)
		os.Exit(1)
	}

	// Setup structured logging
	setupLogging(cfg.Logging)

	slog.Info("starting agentura-gateway",
		"addr", cfg.Server.Addr(),
		"auth_enabled", cfg.Auth.Enabled,
	)

	// Database (optional — graceful if unavailable)
	var dbCheck func() error
	db, err := postgres.NewDB(cfg.Database.DSN())
	if err != nil {
		slog.Warn("database unavailable, running without persistence", "error", err)
	} else {
		if err := postgres.AutoMigrate(db); err != nil {
			slog.Warn("auto-migrate failed", "error", err)
		}
		dbCheck = postgres.HealthCheck(db)
	}

	// Adapters
	executorClient := executor.NewClient(cfg.Executor.URL, time.Duration(cfg.Executor.Timeout)*time.Second)

	// Execution dispatcher — determines how skill executions are isolated
	var dispatcher executor.ExecutionDispatcher
	switch cfg.Execution.Mode {
	case "docker":
		dispatcher = executor.NewDockerDispatcher(cfg.Execution.Docker)
		slog.Info("execution mode: docker", "image", cfg.Execution.Docker.Image)
	case "kubernetes":
		dispatcher = executor.NewK8sDispatcher(cfg.Execution.Kubernetes)
		slog.Info("execution mode: kubernetes",
			"namespace", cfg.Execution.Kubernetes.Namespace,
			"image", cfg.Execution.Kubernetes.Image,
		)
	default:
		dispatcher = executor.NewProxyDispatcher(executorClient)
		slog.Info("execution mode: proxy", "executor_url", cfg.Executor.URL)
	}

	// Cron scheduler
	scheduler := service.NewScheduler(executorClient, cfg.Triggers)

	// Heartbeat runner — LLM-as-coordinator pattern
	var heartbeatRunner *service.HeartbeatRunner
	if cfg.Triggers.Enabled && cfg.Triggers.Heartbeat.Enabled && len(cfg.Agents) > 0 {
		heartbeatRunner = service.NewHeartbeatRunner(executorClient, cfg.Agents, cfg.Triggers.Slack.Apps)
		slog.Info("heartbeat runner configured", "agents", len(cfg.Agents))
	}

	// Slack webhook handler (conditional — only if enabled with apps configured)
	var slackHandler *handler.SlackWebhookHandler
	if cfg.Triggers.Slack.Enabled && len(cfg.Triggers.Slack.Apps) > 0 {
		slackHandler = handler.NewSlackWebhookHandler(executorClient, cfg.Triggers.Slack)
		slog.Info("slack webhook enabled", "apps", len(cfg.Triggers.Slack.Apps))

		// Start Socket Mode connections for apps with mode: "socket"
		socketMgr := handler.NewSlackSocketManager(executorClient, cfg.Triggers.Slack)
		socketMgr.Start(context.Background())
	}

	// GitHub App token provider (generates fresh installation tokens per request)
	// Read PEM directly from env — YAML config can't handle multi-line PEM values.
	var githubTokenProvider handler.GitHubTokenProvider
	ghCfg := cfg.Triggers.GitHub
	privateKeyPEM := ghCfg.PrivateKey
	if pk := os.Getenv("GITHUB_APP_PRIVATE_KEY"); pk != "" {
		privateKeyPEM = pk
	}
	tp, err := ghtoken.NewTokenProvider(ghCfg.AppID, privateKeyPEM, ghCfg.InstallationID)
	if err != nil {
		slog.Error("failed to initialize GitHub token provider, falling back to static token", "error", err)
	}
	if tp != nil {
		githubTokenProvider = tp
		slog.Info("github app token provider initialized", "app_id", ghCfg.AppID)
	} else if ghCfg.Token != "" {
		slog.Info("github using static token (no app credentials configured)")
	}

	// Handlers
	handlers := handler.Handlers{
		Health:    handler.NewHealthHandler(dbCheck),
		Chat:      handler.NewChatHandler(),
		Skill:     handler.NewSkillHandler(executorClient, dispatcher),
		Knowledge: handler.NewKnowledgeHandler(executorClient),
		Domain:    handler.NewDomainHandler(executorClient),
		Platform:  handler.NewPlatformHandler(executorClient),
		Events:    handler.NewEventsHandler(executorClient),
		Memory:    handler.NewMemoryHandler(executorClient),
		Webhook:   handler.NewWebhookHandler(executorClient, cfg.Triggers.Webhook),
		GitHub:    handler.NewGitHubWebhookHandler(executorClient, cfg.Triggers.GitHub, githubTokenProvider),
		Slack:     slackHandler,
		Trigger:   handler.NewTriggerHandler(scheduler),
		Pipeline:  handler.NewPipelineHandler(executorClient),
		Fleet:     handler.NewFleetHandler(executorClient),
		Agent:     handler.NewAgentHandler(executorClient),
		Ticket:    handler.NewTicketHandler(executorClient),
		Heartbeat: handler.NewHeartbeatHandler(executorClient),
	}

	mwCfg := handler.MiddlewareConfig{
		AuthEnabled:    cfg.Auth.Enabled,
		CORSOrigins:    cfg.CORS.AllowedOrigins,
		RateLimitRPS:   cfg.RateLimit.RequestsPerSecond,
		RateLimitBurst: cfg.RateLimit.Burst,
	}

	router := handler.NewRouter(handlers, mwCfg)

	// Start cron scheduler and heartbeat runner before HTTP server
	scheduler.Start(context.Background())
	if heartbeatRunner != nil {
		heartbeatRunner.Start(context.Background())
	}

	srv := &http.Server{
		Addr:         cfg.Server.Addr(),
		Handler:      router,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: time.Duration(cfg.Executor.Timeout) * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Graceful shutdown
	go func() {
		sigCh := make(chan os.Signal, 1)
		signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
		<-sigCh
		slog.Info("shutting down server")

		scheduler.Stop()
		if heartbeatRunner != nil {
			heartbeatRunner.Stop()
		}

		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()

		if err := srv.Shutdown(ctx); err != nil {
			slog.Error("server shutdown error", "error", err)
		}
	}()

	slog.Info("server listening", "addr", cfg.Server.Addr())
	if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		slog.Error("server error", "error", err)
		os.Exit(1)
	}
	slog.Info("server stopped")
}

func setupLogging(cfg config.LoggingConfig) {
	var h slog.Handler
	opts := &slog.HandlerOptions{}

	switch cfg.Level {
	case "debug":
		opts.Level = slog.LevelDebug
	case "warn":
		opts.Level = slog.LevelWarn
	case "error":
		opts.Level = slog.LevelError
	default:
		opts.Level = slog.LevelInfo
	}

	if cfg.Format == "text" {
		h = slog.NewTextHandler(os.Stdout, opts)
	} else {
		h = slog.NewJSONHandler(os.Stdout, opts)
	}

	slog.SetDefault(slog.New(h))
}
