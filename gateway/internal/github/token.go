package github

import (
	"context"
	"crypto/rsa"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

// TokenProvider generates fresh GitHub App installation tokens on demand.
// Uses the App's private key to create a JWT, then exchanges it for an installation token.
// Tokens are cached until 5 minutes before expiry.
type TokenProvider struct {
	appID          string
	installationID string
	privateKey     *rsa.PrivateKey

	mu          sync.RWMutex
	cachedToken string
	expiresAt   time.Time
}

// NewTokenProvider creates a TokenProvider from raw config values.
// Returns nil if appID or privateKeyPEM is empty (allows fallback to static token).
func NewTokenProvider(appID, privateKeyPEM, installationID string) (*TokenProvider, error) {
	if appID == "" || privateKeyPEM == "" || installationID == "" {
		return nil, nil
	}

	// Normalize PEM: env var substitution or YAML parsing may replace real
	// newlines with literal "\n" sequences. Restore them before parsing.
	normalizedPEM := strings.ReplaceAll(privateKeyPEM, `\n`, "\n")

	key, err := jwt.ParseRSAPrivateKeyFromPEM([]byte(normalizedPEM))
	if err != nil {
		return nil, fmt.Errorf("parsing GitHub App private key: %w", err)
	}

	return &TokenProvider{
		appID:          appID,
		installationID: installationID,
		privateKey:     key,
	}, nil
}

// Token returns a valid installation token, refreshing if needed.
func (p *TokenProvider) Token(ctx context.Context) (string, error) {
	p.mu.RLock()
	if p.cachedToken != "" && time.Now().Before(p.expiresAt) {
		token := p.cachedToken
		p.mu.RUnlock()
		return token, nil
	}
	p.mu.RUnlock()

	p.mu.Lock()
	defer p.mu.Unlock()

	// Double-check after acquiring write lock
	if p.cachedToken != "" && time.Now().Before(p.expiresAt) {
		return p.cachedToken, nil
	}

	token, expiresAt, err := p.generateInstallationToken(ctx)
	if err != nil {
		return "", err
	}

	p.cachedToken = token
	p.expiresAt = expiresAt
	return token, nil
}

func (p *TokenProvider) generateInstallationToken(ctx context.Context) (string, time.Time, error) {
	now := time.Now()
	claims := jwt.RegisteredClaims{
		IssuedAt:  jwt.NewNumericDate(now.Add(-60 * time.Second)),
		ExpiresAt: jwt.NewNumericDate(now.Add(10 * time.Minute)),
		Issuer:    p.appID,
	}

	jwtToken := jwt.NewWithClaims(jwt.SigningMethodRS256, claims)
	signed, err := jwtToken.SignedString(p.privateKey)
	if err != nil {
		return "", time.Time{}, fmt.Errorf("signing JWT: %w", err)
	}

	url := fmt.Sprintf("https://api.github.com/app/installations/%s/access_tokens", p.installationID)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, nil)
	if err != nil {
		return "", time.Time{}, fmt.Errorf("creating token request: %w", err)
	}
	req.Header.Set("Authorization", "Bearer "+signed)
	req.Header.Set("Accept", "application/vnd.github+json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", time.Time{}, fmt.Errorf("requesting installation token: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		return "", time.Time{}, fmt.Errorf("installation token request returned %d", resp.StatusCode)
	}

	var result struct {
		Token     string    `json:"token"`
		ExpiresAt time.Time `json:"expires_at"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", time.Time{}, fmt.Errorf("decoding installation token response: %w", err)
	}

	// Cache until 5 minutes before expiry
	safeExpiry := result.ExpiresAt.Add(-5 * time.Minute)
	return result.Token, safeExpiry, nil
}
