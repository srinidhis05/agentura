package handler

import (
	"net/http"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
	"github.com/wealth-copilot/wealth-copilot-go/internal/port"
	"github.com/wealth-copilot/wealth-copilot-go/pkg/httputil"
)

type TradeHandler struct {
	broker port.BrokerPort
	risk   port.RiskPort
}

func NewTradeHandler(b port.BrokerPort, r port.RiskPort) *TradeHandler {
	return &TradeHandler{broker: b, risk: r}
}

type tradeRequest struct {
	Symbol    string           `json:"symbol"`
	Exchange  domain.Exchange  `json:"exchange"`
	Quantity  int              `json:"quantity"`
	OrderType domain.OrderType `json:"orderType"`
	Price     *float64         `json:"price,omitempty"`
}

func (h *TradeHandler) Buy(w http.ResponseWriter, r *http.Request) {
	var req tradeRequest
	if err := httputil.DecodeJSON(r, &req); err != nil {
		httputil.RespondError(w, http.StatusBadRequest, err.Error())
		return
	}

	order, err := h.broker.Buy(r.Context(), req.Symbol, req.Exchange, req.Quantity, req.OrderType, req.Price)
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	httputil.RespondJSON(w, http.StatusOK, order)
}

func (h *TradeHandler) Sell(w http.ResponseWriter, r *http.Request) {
	var req tradeRequest
	if err := httputil.DecodeJSON(r, &req); err != nil {
		httputil.RespondError(w, http.StatusBadRequest, err.Error())
		return
	}

	order, err := h.broker.Sell(r.Context(), req.Symbol, req.Exchange, req.Quantity, req.OrderType, req.Price)
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	httputil.RespondJSON(w, http.StatusOK, order)
}

func (h *TradeHandler) GetOrders(w http.ResponseWriter, r *http.Request) {
	orders, err := h.broker.GetOrders(r.Context())
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	httputil.RespondJSON(w, http.StatusOK, orders)
}
