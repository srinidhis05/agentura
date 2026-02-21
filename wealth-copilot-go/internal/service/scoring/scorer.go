package scoring

import (
	"fmt"
	"math"
	"sort"
	"strings"
	"time"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
	"github.com/wealth-copilot/wealth-copilot-go/internal/port"
)

// Factor weights by risk profile.
var weights = map[domain.RiskProfile]map[string]float64{
	domain.RiskProfileConservative: {"value": 0.25, "quality": 0.30, "momentum": 0.15, "technical": 0.15, "risk": 0.15},
	domain.RiskProfileModerate:     {"value": 0.20, "quality": 0.25, "momentum": 0.25, "technical": 0.20, "risk": 0.10},
	domain.RiskProfileAggressive:   {"value": 0.15, "quality": 0.20, "momentum": 0.30, "technical": 0.25, "risk": 0.10},
}

const (
	thresholdStrongBuy = 6.5
	thresholdBuy       = 5.5
	thresholdHold      = 4.5
)

type Scorer struct{}

func NewScorer() *Scorer {
	return &Scorer{}
}

func (s *Scorer) Score(symbol string, fundamentals domain.Fundamentals, technicals domain.Technicals, riskProfile domain.RiskProfile) domain.StockScore {
	w := weights[riskProfile]
	price := technicals.SMA20

	factors := domain.FactorScores{
		Value:     calculateValueScore(fundamentals),
		Quality:   calculateQualityScore(fundamentals),
		Momentum:  calculateMomentumScore(technicals),
		Technical: calculateTechnicalScore(technicals, price),
		Risk:      calculateRiskScore(fundamentals),
	}

	weightedSum := factors.Value*w["value"] +
		factors.Quality*w["quality"] +
		factors.Momentum*w["momentum"] +
		factors.Technical*w["technical"] +
		factors.Risk*w["risk"]

	score := math.Round(weightedSum/3*100) / 100

	return domain.StockScore{
		Symbol:         symbol,
		Exchange:       getExchange(symbol),
		Score:          score,
		Recommendation: getRecommendation(score),
		FactorScores:   factors,
		BullSignals:    extractBullSignals(fundamentals, technicals),
		BearSignals:    extractBearSignals(fundamentals, technicals),
		Timestamp:      time.Now(),
	}
}

func (s *Scorer) ScoreAndRank(data []port.ScorerInput, riskProfile domain.RiskProfile) []domain.StockScore {
	scores := make([]domain.StockScore, 0, len(data))
	for _, d := range data {
		scores = append(scores, s.Score(d.Symbol, d.Fundamentals, d.Technicals, riskProfile))
	}
	sort.Slice(scores, func(i, j int) bool {
		return scores[i].Score > scores[j].Score
	})
	return scores
}

func calculateValueScore(f domain.Fundamentals) float64 {
	var score float64

	pe := ptrOr(f.PERatio, 0)
	if pe > 0 && pe < 15 {
		score += 10
	} else if pe > 0 && pe < 25 {
		score += 5
	}

	pb := ptrOr(f.PBRatio, 0)
	if pb > 0 && pb < 2 {
		score += 10
	} else if pb > 0 && pb < 4 {
		score += 5
	}

	div := 0.0
	if f.DividendYield != nil {
		div = f.DividendYield.Value
	}
	if div > 3 {
		score += 10
	} else if div > 1 {
		score += 5
	}

	return score
}

func calculateQualityScore(f domain.Fundamentals) float64 {
	var score float64

	roe := 0.0
	if f.ROE != nil {
		roe = f.ROE.Value
	}
	if roe > 15 {
		score += 10
	} else if roe > 10 {
		score += 5
	}

	margin := 0.0
	if f.ProfitMargin != nil {
		margin = f.ProfitMargin.Value
	}
	if margin > 10 {
		score += 10
	} else if margin > 5 {
		score += 5
	}

	de := ptrOr(f.DebtToEquity, 0)
	if de >= 0 && de < 1 {
		score += 10
	} else if de >= 0 && de < 2 {
		score += 5
	}

	return score
}

func calculateMomentumScore(t domain.Technicals) float64 {
	var score float64

	if t.RSI > 30 && t.RSI < 70 {
		score += 10
	} else {
		score += 5
	}

	if t.Trend == domain.TrendStrongUptrend || t.Trend == domain.TrendUptrend {
		score += 10
	} else if t.Trend == domain.TrendMixed {
		score += 5
	}

	return score
}

func calculateTechnicalScore(t domain.Technicals, price float64) float64 {
	var score float64

	if t.RSISignal == domain.RSISignalOversold {
		score += 10
	} else if t.RSISignal == domain.RSISignalNeutral {
		score += 5
	}

	if t.MACDTrend == domain.MACDTrendBullish {
		score += 10
	}

	if t.SMA50 != nil && price > *t.SMA50 {
		score += 10
	}

	return score
}

func calculateRiskScore(f domain.Fundamentals) float64 {
	beta := ptrOr(f.Beta, 1)
	if beta < 1.2 {
		return 15
	}
	if beta < 1.5 {
		return 10
	}
	return 5
}

func getRecommendation(score float64) domain.Recommendation {
	if score >= thresholdStrongBuy {
		return domain.RecommendationStrongBuy
	}
	if score >= thresholdBuy {
		return domain.RecommendationBuy
	}
	if score >= thresholdHold {
		return domain.RecommendationHold
	}
	return domain.RecommendationSell
}

func extractBullSignals(f domain.Fundamentals, t domain.Technicals) []string {
	var signals []string

	pe := ptrOr(f.PERatio, 0)
	if pe > 0 && pe < 15 {
		signals = append(signals, fmt.Sprintf("Low P/E: %.1f", pe))
	}

	div := 0.0
	if f.DividendYield != nil {
		div = f.DividendYield.Value
	}
	if div > 3 {
		signals = append(signals, fmt.Sprintf("High Dividend: %.1f%%", div))
	}

	if t.RSISignal == domain.RSISignalOversold {
		signals = append(signals, fmt.Sprintf("RSI Oversold: %.0f", t.RSI))
	}
	if t.MACDTrend == domain.MACDTrendBullish {
		signals = append(signals, "MACD Bullish Crossover")
	}

	roe := 0.0
	if f.ROE != nil {
		roe = f.ROE.Value
	}
	if roe > 15 {
		signals = append(signals, fmt.Sprintf("Strong ROE: %.1f%%", roe))
	}

	return signals
}

func extractBearSignals(f domain.Fundamentals, t domain.Technicals) []string {
	var signals []string

	pe := ptrOr(f.PERatio, 0)
	if pe > 30 {
		signals = append(signals, fmt.Sprintf("High P/E: %.1f", pe))
	}

	if t.RSISignal == domain.RSISignalOverbought {
		signals = append(signals, fmt.Sprintf("RSI Overbought: %.0f", t.RSI))
	}

	de := ptrOr(f.DebtToEquity, 0)
	if de > 2 {
		signals = append(signals, fmt.Sprintf("High Debt: D/E %.2f", de))
	}

	beta := ptrOr(f.Beta, 1)
	if beta > 1.5 {
		signals = append(signals, fmt.Sprintf("High Beta: %.2f", beta))
	}

	return signals
}

func getExchange(symbol string) domain.Exchange {
	if strings.HasSuffix(symbol, ".NS") {
		return domain.ExchangeNSE
	}
	if strings.HasSuffix(symbol, ".BO") {
		return domain.ExchangeBSE
	}
	if strings.HasSuffix(symbol, ".L") {
		return domain.ExchangeLSE
	}
	if strings.Contains(symbol, "-USD") {
		return domain.ExchangeCRYPTO
	}
	return domain.ExchangeNASDAQ
}

func ptrOr(p *float64, def float64) float64 {
	if p != nil {
		return *p
	}
	return def
}
