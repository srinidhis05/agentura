package middleware

import (
	"context"
	"crypto"
	"crypto/rsa"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"math/big"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

const (
	DomainScopeKey contextKey = "domain_scope"
	WorkspaceIDKey contextKey = "workspace_id"
)

func GetDomainScope(ctx context.Context) string {
	if s, ok := ctx.Value(DomainScopeKey).(string); ok {
		return s
	}
	return "*"
}

func GetWorkspaceID(ctx context.Context) string {
	if s, ok := ctx.Value(WorkspaceIDKey).(string); ok {
		return s
	}
	return "default"
}

// JWTConfig holds JWT validation configuration.
type JWTConfig struct {
	Issuer   string // Expected issuer (e.g., "https://clerk.your-app.com")
	Audience string // Expected audience
	JWKSURL  string // JWKS endpoint for key rotation
}

// JWTAuth validates JWT tokens and extracts user identity + domain claims.
// Claims expected in the JWT:
//   - sub: user ID
//   - domain_scope: comma-separated domains (e.g., "hr,finance") or "*" for all
//   - workspace_id: organization/workspace identifier
func JWTAuth(cfg JWTConfig) Middleware {
	keyCache := &jwksCache{url: cfg.JWKSURL}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
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

			claims, err := validateJWT(token, cfg, keyCache)
			if err != nil {
				httputil.RespondError(w, http.StatusUnauthorized, fmt.Sprintf("invalid token: %v", err))
				return
			}

			userID := claims.Subject
			domainScope := claims.DomainScope
			if domainScope == "" {
				domainScope = "*"
			}
			workspaceID := claims.WorkspaceID
			if workspaceID == "" {
				workspaceID = "default"
			}

			ctx := context.WithValue(r.Context(), UserIDKey, userID)
			ctx = context.WithValue(ctx, DomainScopeKey, domainScope)
			ctx = context.WithValue(ctx, WorkspaceIDKey, workspaceID)

			// Forward as headers to upstream (Python executor)
			r.Header.Set("X-User-ID", userID)
			r.Header.Set("X-Domain-Scope", domainScope)
			r.Header.Set("X-Workspace-ID", workspaceID)

			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// Claims represents the JWT payload fields we care about.
type Claims struct {
	Subject     string `json:"sub"`
	Issuer      string `json:"iss"`
	Audience    string `json:"aud"`
	ExpiresAt   int64  `json:"exp"`
	IssuedAt    int64  `json:"iat"`
	DomainScope string `json:"domain_scope"`
	WorkspaceID string `json:"workspace_id"`
}

func validateJWT(tokenStr string, cfg JWTConfig, keyCache *jwksCache) (*Claims, error) {
	parts := strings.Split(tokenStr, ".")
	if len(parts) != 3 {
		return nil, fmt.Errorf("malformed JWT: expected 3 parts, got %d", len(parts))
	}

	headerBytes, err := base64.RawURLEncoding.DecodeString(parts[0])
	if err != nil {
		return nil, fmt.Errorf("decoding header: %w", err)
	}
	var header struct {
		Alg string `json:"alg"`
		Kid string `json:"kid"`
	}
	if err := json.Unmarshal(headerBytes, &header); err != nil {
		return nil, fmt.Errorf("parsing header: %w", err)
	}
	if header.Alg != "RS256" {
		return nil, fmt.Errorf("unsupported algorithm: %s", header.Alg)
	}

	claimsBytes, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return nil, fmt.Errorf("decoding claims: %w", err)
	}
	var claims Claims
	if err := json.Unmarshal(claimsBytes, &claims); err != nil {
		return nil, fmt.Errorf("parsing claims: %w", err)
	}

	now := time.Now().Unix()
	if claims.ExpiresAt > 0 && now > claims.ExpiresAt {
		return nil, fmt.Errorf("token expired")
	}
	if cfg.Issuer != "" && claims.Issuer != cfg.Issuer {
		return nil, fmt.Errorf("issuer mismatch: got %s, want %s", claims.Issuer, cfg.Issuer)
	}

	if cfg.JWKSURL != "" {
		key, err := keyCache.getKey(header.Kid)
		if err != nil {
			return nil, fmt.Errorf("fetching signing key: %w", err)
		}
		if err := verifyRS256(parts[0]+"."+parts[1], parts[2], key); err != nil {
			return nil, fmt.Errorf("signature verification failed: %w", err)
		}
	}

	return &claims, nil
}

func verifyRS256(signingInput, signatureB64 string, key *rsa.PublicKey) error {
	signature, err := base64.RawURLEncoding.DecodeString(signatureB64)
	if err != nil {
		return fmt.Errorf("decoding signature: %w", err)
	}

	hash := sha256.Sum256([]byte(signingInput))
	return rsa.VerifyPKCS1v15(key, crypto.SHA256, hash[:], signature)
}

type jwksCache struct {
	url  string
	mu   sync.RWMutex
	keys map[string]*rsa.PublicKey
	ttl  time.Time
}

func (c *jwksCache) getKey(kid string) (*rsa.PublicKey, error) {
	c.mu.RLock()
	if time.Now().Before(c.ttl) {
		if key, ok := c.keys[kid]; ok {
			c.mu.RUnlock()
			return key, nil
		}
	}
	c.mu.RUnlock()

	return c.refresh(kid)
}

func (c *jwksCache) refresh(kid string) (*rsa.PublicKey, error) {
	c.mu.Lock()
	defer c.mu.Unlock()

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Get(c.url)
	if err != nil {
		return nil, fmt.Errorf("fetching JWKS: %w", err)
	}
	defer resp.Body.Close()

	var jwks struct {
		Keys []struct {
			Kid string `json:"kid"`
			N   string `json:"n"`
			E   string `json:"e"`
			Kty string `json:"kty"`
		} `json:"keys"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&jwks); err != nil {
		return nil, fmt.Errorf("decoding JWKS: %w", err)
	}

	c.keys = make(map[string]*rsa.PublicKey)
	for _, k := range jwks.Keys {
		if k.Kty != "RSA" {
			continue
		}
		nBytes, err := base64.RawURLEncoding.DecodeString(k.N)
		if err != nil {
			continue
		}
		eBytes, err := base64.RawURLEncoding.DecodeString(k.E)
		if err != nil {
			continue
		}
		n := new(big.Int).SetBytes(nBytes)
		e := 0
		for _, b := range eBytes {
			e = e<<8 + int(b)
		}
		c.keys[k.Kid] = &rsa.PublicKey{N: n, E: e}
	}
	c.ttl = time.Now().Add(1 * time.Hour)

	key, ok := c.keys[kid]
	if !ok {
		return nil, fmt.Errorf("key %s not found in JWKS", kid)
	}
	return key, nil
}
