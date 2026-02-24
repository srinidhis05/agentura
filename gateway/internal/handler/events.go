package handler

import (
	"net/http"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

type EventsHandler struct {
	executor *executor.Client
}

func NewEventsHandler(exec *executor.Client) *EventsHandler {
	return &EventsHandler{executor: exec}
}

func (h *EventsHandler) ListEvents(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.ListEvents(r.Context(), r.URL.RawQuery)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}
