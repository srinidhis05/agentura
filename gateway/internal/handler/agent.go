package handler

import (
	"fmt"
	"io"
	"net/http"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

// AgentHandler proxies agent registry requests to the Python executor.
type AgentHandler struct {
	executor *executor.Client
}

// NewAgentHandler creates a handler for agent endpoints.
func NewAgentHandler(exec *executor.Client) *AgentHandler {
	return &AgentHandler{executor: exec}
}

// ListAgents proxies GET /api/v1/agents to the executor.
func (h *AgentHandler) ListAgents(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.ProxyGet(r.Context(), "/api/v1/agents", r.URL.RawQuery)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// GetOrgChart proxies GET /api/v1/agents/org-chart to the executor.
func (h *AgentHandler) GetOrgChart(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.ProxyGet(r.Context(), "/api/v1/agents/org-chart", "")
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// GetAgent proxies GET /api/v1/agents/{agent_id} to the executor.
func (h *AgentHandler) GetAgent(w http.ResponseWriter, r *http.Request) {
	agentID := r.PathValue("agent_id")
	raw, err := h.executor.ProxyGet(r.Context(), fmt.Sprintf("/api/v1/agents/%s", agentID), "")
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// CreateAgent proxies POST /api/v1/agents to the executor.
func (h *AgentHandler) CreateAgent(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}
	raw, err := h.executor.PostRaw(r.Context(), "/api/v1/agents", body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	w.Write(raw)
}

// UpdateAgent proxies PUT /api/v1/agents/{agent_id} to the executor.
func (h *AgentHandler) UpdateAgent(w http.ResponseWriter, r *http.Request) {
	agentID := r.PathValue("agent_id")
	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}
	raw, err := h.executor.PutRaw(r.Context(), fmt.Sprintf("/api/v1/agents/%s", agentID), body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// DeleteAgent proxies DELETE /api/v1/agents/{agent_id} to the executor.
func (h *AgentHandler) DeleteAgent(w http.ResponseWriter, r *http.Request) {
	agentID := r.PathValue("agent_id")
	raw, err := h.executor.DeleteRaw(r.Context(), fmt.Sprintf("/api/v1/agents/%s", agentID))
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// DelegateTicket proxies POST /api/v1/agents/{agent_id}/delegate to the executor.
func (h *AgentHandler) DelegateTicket(w http.ResponseWriter, r *http.Request) {
	agentID := r.PathValue("agent_id")
	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}
	raw, err := h.executor.PostRaw(r.Context(), fmt.Sprintf("/api/v1/agents/%s/delegate", agentID), body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}
