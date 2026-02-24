package middleware

import (
	"context"
	"net/http"
	"os"
	"strings"

	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

const UserIDKey contextKey = "user_id"

func GetUserID(ctx context.Context) string {
	if id, ok := ctx.Value(UserIDKey).(string); ok {
		return id
	}
	return ""
}

// Auth validates the Authorization header and extracts user identity.
// When JWT is configured (JWKS_URL set), it validates RS256 tokens and
// extracts domain_scope + workspace_id claims.
// When disabled, it passes through with dev defaults.
func Auth(enabled bool) Middleware {
	// Check if JWT validation is configured
	jwksURL := os.Getenv("JWKS_URL")
	issuer := os.Getenv("JWT_ISSUER")

	if enabled && jwksURL != "" {
		return JWTAuth(JWTConfig{
			Issuer:  issuer,
			JWKSURL: jwksURL,
		})
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if !enabled {
				ctx := context.WithValue(r.Context(), UserIDKey, "dev-user")
				ctx = context.WithValue(ctx, DomainScopeKey, "*")
				ctx = context.WithValue(ctx, WorkspaceIDKey, "default")
				r.Header.Set("X-User-ID", "dev-user")
				r.Header.Set("X-Domain-Scope", "*")
				r.Header.Set("X-Workspace-ID", "default")
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

			// Simple token auth (no JWT validation — use for API keys)
			userID := token
			ctx := context.WithValue(r.Context(), UserIDKey, userID)
			ctx = context.WithValue(ctx, DomainScopeKey, "*")
			ctx = context.WithValue(ctx, WorkspaceIDKey, "default")
			r.Header.Set("X-User-ID", userID)
			r.Header.Set("X-Domain-Scope", "*")
			r.Header.Set("X-Workspace-ID", "default")
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}
