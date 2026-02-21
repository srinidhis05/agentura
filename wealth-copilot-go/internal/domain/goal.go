package domain

import "time"

type GoalPriority string

const (
	GoalPriorityCritical  GoalPriority = "critical"
	GoalPriorityImportant GoalPriority = "important"
	GoalPriorityFlexible  GoalPriority = "flexible"
)

type AssetClass string

const (
	AssetClassEquity AssetClass = "equity"
	AssetClassDebt   AssetClass = "debt"
	AssetClassGold   AssetClass = "gold"
	AssetClassCrypto AssetClass = "crypto"
	AssetClassCash   AssetClass = "cash"
)

type Goal struct {
	ID          string           `json:"id"`
	Name        string           `json:"name"`
	TargetAmount Money           `json:"targetAmount"`
	CurrentAmount Money          `json:"currentAmount"`
	TargetDate  time.Time        `json:"targetDate"`
	RiskProfile RiskProfile      `json:"riskProfile"`
	Priority    GoalPriority     `json:"priority"`
	Allocations []GoalAllocation `json:"allocations"`
}

type GoalAllocation struct {
	AssetClass AssetClass `json:"assetClass"`
	Market     Market     `json:"market"`
	TargetPct  Percentage `json:"targetPct"`
	CurrentPct Percentage `json:"currentPct"`
	Currency   Currency   `json:"currency"`
}

type AllocationRequest struct {
	TargetAmount float64     `json:"targetAmount"`
	TargetDate   time.Time   `json:"targetDate"`
	RiskProfile  RiskProfile `json:"riskProfile"`
	BaseCurrency Currency    `json:"baseCurrency"`
}
