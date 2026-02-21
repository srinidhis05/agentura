package port

import (
	"context"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
)

type NotifierPort interface {
	Notify(ctx context.Context, message string, channel domain.NotificationChannel) (bool, error)
	RequestApproval(ctx context.Context, message string, timeoutMs int64, tradeDetails *domain.Signal) (*bool, error)
}
