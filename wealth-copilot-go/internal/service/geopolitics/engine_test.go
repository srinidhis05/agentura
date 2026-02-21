package geopolitics

import (
	"testing"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
)

func TestGetScenarios(t *testing.T) {
	e := NewEngine()
	s := e.GetScenarios()
	if len(s) != 7 {
		t.Errorf("expected 7 scenarios, got %d", len(s))
	}
}

func TestDetectScenario(t *testing.T) {
	tests := []struct {
		input  string
		wantID string
	}{
		{"Taiwan tensions escalate", "china-taiwan"},
		{"Chip war between US and China", "china-taiwan"},
		{"NATO expansion in eastern Europe", "russia-nato"},
		{"Ukraine peace talks fail", "russia-nato"},
		{"Iran threatens strait of hormuz", "middle-east"},
		{"OPEC cuts production", "middle-east"},
		{"Galwan valley standoff resumes", "india-china"},
		{"LAC tension at Arunachal border", "india-china"},
		{"BRICS announce new currency plan", "dollar-dedollarization"},
		{"Renewable energy investment soars", "climate-energy"},
		{"Fed rate cut expected in March", "fed-rate-cycle"},
		{"No match for this random text", ""},
	}

	e := NewEngine()
	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			result := e.DetectScenario(tt.input)
			if tt.wantID == "" {
				if result != nil {
					t.Errorf("expected nil, got %s", result.ID)
				}
				return
			}
			if result == nil {
				t.Fatalf("expected scenario %s, got nil", tt.wantID)
			}
			if result.ID != tt.wantID {
				t.Errorf("got %s, want %s", result.ID, tt.wantID)
			}
		})
	}
}

func TestGetStocksForScenario(t *testing.T) {
	e := NewEngine()

	stocks := e.GetStocksForScenario("china-taiwan", []domain.Market{domain.MarketIndia, domain.MarketUS})
	if len(stocks) == 0 {
		t.Error("expected stocks for china-taiwan in india+us markets")
	}

	empty := e.GetStocksForScenario("nonexistent", []domain.Market{domain.MarketIndia})
	if len(empty) != 0 {
		t.Error("expected empty for nonexistent scenario")
	}
}

func TestGetCurrencyImpact(t *testing.T) {
	e := NewEngine()

	impact := e.GetCurrencyImpact("russia-nato")
	if impact == nil {
		t.Fatal("expected non-nil impact")
	}
	if impact[domain.CurrencyUSD] != 0.15 {
		t.Errorf("USD impact = %f, want 0.15", impact[domain.CurrencyUSD])
	}
	if impact[domain.CurrencyEUR] != -0.15 {
		t.Errorf("EUR impact = %f, want -0.15", impact[domain.CurrencyEUR])
	}
}

func TestDetectActiveScenarios(t *testing.T) {
	news := []string{
		"Taiwan chip war escalates",
		"NATO deploys troops to eastern Europe",
		"Taiwan blockade feared", // duplicate should be deduped
	}

	results := DetectActiveScenarios(news)
	if len(results) != 2 {
		t.Errorf("expected 2 unique scenarios, got %d", len(results))
	}
}

func TestCalculateNetCurrencyImpact(t *testing.T) {
	e := NewEngine()
	s1 := e.GetScenarios()[0] // china-taiwan
	s2 := e.GetScenarios()[1] // russia-nato

	impact := CalculateNetCurrencyImpact([]domain.GeopoliticalScenario{s1, s2})

	// USD should be averaged: (0.10 + 0.15) / 2 = 0.125
	if impact[domain.CurrencyUSD] < 0.12 || impact[domain.CurrencyUSD] > 0.13 {
		t.Errorf("USD impact = %f, want ~0.125", impact[domain.CurrencyUSD])
	}

	// Single scenario should not average
	single := CalculateNetCurrencyImpact([]domain.GeopoliticalScenario{s1})
	if single[domain.CurrencyUSD] != 0.10 {
		t.Errorf("single USD impact = %f, want 0.10", single[domain.CurrencyUSD])
	}
}
