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
		GitHub:    handler.NewGitHubWebhookHandler(executorClient, cfg.Triggers.GitHub),
		Trigger:   handler.NewTriggerHandler(scheduler),
	}

	mwCfg := handler.MiddlewareConfig{
		AuthEnabled:    cfg.Auth.Enabled,
		CORSOrigins:    cfg.CORS.AllowedOrigins,
		RateLimitRPS:   cfg.RateLimit.RequestsPerSecond,
		RateLimitBurst: cfg.RateLimit.Burst,
	}

	router := handler.NewRouter(handlers, mwCfg)

	// Start cron scheduler before HTTP server
	scheduler.Start(context.Background())

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
