package handler

import (
	"io"
	"log/slog"
	"net/http"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

// PipelineHandler proxies pipeline requests to the Python executor.
type PipelineHandler struct {
	executor *executor.Client
}

// NewPipelineHandler creates a handler for pipeline endpoints.
func NewPipelineHandler(exec *executor.Client) *PipelineHandler {
	return &PipelineHandler{executor: exec}
}

// ExecuteBuildDeploy proxies the synchronous build-deploy pipeline.
func (h *PipelineHandler) ExecuteBuildDeploy(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}

	raw, err := h.executor.PostRaw(r.Context(), "/api/v1/pipelines/build-deploy/execute", body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// ExecuteBuildDeployStream proxies the SSE streaming build-deploy pipeline.
func (h *PipelineHandler) ExecuteBuildDeployStream(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}

	resp, err := h.executor.StreamPost(r.Context(), "/api/v1/pipelines/build-deploy/execute-stream", body)
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
				slog.Debug("client disconnected during SSE stream", "error", writeErr)
				return
			}
			if ok {
				flusher.Flush()
			}
		}
		if readErr != nil {
			if readErr != io.EOF {
				slog.Error("error reading SSE stream from executor", "error", readErr)
			}
			return
		}
	}
}
