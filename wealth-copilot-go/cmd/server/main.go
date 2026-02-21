package main

import (
	"context"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/wealth-copilot/wealth-copilot-go/internal/adapter/broker"
	"github.com/wealth-copilot/wealth-copilot-go/internal/adapter/executor"
	"github.com/wealth-copilot/wealth-copilot-go/internal/adapter/marketdata"
	"github.com/wealth-copilot/wealth-copilot-go/internal/adapter/postgres"
	"github.com/wealth-copilot/wealth-copilot-go/internal/config"
	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
	"github.com/wealth-copilot/wealth-copilot-go/internal/handler"
	"github.com/wealth-copilot/wealth-copilot-go/internal/service/geopolitics"
	"github.com/wealth-copilot/wealth-copilot-go/internal/service/risk"
	"github.com/wealth-copilot/wealth-copilot-go/internal/service/scoring"
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

	slog.Info("starting wealth-copilot",
		"addr", cfg.Server.Addr(),
		"broker_mode", cfg.Broker.Mode,
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
	mockMarketData := marketdata.NewMock()
	paperBroker := broker.NewPaper(mockMarketData, domain.Money{Amount: 1_000_000, Currency: domain.CurrencyINR})
	executorClient := executor.NewClient(cfg.Executor.URL, time.Duration(cfg.Executor.Timeout)*time.Second)

	// Services
	riskManager := risk.NewManager()
	scorer := scoring.NewScorer()
	geoEngine := geopolitics.NewEngine()

	// Handlers
	handlers := handler.Handlers{
		Health:       handler.NewHealthHandler(dbCheck),
		Market:       handler.NewMarketHandler(mockMarketData),
		Scoring:      handler.NewScoringHandler(scorer),
		Risk:         handler.NewRiskHandler(riskManager),
		Portfolio:    handler.NewPortfolioHandler(paperBroker),
		Trade:        handler.NewTradeHandler(paperBroker, riskManager),
		Goal:         handler.NewGoalHandler(nil), // GoalsPort adapter pending
		CrossBorder:  handler.NewCrossBorderHandler(nil), // CrossBorderPort adapter pending
		Geopolitics:  handler.NewGeopoliticsHandler(geoEngine),
		Chat:         handler.NewChatHandler(),
		Notification: handler.NewNotificationHandler(),
		Skill:        handler.NewSkillHandler(executorClient),
		Knowledge:    handler.NewKnowledgeHandler(executorClient),
		Domain:       handler.NewDomainHandler(executorClient),
		Platform:     handler.NewPlatformHandler(executorClient),
		Events:       handler.NewEventsHandler(executorClient),
		Memory:       handler.NewMemoryHandler(executorClient),
	}

	mwCfg := handler.MiddlewareConfig{
		AuthEnabled:    cfg.Auth.Enabled,
		CORSOrigins:    cfg.CORS.AllowedOrigins,
		RateLimitRPS:   cfg.RateLimit.RequestsPerSecond,
		RateLimitBurst: cfg.RateLimit.Burst,
	}

	router := handler.NewRouter(handlers, mwCfg)

	srv := &http.Server{
		Addr:         cfg.Server.Addr(),
		Handler:      router,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Graceful shutdown
	go func() {
		sigCh := make(chan os.Signal, 1)
		signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
		<-sigCh
		slog.Info("shutting down server")

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
