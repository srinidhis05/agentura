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
// Optional threadTS posts as a thread reply.
func postSlackBlocksFromService(botToken, channel, fallbackText string, blocks []map[string]any, threadTS ...string) (string, error) {
	msg := map[string]any{
		"channel": channel,
		"text":    fallbackText,
		"blocks":  blocks,
	}
	if len(threadTS) > 0 && threadTS[0] != "" {
		msg["thread_ts"] = threadTS[0]
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

// parseRichOutput extracts the rich_output object and fallback text from skill output.
func parseRichOutput(text string) (map[string]any, string, bool) {
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
	fallback, _ := parsed["fallback"].(string)
	if fallback == "" {
		if title, ok := richOutput["title"].(string); ok {
			fallback = title
		} else {
			fallback = "Skill result"
		}
	}
	return richOutput, fallback, true
}

// statusToEmoji maps rich_output status to the appropriate emoji.
// 4-tier model: briefings (info), scans (healthy/watch), deep-dives (insight), signals (signal/critical).
// Backward-compatible: "warning" maps to "watch".
func statusToEmoji(status string) string {
	switch status {
	case "info":
		return "\U0001F4CA " // 📊 briefing — neutral, no emotional charge
	case "healthy":
		return "\u2705 " // ✅ scan all clear — reassuring
	case "watch":
		return "\U0001F440 " // 👀 worth looking at — curiosity, not fear
	case "warning":
		return "\U0001F440 " // 👀 backward compat → watch
	case "insight":
		return "\U0001F52C " // 🔬 deep dive — scholarly
	case "signal":
		return "\U0001F4E1 " // 📡 strategic signal detected
	case "critical":
		return "\U0001F534 " // 🔴 structural shift — reserved for rare, truly urgent
	default:
		return ""
	}
}

// buildHeaderBlocks creates a compact 2-block summary for the top-level Slack message.
// Header block with status emoji + title, context block with truncated summary.
func buildHeaderBlocks(skill string, rich map[string]any) []map[string]any {
	var blocks []map[string]any

	title, _ := rich["title"].(string)
	if title == "" {
		title = skill
	}

	statusEmoji := ""
	if status, ok := rich["status"].(string); ok {
		statusEmoji = statusToEmoji(status)
	}

	blocks = append(blocks, map[string]any{
		"type": "header",
		"text": map[string]any{
			"type":  "plain_text",
			"text":  statusEmoji + title,
			"emoji": true,
		},
	})

	summary, _ := rich["summary"].(string)
	if summary != "" {
		if len(summary) > 200 {
			summary = summary[:197] + "..."
		}
		blocks = append(blocks, map[string]any{
			"type": "context",
			"elements": []map[string]any{
				{
					"type": "mrkdwn",
					"text": summary + "  \u00b7  _details in thread_ :thread:",
				},
			},
		})
	} else {
		blocks = append(blocks, map[string]any{
			"type": "context",
			"elements": []map[string]any{
				{
					"type": "mrkdwn",
					"text": "_Full report in thread_ :thread:",
				},
			},
		})
	}

	return blocks
}

// renderRichBlocks converts a rich_output structure to Slack Block Kit blocks.
// Contract: { title, status?, summary?, sections: [{heading?, body}], footer? }
func renderRichBlocks(rich map[string]any) []map[string]any {
	var blocks []map[string]any

	if title, ok := rich["title"].(string); ok && title != "" {
		statusEmoji := ""
		if status, ok := rich["status"].(string); ok {
			statusEmoji = statusToEmoji(status)
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

// postSkillOutputToSlack posts skill output to Slack.
// Rich outputs: compact header as top-level message, full content as thread reply.
// Plain text: posted directly as top-level message.
func postSkillOutputToSlack(botToken, channel, skill, output string) {
	rich, fallback, ok := parseRichOutput(output)
	if !ok {
		postSlackMessageFromService(botToken, channel,
			fmt.Sprintf(":white_check_mark: *%s* completed:\n%s", skill, truncateOutput(output, 3500)))
		return
	}

	blocks := renderRichBlocks(rich)
	if len(blocks) == 0 {
		postSlackMessageFromService(botToken, channel,
			fmt.Sprintf(":white_check_mark: *%s* completed:\n%s", skill, truncateOutput(output, 3500)))
		return
	}

	// Post compact header as top-level message
	headerBlocks := buildHeaderBlocks(skill, rich)
	ts, err := postSlackBlocksFromService(botToken, channel, fallback, headerBlocks)
	if err != nil {
		slog.Error("heartbeat: header post failed, falling back to flat post",
			"skill", skill, "error", err)
		postSlackBlocksFromService(botToken, channel, fallback, blocks)
		return
	}

	// Post full content as thread reply
	slog.Info("heartbeat: posting rich_output as thread reply",
		"skill", skill, "blocks", len(blocks), "thread_ts", ts)
	if _, err := postSlackBlocksFromService(botToken, channel, fallback, blocks, ts); err != nil {
		slog.Error("heartbeat: thread reply failed",
			"skill", skill, "error", err)
	}
}
