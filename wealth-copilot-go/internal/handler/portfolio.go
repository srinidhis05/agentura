package handler

import (
	"net/http"

	"github.com/wealth-copilot/wealth-copilot-go/internal/port"
	"github.com/wealth-copilot/wealth-copilot-go/pkg/httputil"
)

type PortfolioHandler struct {
	broker port.BrokerPort
}

func NewPortfolioHandler(b port.BrokerPort) *PortfolioHandler {
	return &PortfolioHandler{broker: b}
}

func (h *PortfolioHandler) Create(w http.ResponseWriter, _ *http.Request) {
	// TODO: implement portfolio creation with persistence
	httputil.RespondJSON(w, http.StatusCreated, map[string]string{"status": "created"})
}

func (h *PortfolioHandler) List(w http.ResponseWriter, r *http.Request) {
	portfolio, err := h.broker.GetPortfolio(r.Context())
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	httputil.RespondJSON(w, http.StatusOK, []interface{}{portfolio})
}

func (h *PortfolioHandler) Get(w http.ResponseWriter, r *http.Request) {
	_ = r.PathValue("id")
	portfolio, err := h.broker.GetPortfolio(r.Context())
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	httputil.RespondJSON(w, http.StatusOK, portfolio)
}

func (h *PortfolioHandler) AddTransaction(w http.ResponseWriter, _ *http.Request) {
	// TODO: implement transaction recording
	httputil.RespondJSON(w, http.StatusCreated, map[string]string{"status": "recorded"})
}

func (h *PortfolioHandler) GetHoldings(w http.ResponseWriter, r *http.Request) {
	portfolio, err := h.broker.GetPortfolio(r.Context())
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	httputil.RespondJSON(w, http.StatusOK, portfolio.Positions)
}

func (h *PortfolioHandler) GetPerformance(w http.ResponseWriter, r *http.Request) {
	portfolio, err := h.broker.GetPortfolio(r.Context())
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	httputil.RespondJSON(w, http.StatusOK, map[string]interface{}{
		"dailyPnl":    portfolio.DailyPnL,
		"dailyPnlPct": portfolio.DailyPnLPct,
		"totalValue":  portfolio.TotalValue,
	})
}
