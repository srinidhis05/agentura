package notifier

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
)

// Slack implements NotifierPort via Slack webhooks.
type Slack struct {
	webhookURL string
	client     *http.Client
}

func NewSlack(webhookURL string) *Slack {
	return &Slack{
		webhookURL: webhookURL,
		client:     &http.Client{},
	}
}

func (s *Slack) Notify(ctx context.Context, message string, _ domain.NotificationChannel) (bool, error) {
	payload, _ := json.Marshal(map[string]string{"text": message})

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, s.webhookURL, bytes.NewReader(payload))
	if err != nil {
		return false, fmt.Errorf("creating slack request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := s.client.Do(req)
	if err != nil {
		return false, fmt.Errorf("sending slack notification: %w", err)
	}
	defer resp.Body.Close()

	return resp.StatusCode == http.StatusOK, nil
}

func (s *Slack) RequestApproval(_ context.Context, _ string, _ int64, _ *domain.Signal) (*bool, error) {
	// Slack approval would require interactive messages — deferred
	return nil, nil
}
