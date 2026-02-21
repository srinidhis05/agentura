package domain

import "time"

type RiskLimits struct {
	MaxPositionPct         Percentage          `json:"maxPositionPct"`
	MaxSectorPct           Percentage          `json:"maxSectorPct"`
	MaxConcentration       int                 `json:"maxConcentration"`
	MaxDailyLossPct        Percentage          `json:"maxDailyLossPct"`
	MaxWeeklyLossPct       Percentage          `json:"maxWeeklyLossPct"`
	MaxDrawdownPct         Percentage          `json:"maxDrawdownPct"`
	MaxTradesPerDay        int                 `json:"maxTradesPerDay"`
	MinHoldingPeriodSec    int                 `json:"minHoldingPeriodSec"`
	RequireStopLoss        bool                `json:"requireStopLoss"`
	MinRiskRewardRatio     float64             `json:"minRiskRewardRatio"`
	MinScoreThreshold      float64             `json:"minScoreThreshold"`
	HumanApprovalThreshold map[Currency]float64 `json:"humanApprovalThreshold"`
}

type ViolationSeverity string

const (
	SeverityWarning ViolationSeverity = "warning"
	SeverityBlock   ViolationSeverity = "block"
	SeverityHalt    ViolationSeverity = "halt"
)

type RiskViolation struct {
	Rule     string            `json:"rule"`
	Severity ViolationSeverity `json:"severity"`
	Limit    string            `json:"limit"`
	Actual   string            `json:"actual"`
	Message  string            `json:"message"`
}

type RiskCheck struct {
	Approved         bool            `json:"approved"`
	Violations       []RiskViolation `json:"violations"`
	Warnings         []string        `json:"warnings"`
	AdjustedQuantity *int            `json:"adjustedQuantity,omitempty"`
}

type CircuitBreakerStatus struct {
	IsHalted  bool       `json:"isHalted"`
	Reason    *string    `json:"reason"`
	HaltedAt  *time.Time `json:"haltedAt"`
	ResumesAt *time.Time `json:"resumesAt"`
}

type DailyStats struct {
	Trades int     `json:"trades"`
	PnL    float64 `json:"pnl"`
}

type RiskStatus struct {
	DailyLossPct   float64              `json:"dailyLossPct"`
	DailyLossLimit float64              `json:"dailyLossLimit"`
	TradesUsed     int                  `json:"tradesUsed"`
	TradesLimit    int                  `json:"tradesLimit"`
	IsHealthy      bool                 `json:"isHealthy"`
	CircuitBreaker CircuitBreakerStatus `json:"circuitBreaker"`
}
