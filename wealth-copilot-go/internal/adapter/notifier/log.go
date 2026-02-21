package notifier

import (
	"context"
	"log/slog"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
)

// Log implements NotifierPort by logging notifications (for dev/demo).
type Log struct{}

func NewLog() *Log { return &Log{} }

func (l *Log) Notify(_ context.Context, message string, channel domain.NotificationChannel) (bool, error) {
	slog.Info("notification",
		"channel", string(channel),
		"message", message,
	)
	return true, nil
}

func (l *Log) RequestApproval(_ context.Context, message string, _ int64, _ *domain.Signal) (*bool, error) {
	slog.Info("approval requested (auto-approving in dev)",
		"message", message,
	)
	approved := true
	return &approved, nil
}
