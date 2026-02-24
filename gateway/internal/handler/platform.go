package handler

import (
	"net/http"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

type PlatformHandler struct {
	executor *executor.Client
}

func NewPlatformHandler(exec *executor.Client) *PlatformHandler {
	return &PlatformHandler{executor: exec}
}

func (h *PlatformHandler) GetHealth(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.GetPlatformHealth(r.Context())
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}
