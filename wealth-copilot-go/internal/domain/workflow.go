package domain

import "time"

type WorkflowTriggerType string

const (
	TriggerPriceAbove  WorkflowTriggerType = "price_above"
	TriggerPriceBelow  WorkflowTriggerType = "price_below"
	TriggerRSIOversold WorkflowTriggerType = "rsi_oversold"
	TriggerSchedule    WorkflowTriggerType = "schedule"
)

type WorkflowActionType string

const (
	WorkflowActionBuy    WorkflowActionType = "buy"
	WorkflowActionSell   WorkflowActionType = "sell"
	WorkflowActionNotify WorkflowActionType = "notify"
	WorkflowActionAlert  WorkflowActionType = "alert"
)

type WorkflowTrigger struct {
	Type   WorkflowTriggerType    `json:"type"`
	Params map[string]interface{} `json:"params"`
}

type WorkflowAction struct {
	Type   WorkflowActionType     `json:"type"`
	Params map[string]interface{} `json:"params"`
}

type Workflow struct {
	ID        string           `json:"id"`
	UserID    string           `json:"userId"`
	Name      string           `json:"name"`
	Trigger   WorkflowTrigger  `json:"trigger"`
	Action    WorkflowAction   `json:"action"`
	Enabled   bool             `json:"enabled"`
	CreatedAt time.Time        `json:"createdAt"`
}

type WorkflowExecution struct {
	ID         string    `json:"id"`
	WorkflowID string    `json:"workflowId"`
	TriggeredAt time.Time `json:"triggeredAt"`
	Success    bool      `json:"success"`
	Result     string    `json:"result"`
}
