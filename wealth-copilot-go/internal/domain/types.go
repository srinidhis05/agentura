package domain

// Value objects — immutable enums and primitives.

type Currency string

const (
	CurrencyINR Currency = "INR"
	CurrencyUSD Currency = "USD"
	CurrencyAED Currency = "AED"
	CurrencyGBP Currency = "GBP"
	CurrencyEUR Currency = "EUR"
	CurrencySGD Currency = "SGD"
	CurrencyCAD Currency = "CAD"
	CurrencyAUD Currency = "AUD"
)

var AllCurrencies = []Currency{
	CurrencyINR, CurrencyUSD, CurrencyAED, CurrencyGBP,
	CurrencyEUR, CurrencySGD, CurrencyCAD, CurrencyAUD,
}

type Exchange string

const (
	ExchangeNSE    Exchange = "NSE"
	ExchangeBSE    Exchange = "BSE"
	ExchangeNASDAQ Exchange = "NASDAQ"
	ExchangeNYSE   Exchange = "NYSE"
	ExchangeLSE    Exchange = "LSE"
	ExchangeCRYPTO Exchange = "CRYPTO"
)

type Action string

const (
	ActionBUY  Action = "BUY"
	ActionSELL Action = "SELL"
	ActionHOLD Action = "HOLD"
)

type Recommendation string

const (
	RecommendationStrongBuy  Recommendation = "STRONG_BUY"
	RecommendationBuy        Recommendation = "BUY"
	RecommendationHold       Recommendation = "HOLD"
	RecommendationSell       Recommendation = "SELL"
	RecommendationStrongSell Recommendation = "STRONG_SELL"
)

type RiskProfile string

const (
	RiskProfileConservative RiskProfile = "conservative"
	RiskProfileModerate     RiskProfile = "moderate"
	RiskProfileAggressive   RiskProfile = "aggressive"
)

type TradingMode string

const (
	TradingModePaper TradingMode = "paper"
	TradingModeLive  TradingMode = "live"
)

type Market string

const (
	MarketIndia     Market = "india"
	MarketUS        Market = "us"
	MarketUK        Market = "uk"
	MarketUAE       Market = "uae"
	MarketSingapore Market = "singapore"
	MarketCrypto    Market = "crypto"
)

type Money struct {
	Amount   float64  `json:"amount"`
	Currency Currency `json:"currency"`
}

type Percentage struct {
	Value float64 `json:"value"` // 0-100
}
