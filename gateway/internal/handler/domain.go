package handler

import (
	"net/http"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

type DomainHandler struct {
	executor *executor.Client
}

func NewDomainHandler(exec *executor.Client) *DomainHandler {
	return &DomainHandler{executor: exec}
}

func (h *DomainHandler) ListDomains(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.ListDomains(r.Context())
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

func (h *DomainHandler) GetDomain(w http.ResponseWriter, r *http.Request) {
	domain := r.PathValue("domain")

	raw, err := h.executor.GetDomain(r.Context(), domain)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}
