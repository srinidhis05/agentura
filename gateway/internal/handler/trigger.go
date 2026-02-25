package handler

import (
	"net/http"

	"github.com/agentura-ai/agentura/gateway/internal/service"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

// TriggerHandler exposes cron scheduler status via HTTP.
type TriggerHandler struct {
	scheduler *service.Scheduler
}

// NewTriggerHandler creates a handler for trigger status endpoints.
func NewTriggerHandler(scheduler *service.Scheduler) *TriggerHandler {
	return &TriggerHandler{scheduler: scheduler}
}

// ListTriggers returns registered cron jobs with next/prev run times.
func (h *TriggerHandler) ListTriggers(w http.ResponseWriter, r *http.Request) {
	jobs := h.scheduler.ListJobs()
	httputil.RespondJSON(w, http.StatusOK, jobs)
}

// Status returns scheduler health.
func (h *TriggerHandler) Status(w http.ResponseWriter, r *http.Request) {
	status := h.scheduler.Status()
	httputil.RespondJSON(w, http.StatusOK, status)
}
