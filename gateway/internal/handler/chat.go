package handler

import (
	"net/http"

	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

type ChatHandler struct {
	// agentClient will be the gRPC client to Python agent service
}

func NewChatHandler() *ChatHandler {
	return &ChatHandler{}
}

type chatRequest struct {
	Message string `json:"message"`
	UserID  string `json:"userId,omitempty"`
}

func (h *ChatHandler) SendMessage(w http.ResponseWriter, r *http.Request) {
	var req chatRequest
	if err := httputil.DecodeJSON(r, &req); err != nil {
		httputil.RespondError(w, http.StatusBadRequest, err.Error())
		return
	}

	// TODO: Forward to Python agent via gRPC stream
	httputil.RespondJSON(w, http.StatusOK, map[string]string{
		"response": "Chat integration pending — gRPC bridge to Python agent not yet connected.",
	})
}
