package service

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"strings"
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

// postSlackBlocksFromService posts a Block Kit message to a Slack channel.
func postSlackBlocksFromService(botToken, channel, fallbackText string, blocks []map[string]any) (string, error) {
	msg := map[string]any{
		"channel": channel,
		"text":    fallbackText,
		"blocks":  blocks,
	}

	payload, err := json.Marshal(msg)
	if err != nil {
		return "", fmt.Errorf("marshaling slack blocks: %w", err)
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
		return "", fmt.Errorf("posting blocks to slack: %w", err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("slack API returned %d: %s", resp.StatusCode, body)
	}

	var slackResp struct {
		OK    bool   `json:"ok"`
		TS    string `json:"ts"`
		Error string `json:"error"`
	}
	json.Unmarshal(body, &slackResp)
	if !slackResp.OK {
		return "", fmt.Errorf("slack blocks error: %s", slackResp.Error)
	}
	return slackResp.TS, nil
}

// tryParseRichOutputService parses skill output for rich_output JSON and converts to Block Kit.
func tryParseRichOutputService(text string) ([]map[string]any, string, bool) {
	text = strings.TrimSpace(text)
	if len(text) == 0 {
		return nil, "", false
	}

	jsonStr := text
	if text[0] != '{' {
		idx := strings.Index(text, "{\"fallback\"")
		if idx < 0 {
			idx = strings.Index(text, "{\"rich_output\"")
		}
		if idx < 0 {
			return nil, "", false
		}
		jsonStr = text[idx:]
		if end := strings.LastIndex(jsonStr, "}"); end >= 0 {
			jsonStr = jsonStr[:end+1]
		}
	}

	var parsed map[string]any
	if err := json.Unmarshal([]byte(jsonStr), &parsed); err != nil {
		return nil, "", false
	}
	richOutput, ok := parsed["rich_output"].(map[string]any)
	if !ok {
		return nil, "", false
	}
	blocks := renderRichBlocks(richOutput)
	if len(blocks) == 0 {
		return nil, "", false
	}
	fallback, _ := parsed["fallback"].(string)
	if fallback == "" {
		if title, ok := richOutput["title"].(string); ok {
			fallback = title
		} else {
			fallback = "Skill result"
		}
	}
	return blocks, fallback, true
}

// renderRichBlocks converts a rich_output structure to Slack Block Kit blocks.
// Contract: { title, status?, summary?, sections: [{heading?, body}], footer? }
func renderRichBlocks(rich map[string]any) []map[string]any {
	var blocks []map[string]any

	if title, ok := rich["title"].(string); ok && title != "" {
		statusEmoji := ""
		if status, ok := rich["status"].(string); ok {
			switch status {
			case "healthy":
				statusEmoji = "\U0001F7E2 "
			case "warning":
				statusEmoji = "\U0001F7E1 "
			case "critical":
				statusEmoji = "\U0001F534 "
			}
		}
		blocks = append(blocks, map[string]any{
			"type": "header",
			"text": map[string]any{
				"type":  "plain_text",
				"text":  statusEmoji + title,
				"emoji": true,
			},
		})
	}

	if summary, ok := rich["summary"].(string); ok && summary != "" {
		blocks = append(blocks, map[string]any{
			"type": "section",
			"text": map[string]any{
				"type": "mrkdwn",
				"text": summary,
			},
		})
	}

	hasSummary := rich["summary"] != nil && rich["summary"] != ""
	if sections, ok := rich["sections"].([]any); ok {
		for i, s := range sections {
			section, ok := s.(map[string]any)
			if !ok {
				continue
			}
			if i > 0 || hasSummary {
				blocks = append(blocks, map[string]any{"type": "divider"})
			}

			heading, _ := section["heading"].(string)
			body, _ := section["body"].(string)

			text := body
			if heading != "" {
				text = "*" + heading + "*\n" + body
			}
			if text == "" {
				continue
			}
			if len(text) > 3000 {
				text = text[:2990] + "\n...(truncated)"
			}

			blocks = append(blocks, map[string]any{
				"type": "section",
				"text": map[string]any{
					"type": "mrkdwn",
					"text": text,
				},
			})
		}
	}

	if footer, ok := rich["footer"].(string); ok && footer != "" {
		blocks = append(blocks, map[string]any{
			"type": "context",
			"elements": []map[string]any{
				{
					"type": "mrkdwn",
					"text": footer,
				},
			},
		})
	}

	return blocks
}

// postSkillOutputToSlack posts skill output to Slack, using Block Kit if rich_output is present.
func postSkillOutputToSlack(botToken, channel, skill, output string) {
	if blocks, fallback, ok := tryParseRichOutputService(output); ok {
		slog.Info("heartbeat: posting rich_output as Block Kit",
			"skill", skill, "blocks", len(blocks))
		if _, err := postSlackBlocksFromService(botToken, channel, fallback, blocks); err != nil {
			slog.Error("heartbeat: Block Kit post failed, falling back to text",
				"skill", skill, "error", err)
			postSlackMessageFromService(botToken, channel,
				fmt.Sprintf(":white_check_mark: *%s* completed:\n%s", skill, truncateOutput(output, 3500)))
		}
		return
	}
	// No rich_output — post as plain text
	postSlackMessageFromService(botToken, channel,
		fmt.Sprintf(":white_check_mark: *%s* completed:\n%s", skill, truncateOutput(output, 3500)))
}
