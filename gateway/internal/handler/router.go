package handler

import (
	"net/http"

	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/agentura-ai/agentura/gateway/internal/middleware"
)

type Handlers struct {
	Health    *HealthHandler
	Chat      *ChatHandler
	Skill     *SkillHandler
	Knowledge *KnowledgeHandler
	Domain    *DomainHandler
	Platform  *PlatformHandler
	Events    *EventsHandler
	Memory    *MemoryHandler
	Webhook   *WebhookHandler
	GitHub    *GitHubWebhookHandler
	Trigger   *TriggerHandler
}

func NewRouter(h Handlers, mw MiddlewareConfig) http.Handler {
	mux := http.NewServeMux()

	// Health — no auth
	mux.HandleFunc("GET /healthz", h.Health.Healthz)
	mux.HandleFunc("GET /readyz", h.Health.Readyz)

	// Metrics — no auth
	mux.Handle("GET /metrics", promhttp.Handler())

	// API routes — auth applied
	api := http.NewServeMux()

	// Chat
	api.HandleFunc("POST /api/v1/chat/message", h.Chat.SendMessage)

	// Skills (proxied to Python executor)
	if h.Skill != nil {
		api.HandleFunc("POST /api/v1/skills", h.Skill.CreateSkill)
		api.HandleFunc("GET /api/v1/skills", h.Skill.ListSkills)
		api.HandleFunc("GET /api/v1/skills/{domain}/{skill}", h.Skill.GetSkill)
		api.HandleFunc("POST /api/v1/skills/{domain}/{skill}/execute", h.Skill.ExecuteSkill)
		api.HandleFunc("POST /api/v1/skills/{domain}/{skill}/correct", h.Skill.Correct)
		api.HandleFunc("GET /api/v1/executions", h.Skill.ListExecutions)
		api.HandleFunc("GET /api/v1/executions/{execution_id}", h.Skill.GetExecution)
		api.HandleFunc("POST /api/v1/executions/{execution_id}/approve", h.Skill.ApproveExecution)
		api.HandleFunc("GET /api/v1/analytics", h.Skill.GetAnalytics)
	}

	// Knowledge Layer (proxied to Python executor)
	if h.Knowledge != nil {
		api.HandleFunc("GET /api/v1/knowledge/reflexions", h.Knowledge.ListReflexions)
		api.HandleFunc("GET /api/v1/knowledge/corrections", h.Knowledge.ListCorrections)
		api.HandleFunc("GET /api/v1/knowledge/tests", h.Knowledge.ListTests)
		api.HandleFunc("GET /api/v1/knowledge/stats", h.Knowledge.GetStats)
		api.HandleFunc("POST /api/v1/knowledge/search/{domain}/{skill}", h.Knowledge.SemanticSearch)
		api.HandleFunc("POST /api/v1/knowledge/validate/{domain}/{skill}", h.Knowledge.ValidateTests)
	}

	// Domains (proxied to Python executor)
	if h.Domain != nil {
		api.HandleFunc("GET /api/v1/domains", h.Domain.ListDomains)
		api.HandleFunc("GET /api/v1/domains/{domain}", h.Domain.GetDomain)
	}

	// Platform health (proxied to Python executor)
	if h.Platform != nil {
		api.HandleFunc("GET /api/v1/platform/health", h.Platform.GetHealth)
	}

	// Memory Explorer (proxied to Python executor)
	if h.Memory != nil {
		api.HandleFunc("GET /api/v1/memory/status", h.Memory.GetStatus)
		api.HandleFunc("POST /api/v1/memory/search", h.Memory.Search)
		api.HandleFunc("GET /api/v1/memory/prompt-assembly/{domain}/{skill}", h.Memory.GetPromptAssembly)
	}

	// Events (proxied to Python executor)
	if h.Events != nil {
		api.HandleFunc("GET /api/v1/events", h.Events.ListEvents)
	}

	// Webhook inbound — external channels POST here
	if h.Webhook != nil {
		api.HandleFunc("POST /api/v1/channels/{channel}/inbound", h.Webhook.Inbound)
	}

	// GitHub webhook — no auth (uses signature verification)
	if h.GitHub != nil {
		mux.HandleFunc("POST /api/v1/webhooks/github", h.GitHub.Handle)
	}

	// Trigger status — cron scheduler info
	if h.Trigger != nil {
		api.HandleFunc("GET /api/v1/triggers", h.Trigger.ListTriggers)
		api.HandleFunc("GET /api/v1/triggers/status", h.Trigger.Status)
	}

	// Apply auth middleware to API routes
	authedAPI := middleware.Auth(mw.AuthEnabled)(api)
	mux.Handle("/api/", authedAPI)

	// Apply global middleware stack
	handler := middleware.Chain(
		mux,
		middleware.Recovery,
		middleware.RequestID,
		middleware.CORS(mw.CORSOrigins),
		middleware.Logging,
		middleware.Metrics,
		middleware.RateLimit(mw.RateLimitRPS, mw.RateLimitBurst),
	)

	return handler
}

type MiddlewareConfig struct {
	AuthEnabled    bool
	CORSOrigins    []string
	RateLimitRPS   float64
	RateLimitBurst int
}
