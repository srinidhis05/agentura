package risk

import (
	"fmt"
	"math"
	"sync"
	"time"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
)

// Hard-coded limits — non-negotiable and frozen.
var limits = domain.RiskLimits{
	MaxPositionPct:      domain.Percentage{Value: 2.0},
	MaxSectorPct:        domain.Percentage{Value: 25.0},
	MaxConcentration:    5,
	MaxDailyLossPct:     domain.Percentage{Value: 5.0},
	MaxWeeklyLossPct:    domain.Percentage{Value: 10.0},
	MaxDrawdownPct:      domain.Percentage{Value: 15.0},
	MaxTradesPerDay:     10,
	MinHoldingPeriodSec: 60,
	RequireStopLoss:     true,
	MinRiskRewardRatio:  1.5,
	MinScoreThreshold:   5.5,
	HumanApprovalThreshold: map[domain.Currency]float64{
		domain.CurrencyINR: 50000,
		domain.CurrencyUSD: 500,
		domain.CurrencyAED: 2000,
		domain.CurrencyGBP: 400,
		domain.CurrencyEUR: 450,
		domain.CurrencySGD: 700,
		domain.CurrencyCAD: 700,
		domain.CurrencyAUD: 800,
	},
}

type Manager struct {
	mu             sync.RWMutex
	circuitBreaker domain.CircuitBreakerStatus
}

func NewManager() *Manager {
	return &Manager{}
}

func (m *Manager) GetLimits() domain.RiskLimits {
	return limits
}

func (m *Manager) ValidateSignal(signal domain.Signal, portfolio domain.Portfolio, dailyStats domain.DailyStats) domain.RiskCheck {
	var violations []domain.RiskViolation
	var warnings []string

	// Check circuit breaker first
	m.mu.RLock()
	cb := m.circuitBreaker
	m.mu.RUnlock()

	if cb.IsHalted {
		reason := "Unknown"
		if cb.Reason != nil {
			reason = *cb.Reason
		}
		violations = append(violations, domain.RiskViolation{
			Rule:     "CIRCUIT_BREAKER",
			Severity: domain.SeverityHalt,
			Limit:    "Trading halted",
			Actual:   reason,
			Message:  fmt.Sprintf("Trading halted: %s", reason),
		})
		return domain.RiskCheck{Approved: false, Violations: violations, Warnings: warnings}
	}

	portfolioValue := portfolio.TotalValue.Amount
	positionValue := signal.EntryPrice * float64(signal.Quantity)
	positionPct := (positionValue / portfolioValue) * 100

	// Rule 1: Max position size (2%)
	var adjustedQuantity *int
	if positionPct > limits.MaxPositionPct.Value {
		maxQty := int(math.Floor((portfolioValue * limits.MaxPositionPct.Value / 100) / signal.EntryPrice))
		adjustedQuantity = &maxQty
		violations = append(violations, domain.RiskViolation{
			Rule:     "MAX_POSITION",
			Severity: domain.SeverityBlock,
			Limit:    fmt.Sprintf("%.1f%%", limits.MaxPositionPct.Value),
			Actual:   fmt.Sprintf("%.1f%%", positionPct),
			Message:  fmt.Sprintf("Position %.1f%% exceeds max %.1f%%. Max quantity: %d", positionPct, limits.MaxPositionPct.Value, maxQty),
		})
	}

	// Rule 2: Daily trades limit
	if dailyStats.Trades >= limits.MaxTradesPerDay {
		violations = append(violations, domain.RiskViolation{
			Rule:     "MAX_DAILY_TRADES",
			Severity: domain.SeverityBlock,
			Limit:    fmt.Sprintf("%d", limits.MaxTradesPerDay),
			Actual:   fmt.Sprintf("%d", dailyStats.Trades),
			Message:  fmt.Sprintf("Daily trade limit reached (%d/%d)", dailyStats.Trades, limits.MaxTradesPerDay),
		})
	} else if dailyStats.Trades >= limits.MaxTradesPerDay-2 {
		warnings = append(warnings, fmt.Sprintf("Approaching trade limit (%d/%d)", dailyStats.Trades, limits.MaxTradesPerDay))
	}

	// Rule 3: Daily loss circuit breaker (5%)
	dailyLossPct := math.Abs(math.Min(0, dailyStats.PnL)) / portfolioValue * 100
	if dailyLossPct >= limits.MaxDailyLossPct.Value {
		violations = append(violations, domain.RiskViolation{
			Rule:     "MAX_DAILY_LOSS",
			Severity: domain.SeverityHalt,
			Limit:    fmt.Sprintf("%.1f%%", limits.MaxDailyLossPct.Value),
			Actual:   fmt.Sprintf("%.1f%%", dailyLossPct),
			Message:  fmt.Sprintf("Daily loss limit reached (%.1f%%). Trading halted.", dailyLossPct),
		})
		m.TriggerCircuitBreaker("Daily loss limit exceeded", 24*60*60*1000)
	} else if dailyLossPct >= limits.MaxDailyLossPct.Value*0.6 {
		warnings = append(warnings, fmt.Sprintf("Daily loss at %.1f%% (limit: %.1f%%)", dailyLossPct, limits.MaxDailyLossPct.Value))
	}

	// Rule 4: Stop loss required
	if limits.RequireStopLoss && signal.StopLoss == 0 {
		violations = append(violations, domain.RiskViolation{
			Rule:     "STOP_LOSS_REQUIRED",
			Severity: domain.SeverityBlock,
			Limit:    "Required",
			Actual:   "Missing",
			Message:  "Stop loss is required for all trades",
		})
	}

	// Rule 5: Minimum score threshold
	if signal.Score < limits.MinScoreThreshold {
		violations = append(violations, domain.RiskViolation{
			Rule:     "MIN_SCORE",
			Severity: domain.SeverityBlock,
			Limit:    fmt.Sprintf("%.1f", limits.MinScoreThreshold),
			Actual:   fmt.Sprintf("%.1f", signal.Score),
			Message:  fmt.Sprintf("Score %.1f below minimum %.1f", signal.Score, limits.MinScoreThreshold),
		})
	}

	// Rule 6: Risk/Reward ratio
	if signal.StopLoss > 0 && signal.Target > 0 {
		risk := math.Abs(signal.EntryPrice - signal.StopLoss)
		reward := math.Abs(signal.Target - signal.EntryPrice)
		rr := 0.0
		if risk > 0 {
			rr = reward / risk
		}
		if rr < limits.MinRiskRewardRatio {
			violations = append(violations, domain.RiskViolation{
				Rule:     "MIN_RISK_REWARD",
				Severity: domain.SeverityBlock,
				Limit:    fmt.Sprintf("%.1f:1", limits.MinRiskRewardRatio),
				Actual:   fmt.Sprintf("%.2f:1", rr),
				Message:  fmt.Sprintf("Risk/Reward %.2f:1 below minimum %.1f:1", rr, limits.MinRiskRewardRatio),
			})
		}
	}

	return domain.RiskCheck{
		Approved:         len(violations) == 0,
		Violations:       violations,
		Warnings:         warnings,
		AdjustedQuantity: adjustedQuantity,
	}
}

// CalculatePositionSize uses Half-Kelly criterion with volatility adjustment.
func (m *Manager) CalculatePositionSize(price, portfolioValue, winRate, avgWin, avgLoss, volatility float64) int {
	if winRate == 0 {
		winRate = 0.5
	}
	if avgWin == 0 {
		avgWin = 0.08
	}
	if avgLoss == 0 {
		avgLoss = 0.04
	}
	if volatility == 0 {
		volatility = 0.2
	}

	p := winRate
	q := 1 - p
	b := avgWin / avgLoss

	kellyPct := (p*b - q) / b
	halfKelly := math.Max(0, kellyPct/2)
	volAdjusted := halfKelly * (1 / (1 + volatility))
	cappedPct := math.Min(volAdjusted, limits.MaxPositionPct.Value/100)

	positionValue := portfolioValue * cappedPct
	return int(math.Floor(positionValue / price))
}

func (m *Manager) GetCircuitBreakerStatus() domain.CircuitBreakerStatus {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.circuitBreaker.IsHalted && m.circuitBreaker.ResumesAt != nil {
		if time.Now().After(*m.circuitBreaker.ResumesAt) {
			m.resetCircuitBreakerLocked()
		}
	}
	return m.circuitBreaker
}

func (m *Manager) TriggerCircuitBreaker(reason string, durationMs int64) {
	m.mu.Lock()
	defer m.mu.Unlock()

	now := time.Now()
	resumesAt := now.Add(time.Duration(durationMs) * time.Millisecond)
	m.circuitBreaker = domain.CircuitBreakerStatus{
		IsHalted:  true,
		Reason:    &reason,
		HaltedAt:  &now,
		ResumesAt: &resumesAt,
	}
}

func (m *Manager) ResetCircuitBreaker() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.resetCircuitBreakerLocked()
}

func (m *Manager) resetCircuitBreakerLocked() {
	m.circuitBreaker = domain.CircuitBreakerStatus{}
}

// RequiresHumanApproval checks if a trade amount exceeds the human approval threshold.
func RequiresHumanApproval(amount float64, currency domain.Currency) bool {
	threshold, ok := limits.HumanApprovalThreshold[currency]
	if !ok {
		threshold = 500
	}
	return amount > threshold
}

// GetRiskStatus returns a dashboard-ready risk summary.
func GetRiskStatus(portfolio domain.Portfolio, dailyStats domain.DailyStats, cb domain.CircuitBreakerStatus) domain.RiskStatus {
	portfolioValue := portfolio.TotalValue.Amount
	dailyLossPct := math.Abs(math.Min(0, dailyStats.PnL)) / portfolioValue * 100

	return domain.RiskStatus{
		DailyLossPct:   dailyLossPct,
		DailyLossLimit: limits.MaxDailyLossPct.Value,
		TradesUsed:     dailyStats.Trades,
		TradesLimit:    limits.MaxTradesPerDay,
		IsHealthy:      dailyLossPct < limits.MaxDailyLossPct.Value*0.6 && dailyStats.Trades < limits.MaxTradesPerDay-2,
		CircuitBreaker: cb,
	}
}
