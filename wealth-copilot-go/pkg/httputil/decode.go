package httputil

import (
	"encoding/json"
	"fmt"
	"net/http"
)

// DecodeJSON decodes a JSON request body into the given destination.
// Returns an error message suitable for the client if decoding fails.
func DecodeJSON(r *http.Request, dest interface{}) error {
	if r.Body == nil {
		return fmt.Errorf("request body is empty")
	}

	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()

	if err := decoder.Decode(dest); err != nil {
		return fmt.Errorf("invalid JSON: %w", err)
	}
	return nil
}
