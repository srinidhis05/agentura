package port

import "github.com/wealth-copilot/wealth-copilot-go/internal/domain"

type RiskPort interface {
	GetLimits() domain.RiskLimits
	ValidateSignal(signal domain.Signal, portfolio domain.Portfolio, dailyStats domain.DailyStats) domain.RiskCheck
	CalculatePositionSize(price, portfolioValue, winRate, avgWin, avgLoss, volatility float64) int
	GetCircuitBreakerStatus() domain.CircuitBreakerStatus
	TriggerCircuitBreaker(reason string, durationMs int64)
	ResetCircuitBreaker()
}
