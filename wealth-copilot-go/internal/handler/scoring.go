package handler

import (
	"net/http"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
	"github.com/wealth-copilot/wealth-copilot-go/internal/port"
	"github.com/wealth-copilot/wealth-copilot-go/pkg/httputil"
)

type ScoringHandler struct {
	scorer port.ScorerPort
}

func NewScoringHandler(s port.ScorerPort) *ScoringHandler {
	return &ScoringHandler{scorer: s}
}

type scoreRequest struct {
	Symbol       string            `json:"symbol"`
	Fundamentals domain.Fundamentals `json:"fundamentals"`
	Technicals   domain.Technicals   `json:"technicals"`
	RiskProfile  domain.RiskProfile  `json:"riskProfile"`
}

type rankRequest struct {
	Stocks      []scoreRequest     `json:"stocks"`
	RiskProfile domain.RiskProfile `json:"riskProfile"`
}

func (h *ScoringHandler) Score(w http.ResponseWriter, r *http.Request) {
	var req scoreRequest
	if err := httputil.DecodeJSON(r, &req); err != nil {
		httputil.RespondError(w, http.StatusBadRequest, err.Error())
		return
	}

	result := h.scorer.Score(req.Symbol, req.Fundamentals, req.Technicals, req.RiskProfile)
	httputil.RespondJSON(w, http.StatusOK, result)
}

func (h *ScoringHandler) ScoreAndRank(w http.ResponseWriter, r *http.Request) {
	var req rankRequest
	if err := httputil.DecodeJSON(r, &req); err != nil {
		httputil.RespondError(w, http.StatusBadRequest, err.Error())
		return
	}

	inputs := make([]port.ScorerInput, len(req.Stocks))
	for i, s := range req.Stocks {
		inputs[i] = port.ScorerInput{
			Symbol:       s.Symbol,
			Fundamentals: s.Fundamentals,
			Technicals:   s.Technicals,
		}
	}

	results := h.scorer.ScoreAndRank(inputs, req.RiskProfile)
	httputil.RespondJSON(w, http.StatusOK, results)
}
