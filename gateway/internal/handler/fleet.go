package handler

import (
	"fmt"
	"io"
	"log/slog"
	"net/http"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

// FleetHandler proxies fleet session requests to the Python executor.
type FleetHandler struct {
	executor *executor.Client
}

// NewFleetHandler creates a handler for fleet endpoints.
func NewFleetHandler(exec *executor.Client) *FleetHandler {
	return &FleetHandler{executor: exec}
}

// ListSessions proxies GET /api/v1/fleet/sessions to the executor.
func (h *FleetHandler) ListSessions(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.ListFleetSessions(r.Context(), r.URL.RawQuery)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// GetSession proxies GET /api/v1/fleet/sessions/{session_id} to the executor.
func (h *FleetHandler) GetSession(w http.ResponseWriter, r *http.Request) {
	sessionID := r.PathValue("session_id")
	raw, err := h.executor.GetFleetSession(r.Context(), sessionID)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// CancelSession proxies POST /api/v1/fleet/sessions/{session_id}/cancel to the executor.
func (h *FleetHandler) CancelSession(w http.ResponseWriter, r *http.Request) {
	sessionID := r.PathValue("session_id")
	path := fmt.Sprintf("/api/v1/fleet/sessions/%s/cancel", sessionID)
	raw, err := h.executor.PostRaw(r.Context(), path, nil)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// StreamSession proxies GET /api/v1/fleet/sessions/{session_id}/stream as SSE.
func (h *FleetHandler) StreamSession(w http.ResponseWriter, r *http.Request) {
	sessionID := r.PathValue("session_id")
	path := fmt.Sprintf("/api/v1/fleet/sessions/%s/stream", sessionID)

	resp, err := h.executor.StreamGet(r.Context(), path)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	defer resp.Body.Close()

	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.WriteHeader(http.StatusOK)

	flusher, ok := w.(http.Flusher)
	if !ok {
		slog.Warn("response writer does not support flushing")
	}

	buf := make([]byte, 4096)
	for {
		n, readErr := resp.Body.Read(buf)
		if n > 0 {
			if _, writeErr := w.Write(buf[:n]); writeErr != nil {
				slog.Debug("client disconnected during fleet SSE stream", "error", writeErr)
				return
			}
			if ok {
				flusher.Flush()
			}
		}
		if readErr != nil {
			if readErr != io.EOF {
				slog.Error("error reading fleet SSE stream from executor", "error", readErr)
			}
			return
		}
	}
}
