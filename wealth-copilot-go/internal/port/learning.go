package port

import (
	"context"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
)

type LearningPort interface {
	RecordTrade(ctx context.Context, outcome domain.TradeOutcome) error
	GetPattern(ctx context.Context, patternType string, value string) (*domain.LearnedPattern, error)
	GetAllPatterns(ctx context.Context) ([]domain.LearnedPattern, error)
	RecordFeedback(ctx context.Context, tradeID, feedbackType, details string, suggestion *string) error
	GetRecentOutcomes(ctx context.Context, hours int) (domain.OutcomeSummary, error)
	GetPerformanceByGoal(ctx context.Context, goalID string) (domain.GoalPerformance, error)
}
