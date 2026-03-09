package domain

// SlackEvent is the outer envelope for all Slack Events API payloads.
type SlackEvent struct {
	Type      string            `json:"type"`
	Token     string            `json:"token"`
	Challenge string            `json:"challenge,omitempty"`
	TeamID    string            `json:"team_id,omitempty"`
	Event     SlackMessageEvent `json:"event"`
}

// SlackMessageEvent covers message, app_mention, reaction, member, pin, and channel events.
type SlackMessageEvent struct {
	Type        string `json:"type"`
	Subtype     string `json:"subtype,omitempty"`
	Channel     string `json:"channel,omitempty"`
	ChannelType string `json:"channel_type,omitempty"` // im, mpim, channel, group
	User        string `json:"user,omitempty"`
	Text        string `json:"text,omitempty"`
	TS          string `json:"ts,omitempty"`
	ThreadTS    string `json:"thread_ts,omitempty"`
	BotID       string `json:"bot_id,omitempty"`

	// Reaction events (reaction_added, reaction_removed)
	Reaction string     `json:"reaction,omitempty"`
	Item     *SlackItem `json:"item,omitempty"` // also used by pin_added/pin_removed
	ItemUser string     `json:"item_user,omitempty"`

	// Member events (member_joined_channel, member_left_channel)
	Inviter string `json:"inviter,omitempty"`

	// Channel rename
	Name string `json:"name,omitempty"`

	// File attachments
	Files []SlackFile `json:"files,omitempty"`
}

// SlackItem references a message or file that was reacted to or pinned.
type SlackItem struct {
	Type    string `json:"type"`
	Channel string `json:"channel,omitempty"`
	TS      string `json:"ts,omitempty"`
}

// SlackFile represents an uploaded file attachment.
type SlackFile struct {
	ID       string `json:"id"`
	Name     string `json:"name,omitempty"`
	Mimetype string `json:"mimetype,omitempty"`
	URL      string `json:"url_private,omitempty"`
	Size     int    `json:"size,omitempty"`
}
