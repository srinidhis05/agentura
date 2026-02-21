package postgres

import (
	"time"

	"gorm.io/gorm"
)

// GORM models — separate from domain types to keep domain clean.

type UserModel struct {
	gorm.Model
	ID                 string `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
	ClerkID            string `gorm:"uniqueIndex;size:200;not null"`
	Email              string `gorm:"size:255"`
	BaseCurrency       string `gorm:"size:3;default:'INR'"`
	RiskProfile        string `gorm:"size:20;default:'moderate'"`
	OnboardingComplete bool   `gorm:"default:false"`
}

func (UserModel) TableName() string { return "users" }

type UserSettingsModel struct {
	gorm.Model
	ID                      uint   `gorm:"primaryKey;autoIncrement"`
	UserID                  string `gorm:"type:uuid;uniqueIndex;not null"`
	NotificationPreferences string `gorm:"type:jsonb;default:'{\"push\":true,\"email\":true}'"`
	HumanApprovalThreshold  string `gorm:"type:jsonb;default:'{\"INR\":50000,\"USD\":500}'"`
	MarketsEnabled          string `gorm:"type:jsonb;default:'[\"india\"]'"`
	BrokersConnected        string `gorm:"type:jsonb;default:'[]'"`
}

func (UserSettingsModel) TableName() string { return "user_settings" }

type TradeModel struct {
	ID             string     `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
	UserID         string     `gorm:"type:uuid;not null;index"`
	Symbol         string     `gorm:"size:50;not null;index"`
	Exchange       string     `gorm:"size:20;not null"`
	Action         string     `gorm:"size:10;not null"`
	EntryPrice     float64    `gorm:"type:decimal(18,6);not null"`
	ExitPrice      *float64   `gorm:"type:decimal(18,6)"`
	Quantity       int        `gorm:"not null"`
	Currency       string     `gorm:"size:3;default:'INR'"`
	PnL            *float64   `gorm:"type:decimal(18,6)"`
	PnLPct         *float64   `gorm:"type:decimal(8,4)"`
	Outcome        *string    `gorm:"size:20;index"`
	HoldDays       *int
	Recommendation *string    `gorm:"size:20"`
	Score          *float64   `gorm:"type:decimal(4,2)"`
	Reasons        string     `gorm:"type:jsonb"`
	GoalID         *string    `gorm:"type:uuid;index"`
	Broker         string     `gorm:"size:20;default:'paper'"`
	CreatedAt      time.Time  `gorm:"autoCreateTime"`
	ClosedAt       *time.Time
}

func (TradeModel) TableName() string { return "trades" }

type PatternModel struct {
	ID           uint    `gorm:"primaryKey;autoIncrement"`
	UserID       string  `gorm:"type:uuid;not null;index"`
	PatternType  string  `gorm:"size:50;not null;index"`
	PatternValue string  `gorm:"size:200;not null"`
	TotalTrades  int     `gorm:"default:0"`
	Wins         int     `gorm:"default:0"`
	Losses       int     `gorm:"default:0"`
	AvgPnLPct    float64 `gorm:"type:decimal(8,4);default:0"`
	WinRate      float64 `gorm:"type:decimal(5,4);default:0"`
	LastUpdated  time.Time `gorm:"autoUpdateTime"`
}

func (PatternModel) TableName() string { return "patterns" }

type FeedbackModel struct {
	ID           uint   `gorm:"primaryKey;autoIncrement"`
	UserID       string `gorm:"type:uuid;not null"`
	TradeID      string `gorm:"type:uuid;not null;index"`
	FeedbackType string `gorm:"size:50;not null"`
	Details      string `gorm:"type:text"`
	Suggestion   string `gorm:"type:text"`
	CreatedAt    time.Time `gorm:"autoCreateTime"`
}

func (FeedbackModel) TableName() string { return "feedback" }

type DailyStatsModel struct {
	ID          uint    `gorm:"primaryKey;autoIncrement"`
	UserID      string  `gorm:"type:uuid;not null"`
	Date        string  `gorm:"type:date;not null"`
	TotalTrades int     `gorm:"default:0"`
	Wins        int     `gorm:"default:0"`
	Losses      int     `gorm:"default:0"`
	GrossPnL    float64 `gorm:"type:decimal(18,6);default:0"`
	Currency    string  `gorm:"size:3;default:'INR'"`
	WinRate     float64 `gorm:"type:decimal(5,4);default:0"`
	Sharpe      float64 `gorm:"type:decimal(6,4);default:0"`
}

func (DailyStatsModel) TableName() string { return "daily_stats" }

type RiskEventModel struct {
	ID                string    `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
	UserID            string    `gorm:"type:uuid;not null;index"`
	Timestamp         time.Time `gorm:"not null;default:now();index"`
	EventType         string    `gorm:"size:50;not null;index"`
	SignalID          *string   `gorm:"type:uuid"`
	Rule              *string   `gorm:"size:100"`
	LimitValue        *string   `gorm:"size:50"`
	ActualValue       *string   `gorm:"size:50"`
	Decision          *string   `gorm:"size:20"`
	Reason            *string   `gorm:"type:text"`
	PortfolioSnapshot string    `gorm:"type:jsonb"`
}

func (RiskEventModel) TableName() string { return "risk_events" }

type CircuitBreakerModel struct {
	ID        uint      `gorm:"primaryKey;autoIncrement"`
	UserID    string    `gorm:"type:uuid;uniqueIndex;not null"`
	IsHalted  bool      `gorm:"default:false"`
	Reason    *string   `gorm:"type:text"`
	HaltedAt  *time.Time
	ResumesAt *time.Time
}

func (CircuitBreakerModel) TableName() string { return "circuit_breaker" }

type GoalModel struct {
	ID             string    `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
	UserID         string    `gorm:"type:uuid;not null;index"`
	Name           string    `gorm:"size:200;not null"`
	Description    *string   `gorm:"type:text"`
	TargetAmount   float64   `gorm:"type:decimal(18,6);not null"`
	TargetCurrency string    `gorm:"size:3;not null"`
	CurrentAmount  float64   `gorm:"type:decimal(18,6);default:0"`
	TargetDate     string    `gorm:"type:date;not null"`
	RiskProfile    string    `gorm:"size:20;not null"`
	Priority       string    `gorm:"size:20;default:'important'"`
	Status         string    `gorm:"size:20;default:'active';index"`
	CreatedAt      time.Time `gorm:"autoCreateTime"`
	UpdatedAt      time.Time `gorm:"autoUpdateTime"`
}

func (GoalModel) TableName() string { return "goals" }

type GoalAllocationModel struct {
	ID         uint    `gorm:"primaryKey;autoIncrement"`
	GoalID     string  `gorm:"type:uuid;not null;index"`
	AssetClass string  `gorm:"size:20;not null"`
	Market     string  `gorm:"size:20;not null"`
	TargetPct  float64 `gorm:"type:decimal(5,2);not null"`
	CurrentPct float64 `gorm:"type:decimal(5,2);default:0"`
	Currency   string  `gorm:"size:3;not null"`
}

func (GoalAllocationModel) TableName() string { return "goal_allocations" }

type GoalProgressModel struct {
	ID              uint      `gorm:"primaryKey;autoIncrement"`
	GoalID          string    `gorm:"type:uuid;not null;index"`
	RecordedAt      time.Time `gorm:"autoCreateTime"`
	Amount          float64   `gorm:"type:decimal(18,6);not null"`
	Currency        string    `gorm:"size:3;not null"`
	FxRateToTarget  *float64  `gorm:"type:decimal(12,6)"`
	Notes           *string   `gorm:"type:text"`
}

func (GoalProgressModel) TableName() string { return "goal_progress" }

type FxRateModel struct {
	ID           uint      `gorm:"primaryKey;autoIncrement"`
	FromCurrency string    `gorm:"size:3;not null;index:idx_fx_pair"`
	ToCurrency   string    `gorm:"size:3;not null;index:idx_fx_pair"`
	Rate         float64   `gorm:"type:decimal(12,6);not null"`
	RecordedAt   time.Time `gorm:"autoCreateTime;index"`
}

func (FxRateModel) TableName() string { return "fx_rates" }

type ActiveScenarioModel struct {
	ID         uint      `gorm:"primaryKey;autoIncrement"`
	ScenarioID string    `gorm:"size:50;not null"`
	DetectedAt time.Time `gorm:"autoCreateTime"`
	Source     *string   `gorm:"type:text"`
	ExpiresAt  *time.Time
}

func (ActiveScenarioModel) TableName() string { return "active_scenarios" }
