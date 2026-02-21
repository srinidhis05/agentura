package handler

import (
	"net/http"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
	"github.com/wealth-copilot/wealth-copilot-go/internal/port"
	"github.com/wealth-copilot/wealth-copilot-go/pkg/httputil"
)

type RiskHandler struct {
	risk port.RiskPort
}

func NewRiskHandler(r port.RiskPort) *RiskHandler {
	return &RiskHandler{risk: r}
}

func (h *RiskHandler) GetLimits(w http.ResponseWriter, _ *http.Request) {
	httputil.RespondJSON(w, http.StatusOK, h.risk.GetLimits())
}

func (h *RiskHandler) GetStatus(w http.ResponseWriter, _ *http.Request) {
	cb := h.risk.GetCircuitBreakerStatus()
	httputil.RespondJSON(w, http.StatusOK, domain.RiskStatus{
		DailyLossLimit: h.risk.GetLimits().MaxDailyLossPct.Value,
		TradesLimit:    h.risk.GetLimits().MaxTradesPerDay,
		CircuitBreaker: cb,
		IsHealthy:      !cb.IsHalted,
	})
}

type validateSignalRequest struct {
	Signal     domain.Signal     `json:"signal"`
	Portfolio  domain.Portfolio  `json:"portfolio"`
	DailyStats domain.DailyStats `json:"dailyStats"`
}

func (h *RiskHandler) ValidateSignal(w http.ResponseWriter, r *http.Request) {
	var req validateSignalRequest
	if err := httputil.DecodeJSON(r, &req); err != nil {
		httputil.RespondError(w, http.StatusBadRequest, err.Error())
		return
	}

	result := h.risk.ValidateSignal(req.Signal, req.Portfolio, req.DailyStats)
	httputil.RespondJSON(w, http.StatusOK, result)
}

func (h *RiskHandler) GetCircuitBreaker(w http.ResponseWriter, _ *http.Request) {
	httputil.RespondJSON(w, http.StatusOK, h.risk.GetCircuitBreakerStatus())
}
