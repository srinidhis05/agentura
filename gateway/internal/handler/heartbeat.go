package handler

import (
	"fmt"
	"net/http"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

// HeartbeatHandler proxies heartbeat requests to the Python executor.
type HeartbeatHandler struct {
	executor *executor.Client
}

// NewHeartbeatHandler creates a handler for heartbeat endpoints.
func NewHeartbeatHandler(exec *executor.Client) *HeartbeatHandler {
	return &HeartbeatHandler{executor: exec}
}

// ListRuns proxies GET /api/v1/heartbeats to the executor.
func (h *HeartbeatHandler) ListRuns(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.ProxyGet(r.Context(), "/api/v1/heartbeats", r.URL.RawQuery)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// GetSchedule proxies GET /api/v1/heartbeats/schedule to the executor.
func (h *HeartbeatHandler) GetSchedule(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.ProxyGet(r.Context(), "/api/v1/heartbeats/schedule", "")
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// GetRun proxies GET /api/v1/heartbeats/{run_id} to the executor.
func (h *HeartbeatHandler) GetRun(w http.ResponseWriter, r *http.Request) {
	runID := r.PathValue("run_id")
	raw, err := h.executor.ProxyGet(r.Context(), fmt.Sprintf("/api/v1/heartbeats/%s", runID), "")
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// TriggerHeartbeat proxies POST /api/v1/heartbeats/{agent_id}/trigger to the executor.
func (h *HeartbeatHandler) TriggerHeartbeat(w http.ResponseWriter, r *http.Request) {
	agentID := r.PathValue("agent_id")
	raw, err := h.executor.PostRaw(r.Context(), fmt.Sprintf("/api/v1/heartbeats/%s/trigger", agentID), nil)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}
