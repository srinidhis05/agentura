package domain

import "time"

type User struct {
	ID                 string      `json:"id"`
	ClerkID            string      `json:"clerkId"`
	Email              string      `json:"email"`
	BaseCurrency       Currency    `json:"baseCurrency"`
	RiskProfile        RiskProfile `json:"riskProfile"`
	OnboardingComplete bool        `json:"onboardingComplete"`
	CreatedAt          time.Time   `json:"createdAt"`
	UpdatedAt          time.Time   `json:"updatedAt"`
}

type UserSettings struct {
	UserID                  string                  `json:"userId"`
	NotificationPreferences NotificationPreferences `json:"notificationPreferences"`
	HumanApprovalThreshold  map[Currency]float64    `json:"humanApprovalThreshold"`
	MarketsEnabled          []Market                `json:"marketsEnabled"`
	BrokersConnected        []Broker                `json:"brokersConnected"`
}
