package handler

import (
	"encoding/json"
	"io"
	"net/http"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

type MemoryHandler struct {
	executor *executor.Client
}

func NewMemoryHandler(exec *executor.Client) *MemoryHandler {
	return &MemoryHandler{executor: exec}
}

func (h *MemoryHandler) GetStatus(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.GetMemoryStatus(r.Context())
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

func (h *MemoryHandler) Search(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}
	raw, err := h.executor.MemorySearch(r.Context(), json.RawMessage(body))
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

func (h *MemoryHandler) GetPromptAssembly(w http.ResponseWriter, r *http.Request) {
	domain := r.PathValue("domain")
	skill := r.PathValue("skill")
	raw, err := h.executor.GetPromptAssembly(r.Context(), domain, skill)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}
