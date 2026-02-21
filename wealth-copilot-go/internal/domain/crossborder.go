package domain

import "time"

type FxRate struct {
	From      Currency  `json:"from"`
	To        Currency  `json:"to"`
	Rate      float64   `json:"rate"`
	Timestamp time.Time `json:"timestamp"`
}

type CurrencyImpactPeriod string

const (
	Period1M CurrencyImpactPeriod = "1M"
	Period3M CurrencyImpactPeriod = "3M"
	Period6M CurrencyImpactPeriod = "6M"
	Period1Y CurrencyImpactPeriod = "1Y"
	Period3Y CurrencyImpactPeriod = "3Y"
)

type CurrencyImpact struct {
	NominalReturn Percentage           `json:"nominalReturn"`
	FxImpact      Percentage           `json:"fxImpact"`
	RealReturn    Percentage           `json:"realReturn"`
	Period        CurrencyImpactPeriod `json:"period"`
}

type RemittanceRecommendation struct {
	Recommendation string  `json:"recommendation"`
	ExpectedRate   float64 `json:"expectedRate"`
	Confidence     float64 `json:"confidence"`
}
