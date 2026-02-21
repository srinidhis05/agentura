package handler

import (
	"net/http"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
	"github.com/wealth-copilot/wealth-copilot-go/internal/port"
	"github.com/wealth-copilot/wealth-copilot-go/pkg/httputil"
)

type MarketHandler struct {
	marketData port.MarketDataPort
}

func NewMarketHandler(md port.MarketDataPort) *MarketHandler {
	return &MarketHandler{marketData: md}
}

func (h *MarketHandler) GetQuote(w http.ResponseWriter, r *http.Request) {
	symbol := r.PathValue("symbol")
	if symbol == "" {
		httputil.RespondError(w, http.StatusBadRequest, "symbol is required")
		return
	}

	price, err := h.marketData.GetPrice(r.Context(), symbol, domain.ExchangeNASDAQ)
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	if price == nil {
		httputil.RespondError(w, http.StatusNotFound, "symbol not found")
		return
	}

	httputil.RespondJSON(w, http.StatusOK, price)
}

func (h *MarketHandler) GetFundamentals(w http.ResponseWriter, r *http.Request) {
	symbol := r.PathValue("symbol")
	if symbol == "" {
		httputil.RespondError(w, http.StatusBadRequest, "symbol is required")
		return
	}

	data, err := h.marketData.GetFundamentals(r.Context(), symbol)
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	if data == nil {
		httputil.RespondError(w, http.StatusNotFound, "symbol not found")
		return
	}

	httputil.RespondJSON(w, http.StatusOK, data)
}

func (h *MarketHandler) GetTechnicals(w http.ResponseWriter, r *http.Request) {
	symbol := r.PathValue("symbol")
	if symbol == "" {
		httputil.RespondError(w, http.StatusBadRequest, "symbol is required")
		return
	}

	data, err := h.marketData.GetTechnicals(r.Context(), symbol, "")
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	if data == nil {
		httputil.RespondError(w, http.StatusNotFound, "symbol not found")
		return
	}

	httputil.RespondJSON(w, http.StatusOK, data)
}
