package middleware

import (
	"context"
	"net/http"
	"strings"

	"github.com/wealth-copilot/wealth-copilot-go/pkg/httputil"
)

const UserIDKey contextKey = "user_id"

func GetUserID(ctx context.Context) string {
	if id, ok := ctx.Value(UserIDKey).(string); ok {
		return id
	}
	return ""
}

// Auth validates the Authorization header and extracts user_id.
// When disabled, it passes through with a default user_id for development.
func Auth(enabled bool) Middleware {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if !enabled {
				ctx := context.WithValue(r.Context(), UserIDKey, "dev-user")
				next.ServeHTTP(w, r.WithContext(ctx))
				return
			}

			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				httputil.RespondError(w, http.StatusUnauthorized, "missing authorization header")
				return
			}

			token := strings.TrimPrefix(authHeader, "Bearer ")
			if token == authHeader {
				httputil.RespondError(w, http.StatusUnauthorized, "invalid authorization format")
				return
			}

			// TODO: Validate Clerk JWT and extract user_id
			// For now, use the token as user_id placeholder
			userID := token

			ctx := context.WithValue(r.Context(), UserIDKey, userID)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}
