package handler

import (
	"net/http"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
	"github.com/wealth-copilot/wealth-copilot-go/internal/port"
	"github.com/wealth-copilot/wealth-copilot-go/pkg/httputil"
)

type CrossBorderHandler struct {
	crossBorder port.CrossBorderPort
}

func NewCrossBorderHandler(cb port.CrossBorderPort) *CrossBorderHandler {
	return &CrossBorderHandler{crossBorder: cb}
}

func (h *CrossBorderHandler) GetFxRate(w http.ResponseWriter, r *http.Request) {
	from := domain.Currency(r.URL.Query().Get("from"))
	to := domain.Currency(r.URL.Query().Get("to"))

	if from == "" || to == "" {
		httputil.RespondError(w, http.StatusBadRequest, "from and to query params required")
		return
	}

	rate, err := h.crossBorder.GetFxRate(r.Context(), from, to)
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	httputil.RespondJSON(w, http.StatusOK, rate)
}

func (h *CrossBorderHandler) GetCurrencyImpact(w http.ResponseWriter, r *http.Request) {
	symbol := r.PathValue("symbol")
	if symbol == "" {
		httputil.RespondError(w, http.StatusBadRequest, "symbol is required")
		return
	}

	impact, err := h.crossBorder.CalculateCurrencyImpact(r.Context(), symbol, domain.CurrencyINR, domain.Period1Y)
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	httputil.RespondJSON(w, http.StatusOK, impact)
}
