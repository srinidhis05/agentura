package port

import (
	"context"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
)

type GoalsPort interface {
	CreateGoal(ctx context.Context, goal domain.Goal) (domain.Goal, error)
	GetGoal(ctx context.Context, goalID string) (*domain.Goal, error)
	GetAllGoals(ctx context.Context, userID string) ([]domain.Goal, error)
	UpdateGoalProgress(ctx context.Context, goalID string, amount float64) (domain.Goal, error)
	SuggestAllocation(ctx context.Context, req domain.AllocationRequest) ([]domain.GoalAllocation, error)
	RebalanceGoal(ctx context.Context, goalID string) ([]domain.Signal, error)
}
