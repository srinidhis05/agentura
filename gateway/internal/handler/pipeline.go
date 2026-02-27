package handler

import (
	"fmt"
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

// ListPipelines proxies GET /api/v1/pipelines to the executor.
func (h *PipelineHandler) ListPipelines(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.ListPipelines(r.Context())
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// ExecutePipeline proxies POST /api/v1/pipelines/{name}/execute to the executor.
func (h *PipelineHandler) ExecutePipeline(w http.ResponseWriter, r *http.Request) {
	name := r.PathValue("name")
	if name == "" {
		httputil.RespondError(w, http.StatusBadRequest, "missing pipeline name")
		return
	}

	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}

	path := fmt.Sprintf("/api/v1/pipelines/%s/execute", name)
	raw, err := h.executor.PostRaw(r.Context(), path, body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// ExecutePipelineStream proxies POST /api/v1/pipelines/{name}/execute-stream as SSE.
func (h *PipelineHandler) ExecutePipelineStream(w http.ResponseWriter, r *http.Request) {
	name := r.PathValue("name")
	if name == "" {
		httputil.RespondError(w, http.StatusBadRequest, "missing pipeline name")
		return
	}

	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}

	path := fmt.Sprintf("/api/v1/pipelines/%s/execute-stream", name)
	resp, err := h.executor.StreamPost(r.Context(), path, body)
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
