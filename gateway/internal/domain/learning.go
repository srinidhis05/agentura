package domain

type Outcome string

const (
	OutcomeProfit     Outcome = "profit"
	OutcomeLoss       Outcome = "loss"
	OutcomeStoppedOut Outcome = "stopped_out"
	OutcomeTargetHit  Outcome = "target_hit"
)

type TradeOutcome struct {
	TradeID        string         `json:"tradeId"`
	Symbol         string         `json:"symbol"`
	Action         Action         `json:"action"`
	EntryPrice     float64        `json:"entryPrice"`
	ExitPrice      float64        `json:"exitPrice"`
	Quantity       int            `json:"quantity"`
	PnL            float64        `json:"pnl"`
	PnLPct         float64        `json:"pnlPct"`
	Outcome        Outcome        `json:"outcome"`
	HoldDays       int            `json:"holdDays"`
	Recommendation Recommendation `json:"recommendation"`
	Score          float64        `json:"score"`
	Reasons        []string       `json:"reasons"`
	GoalID         *string        `json:"goalId,omitempty"`
}

type PatternType string

const (
	PatternTypeRecommendation PatternType = "recommendation"
	PatternTypeReason         PatternType = "reason"
	PatternTypeScenario       PatternType = "scenario"
	PatternTypeSector         PatternType = "sector"
)

type LearnedPattern struct {
	PatternType  PatternType `json:"patternType"`
	PatternValue string      `json:"patternValue"`
	TotalTrades  int         `json:"totalTrades"`
	Wins         int         `json:"wins"`
	Losses       int         `json:"losses"`
	AvgPnLPct    float64     `json:"avgPnlPct"`
	WinRate      float64     `json:"winRate"`
}

type OutcomeSummary struct {
	Total   int     `json:"total"`
	Wins    int     `json:"wins"`
	Losses  int     `json:"losses"`
	WinRate float64 `json:"winRate"`
}

type GoalPerformance struct {
	TotalTrades int     `json:"totalTrades"`
	WinRate     float64 `json:"winRate"`
	TotalPnL    float64 `json:"totalPnl"`
	SharpeRatio float64 `json:"sharpeRatio"`
}
