package handler

import (
	"net/http"

	"github.com/wealth-copilot/wealth-copilot-go/pkg/httputil"
)

type NotificationHandler struct {
	// notifier port.NotifierPort — will be wired later
}

func NewNotificationHandler() *NotificationHandler {
	return &NotificationHandler{}
}

func (h *NotificationHandler) List(w http.ResponseWriter, _ *http.Request) {
	// TODO: fetch from persistence
	httputil.RespondJSON(w, http.StatusOK, []interface{}{})
}

func (h *NotificationHandler) SetPreferences(w http.ResponseWriter, r *http.Request) {
	// TODO: update user notification preferences
	httputil.RespondJSON(w, http.StatusOK, map[string]string{"status": "updated"})
}
