package scoring

import (
	"testing"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
	"github.com/wealth-copilot/wealth-copilot-go/internal/port"
)

func ptr(f float64) *float64 { return &f }

func makeFundamentals(pe, pb, divYield, roe, margin, de, beta float64) domain.Fundamentals {
	return domain.Fundamentals{
		Symbol:        "TEST",
		PERatio:       &pe,
		PBRatio:       &pb,
		DividendYield: &domain.Percentage{Value: divYield},
		ROE:           &domain.Percentage{Value: roe},
		ProfitMargin:  &domain.Percentage{Value: margin},
		DebtToEquity:  &de,
		Beta:          &beta,
	}
}

func makeTechnicals(rsi float64, rsiSig domain.RSISignal, macdTrend domain.MACDTrend, trend domain.Trend, sma20 float64, sma50 *float64) domain.Technicals {
	return domain.Technicals{
		Symbol:    "TEST",
		RSI:       rsi,
		RSISignal: rsiSig,
		MACDTrend: macdTrend,
		SMA20:     sma20,
		SMA50:     sma50,
		Trend:     trend,
	}
}

func TestScore(t *testing.T) {
	tests := []struct {
		name        string
		fund        domain.Fundamentals
		tech        domain.Technicals
		profile     domain.RiskProfile
		wantMinScore float64
		wantMaxScore float64
		wantRec     domain.Recommendation
	}{
		{
			name:        "strong value stock scores high",
			fund:        makeFundamentals(10, 1.5, 4, 20, 15, 0.5, 0.8),
			tech:        makeTechnicals(35, domain.RSISignalOversold, domain.MACDTrendBullish, domain.TrendStrongUptrend, 100, ptr(95)),
			profile:     domain.RiskProfileModerate,
			wantMinScore: 6.0,
			wantMaxScore: 10.0,
			wantRec:     domain.RecommendationStrongBuy,
		},
		{
			name:        "weak stock scores low",
			fund:        makeFundamentals(40, 5, 0.5, 5, 3, 3, 2.0),
			tech:        makeTechnicals(80, domain.RSISignalOverbought, domain.MACDTrendBearish, domain.TrendStrongDowntrend, 100, ptr(120)),
			profile:     domain.RiskProfileModerate,
			wantMinScore: 0.0,
			wantMaxScore: 4.5,
			wantRec:     domain.RecommendationSell,
		},
		{
			name:        "conservative profile weights value higher",
			fund:        makeFundamentals(10, 1.5, 4, 20, 15, 0.5, 0.8),
			tech:        makeTechnicals(50, domain.RSISignalNeutral, domain.MACDTrendBullish, domain.TrendUptrend, 100, ptr(95)),
			profile:     domain.RiskProfileConservative,
			wantMinScore: 5.0,
			wantMaxScore: 10.0,
			wantRec:     domain.RecommendationStrongBuy,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			s := NewScorer()
			result := s.Score("TEST", tt.fund, tt.tech, tt.profile)

			if result.Score < tt.wantMinScore || result.Score > tt.wantMaxScore {
				t.Errorf("score = %.2f, want between %.1f and %.1f", result.Score, tt.wantMinScore, tt.wantMaxScore)
			}
			if result.Recommendation != tt.wantRec {
				t.Errorf("recommendation = %s, want %s (score=%.2f)", result.Recommendation, tt.wantRec, result.Score)
			}
		})
	}
}

func TestScoreAndRank(t *testing.T) {
	s := NewScorer()

	data := []port.ScorerInput{
		{
			Symbol:       "WEAK",
			Fundamentals: makeFundamentals(40, 5, 0.5, 5, 3, 3, 2.0),
			Technicals:   makeTechnicals(80, domain.RSISignalOverbought, domain.MACDTrendBearish, domain.TrendDowntrend, 100, ptr(120)),
		},
		{
			Symbol:       "STRONG",
			Fundamentals: makeFundamentals(10, 1.5, 4, 20, 15, 0.5, 0.8),
			Technicals:   makeTechnicals(35, domain.RSISignalOversold, domain.MACDTrendBullish, domain.TrendStrongUptrend, 100, ptr(95)),
		},
	}

	ranked := s.ScoreAndRank(data, domain.RiskProfileModerate)
	if len(ranked) != 2 {
		t.Fatalf("expected 2 results, got %d", len(ranked))
	}
	if ranked[0].Symbol != "STRONG" {
		t.Errorf("expected STRONG first, got %s", ranked[0].Symbol)
	}
	if ranked[0].Score <= ranked[1].Score {
		t.Error("expected first score > second score")
	}
}

func TestGetExchange(t *testing.T) {
	tests := []struct {
		symbol string
		want   domain.Exchange
	}{
		{"RELIANCE.NS", domain.ExchangeNSE},
		{"TCS.BO", domain.ExchangeBSE},
		{"BAE.L", domain.ExchangeLSE},
		{"BTC-USD", domain.ExchangeCRYPTO},
		{"AAPL", domain.ExchangeNASDAQ},
	}

	for _, tt := range tests {
		got := getExchange(tt.symbol)
		if got != tt.want {
			t.Errorf("getExchange(%s) = %s, want %s", tt.symbol, got, tt.want)
		}
	}
}

func TestBullBearSignals(t *testing.T) {
	fund := makeFundamentals(10, 1.5, 4, 20, 15, 0.5, 0.8)
	tech := makeTechnicals(25, domain.RSISignalOversold, domain.MACDTrendBullish, domain.TrendUptrend, 100, nil)

	bull := extractBullSignals(fund, tech)
	if len(bull) == 0 {
		t.Error("expected bull signals for strong fundamentals")
	}

	bearFund := makeFundamentals(40, 5, 0.5, 5, 3, 3, 2.0)
	bearTech := makeTechnicals(80, domain.RSISignalOverbought, domain.MACDTrendBearish, domain.TrendDowntrend, 100, nil)
	bear := extractBearSignals(bearFund, bearTech)
	if len(bear) == 0 {
		t.Error("expected bear signals for weak fundamentals")
	}
}
