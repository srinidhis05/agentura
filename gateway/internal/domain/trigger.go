package domain

// TriggerType represents the activation mechanism for a skill.
type TriggerType string

const (
	TriggerCron    TriggerType = "cron"
	TriggerWebhook TriggerType = "webhook"
	TriggerCommand TriggerType = "command"
	TriggerSlack   TriggerType = "slack"
	TriggerAPI     TriggerType = "api"
	TriggerManual  TriggerType = "manual"
	TriggerAlways  TriggerType = "always"
)

// TriggerConfig is a single trigger definition from agentura.config.yaml.
type TriggerConfig struct {
	Type        TriggerType `json:"type"`
	Schedule    string      `json:"schedule,omitempty"`
	Pattern     string      `json:"pattern,omitempty"`
	Description string      `json:"description,omitempty"`
}

// SkillTrigger groups all triggers for a single skill.
type SkillTrigger struct {
	Domain   string          `json:"domain"`
	Skill    string          `json:"skill"`
	Triggers []TriggerConfig `json:"triggers"`
}

// InboundMessage is the normalized input from any external channel.
type InboundMessage struct {
	Source   string         `json:"source"`
	Channel  string         `json:"channel"`
	UserID   string         `json:"user_id,omitempty"`
	Text     string         `json:"text"`
	Domain   string         `json:"domain,omitempty"`
	Skill    string         `json:"skill,omitempty"`
	Metadata map[string]any `json:"metadata,omitempty"`
}
