package domain

import "time"

type Signal struct {
	ID         string          `json:"id"`
	Timestamp  time.Time       `json:"timestamp"`
	Action     Action          `json:"action"`
	Symbol     string          `json:"symbol"`
	Exchange   Exchange        `json:"exchange"`
	Quantity   int             `json:"quantity"`
	EntryPrice float64         `json:"entryPrice"`
	StopLoss   float64         `json:"stopLoss"`
	Target     float64         `json:"target"`
	Confidence Percentage      `json:"confidence"`
	Score      float64         `json:"score"`
	Reasons    []string        `json:"reasons"`
	Metadata   *SignalMetadata `json:"metadata,omitempty"`
}

type SignalMetadata struct {
	Scenario        string `json:"scenario,omitempty"`
	GoalID          string `json:"goalId,omitempty"`
	RebalanceReason string `json:"rebalanceReason,omitempty"`
}
