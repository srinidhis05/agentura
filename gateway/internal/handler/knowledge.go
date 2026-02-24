package handler

import (
	"encoding/json"
	"io"
	"net/http"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

type KnowledgeHandler struct {
	executor *executor.Client
}

func NewKnowledgeHandler(exec *executor.Client) *KnowledgeHandler {
	return &KnowledgeHandler{executor: exec}
}

func (h *KnowledgeHandler) ListReflexions(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.ListReflexions(r.Context(), r.URL.RawQuery)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

func (h *KnowledgeHandler) ListCorrections(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.ListCorrections(r.Context(), r.URL.RawQuery)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

func (h *KnowledgeHandler) ListTests(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.ListTests(r.Context(), r.URL.RawQuery)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

func (h *KnowledgeHandler) GetStats(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.GetKnowledgeStats(r.Context())
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

func (h *KnowledgeHandler) SemanticSearch(w http.ResponseWriter, r *http.Request) {
	domain := r.PathValue("domain")
	skill := r.PathValue("skill")
	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}
	raw, err := h.executor.SemanticSearch(r.Context(), domain, skill, json.RawMessage(body))
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

func (h *KnowledgeHandler) ValidateTests(w http.ResponseWriter, r *http.Request) {
	domain := r.PathValue("domain")
	skill := r.PathValue("skill")
	raw, err := h.executor.ValidateTests(r.Context(), domain, skill)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}
