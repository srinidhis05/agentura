package port

import "github.com/wealth-copilot/wealth-copilot-go/internal/domain"

type ScorerPort interface {
	Score(symbol string, fundamentals domain.Fundamentals, technicals domain.Technicals, riskProfile domain.RiskProfile) domain.StockScore
	ScoreAndRank(data []ScorerInput, riskProfile domain.RiskProfile) []domain.StockScore
}

type ScorerInput struct {
	Symbol       string
	Fundamentals domain.Fundamentals
	Technicals   domain.Technicals
}
