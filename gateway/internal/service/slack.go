package service

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

const slackAPIBase = "https://slack.com/api"

// postSlackMessageFromService posts a message to a Slack channel.
// Used by the heartbeat runner (service layer) to deliver alerts.
func postSlackMessageFromService(botToken, channel, text string) (string, error) {
	if len(text) > 3900 {
		text = text[:3900] + "\n... (truncated)"
	}

	payload, err := json.Marshal(map[string]string{
		"channel": channel,
		"text":    text,
	})
	if err != nil {
		return "", fmt.Errorf("marshaling message: %w", err)
	}

	req, err := http.NewRequest(http.MethodPost, slackAPIBase+"/chat.postMessage", bytes.NewReader(payload))
	if err != nil {
		return "", fmt.Errorf("creating request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+botToken)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("posting to slack: %w", err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("slack API returned %d: %s", resp.StatusCode, body)
	}

	var slackResp struct {
		OK bool   `json:"ok"`
		TS string `json:"ts"`
	}
	json.Unmarshal(body, &slackResp)
	return slackResp.TS, nil
}
