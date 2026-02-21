package handler

import (
	"net/http"

	"github.com/wealth-copilot/wealth-copilot-go/internal/port"
	"github.com/wealth-copilot/wealth-copilot-go/pkg/httputil"
)

type GeopoliticsHandler struct {
	geo port.GeopoliticsPort
}

func NewGeopoliticsHandler(g port.GeopoliticsPort) *GeopoliticsHandler {
	return &GeopoliticsHandler{geo: g}
}

func (h *GeopoliticsHandler) GetScenarios(w http.ResponseWriter, _ *http.Request) {
	httputil.RespondJSON(w, http.StatusOK, h.geo.GetScenarios())
}

type detectRequest struct {
	Input string `json:"input"`
}

func (h *GeopoliticsHandler) DetectScenario(w http.ResponseWriter, r *http.Request) {
	var req detectRequest
	if err := httputil.DecodeJSON(r, &req); err != nil {
		httputil.RespondError(w, http.StatusBadRequest, err.Error())
		return
	}

	scenario := h.geo.DetectScenario(req.Input)
	if scenario == nil {
		httputil.RespondJSON(w, http.StatusOK, map[string]interface{}{"detected": false})
		return
	}
	httputil.RespondJSON(w, http.StatusOK, map[string]interface{}{
		"detected": true,
		"scenario": scenario,
	})
}
