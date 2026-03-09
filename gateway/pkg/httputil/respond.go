package httputil

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"strings"
)

type ErrorResponse struct {
	Error   string `json:"error"`
	Code    int    `json:"code"`
	Details string `json:"details,omitempty"`
}

// RespondJSON writes a JSON response with the given status code.
func RespondJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if data != nil {
		if err := json.NewEncoder(w).Encode(data); err != nil {
			slog.Error("failed to encode response", "error", err)
		}
	}
}

// RespondError writes a JSON error response.
func RespondError(w http.ResponseWriter, status int, message string) {
	RespondJSON(w, status, ErrorResponse{
		Error: message,
		Code:  status,
	})
}

// RespondErrorWithDetails writes a JSON error response with additional details.
func RespondErrorWithDetails(w http.ResponseWriter, status int, message, details string) {
	RespondJSON(w, status, ErrorResponse{
		Error:   message,
		Code:    status,
		Details: details,
	})
}

// ExtractStatusCode parses an HTTP status code from error messages matching
// the pattern "executor returned %d: ..." (from http_client.go). Returns
// fallback if no code is found.
func ExtractStatusCode(err error, fallback int) int {
	if err == nil {
		return fallback
	}
	msg := err.Error()
	// Match "executor returned 404: ..." pattern from http_client.go
	prefix := "executor returned "
	idx := strings.Index(msg, prefix)
	if idx < 0 {
		return fallback
	}
	var code int
	_, parseErr := fmt.Sscanf(msg[idx+len(prefix):], "%d", &code)
	if parseErr != nil || code < 100 || code > 599 {
		return fallback
	}
	return code
}
