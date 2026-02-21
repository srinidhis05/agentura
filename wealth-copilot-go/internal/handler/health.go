package handler

import (
	"net/http"

	"github.com/wealth-copilot/wealth-copilot-go/pkg/httputil"
)

type HealthHandler struct {
	// dbCheck can be injected for readiness probes
	dbCheck func() error
}

func NewHealthHandler(dbCheck func() error) *HealthHandler {
	return &HealthHandler{dbCheck: dbCheck}
}

func (h *HealthHandler) Healthz(w http.ResponseWriter, _ *http.Request) {
	httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (h *HealthHandler) Readyz(w http.ResponseWriter, _ *http.Request) {
	if h.dbCheck != nil {
		if err := h.dbCheck(); err != nil {
			httputil.RespondError(w, http.StatusServiceUnavailable, "database not ready")
			return
		}
	}
	httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "ready"})
}
