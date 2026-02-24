package domain

import "time"

type NotificationChannel string

const (
	NotificationChannelPush  NotificationChannel = "push"
	NotificationChannelEmail NotificationChannel = "email"
	NotificationChannelSlack NotificationChannel = "slack"
)

type NotificationType string

const (
	NotificationTypeTradeAlert   NotificationType = "trade_alert"
	NotificationTypeRiskWarning  NotificationType = "risk_warning"
	NotificationTypeGoalUpdate   NotificationType = "goal_update"
	NotificationTypeMarketUpdate NotificationType = "market_update"
)

type Notification struct {
	ID        string              `json:"id"`
	UserID    string              `json:"userId"`
	Type      NotificationType    `json:"type"`
	Channel   NotificationChannel `json:"channel"`
	Message   string              `json:"message"`
	Read      bool                `json:"read"`
	CreatedAt time.Time           `json:"createdAt"`
}

type NotificationPreferences struct {
	Push  bool `json:"push"`
	Email bool `json:"email"`
	Slack bool `json:"slack"`
}
