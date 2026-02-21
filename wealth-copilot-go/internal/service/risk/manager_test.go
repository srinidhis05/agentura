package risk

import (
	"testing"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
)

func makePortfolio(totalValue float64) domain.Portfolio {
	return domain.Portfolio{
		TotalValue: domain.Money{Amount: totalValue, Currency: domain.CurrencyINR},
		Positions:  []domain.Position{},
	}
}

func makeSignal(price float64, qty int, score, stopLoss, target float64) domain.Signal {
	return domain.Signal{
		ID:         "test-signal",
		Action:     domain.ActionBUY,
		Symbol:     "RELIANCE.NS",
		Exchange:   domain.ExchangeNSE,
		Quantity:   qty,
		EntryPrice: price,
		StopLoss:   stopLoss,
		Target:     target,
		Score:      score,
		Confidence: domain.Percentage{Value: 80},
	}
}

func TestValidateSignal(t *testing.T) {
	tests := []struct {
		name           string
		signal         domain.Signal
		portfolio      domain.Portfolio
		dailyStats     domain.DailyStats
		wantApproved   bool
		wantViolations int
	}{
		{
			name:           "valid signal passes all checks",
			signal:         makeSignal(100, 10, 7.0, 95, 115),
			portfolio:      makePortfolio(100000),
			dailyStats:     domain.DailyStats{Trades: 0, PnL: 0},
			wantApproved:   true,
			wantViolations: 0,
		},
		{
			name:           "position too large blocked",
			signal:         makeSignal(100, 50, 7.0, 95, 115),
			portfolio:      makePortfolio(100000),
			dailyStats:     domain.DailyStats{Trades: 0, PnL: 0},
			wantApproved:   false,
			wantViolations: 1,
		},
		{
			name:           "daily trade limit reached",
			signal:         makeSignal(100, 10, 7.0, 95, 115),
			portfolio:      makePortfolio(100000),
			dailyStats:     domain.DailyStats{Trades: 10, PnL: 0},
			wantApproved:   false,
			wantViolations: 1,
		},
		{
			name:           "daily loss limit triggers halt",
			signal:         makeSignal(100, 10, 7.0, 95, 115),
			portfolio:      makePortfolio(100000),
			dailyStats:     domain.DailyStats{Trades: 0, PnL: -5100},
			wantApproved:   false,
			wantViolations: 1,
		},
		{
			name:           "missing stop loss blocked",
			signal:         makeSignal(100, 10, 7.0, 0, 115),
			portfolio:      makePortfolio(100000),
			dailyStats:     domain.DailyStats{Trades: 0, PnL: 0},
			wantApproved:   false,
			wantViolations: 1,
		},
		{
			name:           "low score blocked",
			signal:         makeSignal(100, 10, 4.0, 95, 115),
			portfolio:      makePortfolio(100000),
			dailyStats:     domain.DailyStats{Trades: 0, PnL: 0},
			wantApproved:   false,
			wantViolations: 1,
		},
		{
			name:           "bad risk reward blocked",
			signal:         makeSignal(100, 10, 7.0, 95, 102),
			portfolio:      makePortfolio(100000),
			dailyStats:     domain.DailyStats{Trades: 0, PnL: 0},
			wantApproved:   false,
			wantViolations: 1,
		},
		{
			name:           "multiple violations accumulate",
			signal:         makeSignal(100, 50, 4.0, 0, 102),
			portfolio:      makePortfolio(100000),
			dailyStats:     domain.DailyStats{Trades: 10, PnL: -6000},
			wantApproved:   false,
			wantViolations: 5,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			m := NewManager()
			result := m.ValidateSignal(tt.signal, tt.portfolio, tt.dailyStats)

			if result.Approved != tt.wantApproved {
				t.Errorf("approved = %v, want %v", result.Approved, tt.wantApproved)
			}
			if len(result.Violations) != tt.wantViolations {
				t.Errorf("violations = %d, want %d: %+v", len(result.Violations), tt.wantViolations, result.Violations)
			}
		})
	}
}

func TestValidateSignal_CircuitBreakerBlocks(t *testing.T) {
	m := NewManager()
	m.TriggerCircuitBreaker("test halt", 60000)

	signal := makeSignal(100, 10, 7.0, 95, 115)
	result := m.ValidateSignal(signal, makePortfolio(100000), domain.DailyStats{})

	if result.Approved {
		t.Error("expected blocked by circuit breaker")
	}
	if len(result.Violations) != 1 || result.Violations[0].Rule != "CIRCUIT_BREAKER" {
		t.Errorf("expected CIRCUIT_BREAKER violation, got %+v", result.Violations)
	}
}

func TestCalculatePositionSize(t *testing.T) {
	tests := []struct {
		name           string
		price          float64
		portfolioValue float64
		winRate        float64
		wantMin        int
		wantMax        int
	}{
		{
			name:           "default params",
			price:          100,
			portfolioValue: 100000,
			winRate:        0.5,
			wantMin:        1,
			wantMax:        20,
		},
		{
			name:           "high win rate larger position",
			price:          100,
			portfolioValue: 100000,
			winRate:        0.7,
			wantMin:        1,
			wantMax:        20,
		},
		{
			name:           "zero win rate returns zero",
			price:          100,
			portfolioValue: 100000,
			winRate:        0.0,
			wantMin:        0,
			wantMax:        20,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			m := NewManager()
			qty := m.CalculatePositionSize(tt.price, tt.portfolioValue, tt.winRate, 0.08, 0.04, 0.2)
			if qty < tt.wantMin || qty > tt.wantMax {
				t.Errorf("qty = %d, want between %d and %d", qty, tt.wantMin, tt.wantMax)
			}
		})
	}
}

func TestCircuitBreaker(t *testing.T) {
	m := NewManager()

	status := m.GetCircuitBreakerStatus()
	if status.IsHalted {
		t.Error("expected not halted initially")
	}

	m.TriggerCircuitBreaker("test", 60000)
	status = m.GetCircuitBreakerStatus()
	if !status.IsHalted {
		t.Error("expected halted after trigger")
	}
	if status.Reason == nil || *status.Reason != "test" {
		t.Error("expected reason 'test'")
	}

	m.ResetCircuitBreaker()
	status = m.GetCircuitBreakerStatus()
	if status.IsHalted {
		t.Error("expected not halted after reset")
	}
}

func TestRequiresHumanApproval(t *testing.T) {
	tests := []struct {
		amount   float64
		currency domain.Currency
		want     bool
	}{
		{49999, domain.CurrencyINR, false},
		{50001, domain.CurrencyINR, true},
		{499, domain.CurrencyUSD, false},
		{501, domain.CurrencyUSD, true},
	}

	for _, tt := range tests {
		got := RequiresHumanApproval(tt.amount, tt.currency)
		if got != tt.want {
			t.Errorf("RequiresHumanApproval(%v, %s) = %v, want %v", tt.amount, tt.currency, got, tt.want)
		}
	}
}
