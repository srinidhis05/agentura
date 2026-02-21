package domain

import "time"

type Price struct {
	Symbol    string     `json:"symbol"`
	Exchange  Exchange   `json:"exchange"`
	Current   float64    `json:"current"`
	Open      float64    `json:"open"`
	High      float64    `json:"high"`
	Low       float64    `json:"low"`
	Volume    int64      `json:"volume"`
	Change    Percentage `json:"change"`
	Currency  Currency   `json:"currency"`
	Timestamp time.Time  `json:"timestamp"`
}

type RSISignal string

const (
	RSISignalOversold   RSISignal = "OVERSOLD"
	RSISignalOverbought RSISignal = "OVERBOUGHT"
	RSISignalNeutral    RSISignal = "NEUTRAL"
)

type MACDTrend string

const (
	MACDTrendBullish MACDTrend = "BULLISH"
	MACDTrendBearish MACDTrend = "BEARISH"
)

type Trend string

const (
	TrendStrongUptrend   Trend = "STRONG_UPTREND"
	TrendUptrend         Trend = "UPTREND"
	TrendMixed           Trend = "MIXED"
	TrendDowntrend       Trend = "DOWNTREND"
	TrendStrongDowntrend Trend = "STRONG_DOWNTREND"
)

type Fundamentals struct {
	Symbol        string      `json:"symbol"`
	PERatio       *float64    `json:"peRatio"`
	PBRatio       *float64    `json:"pbRatio"`
	DividendYield *Percentage `json:"dividendYield"`
	ROE           *Percentage `json:"roe"`
	ProfitMargin  *Percentage `json:"profitMargin"`
	DebtToEquity  *float64    `json:"debtToEquity"`
	Beta          *float64    `json:"beta"`
	MarketCap     *Money      `json:"marketCap"`
	Sector        *string     `json:"sector"`
	Industry      *string     `json:"industry"`
}

type Technicals struct {
	Symbol        string    `json:"symbol"`
	RSI           float64   `json:"rsi"`
	RSISignal     RSISignal `json:"rsiSignal"`
	MACD          float64   `json:"macd"`
	MACDSignal    float64   `json:"macdSignal"`
	MACDHistogram float64   `json:"macdHistogram"`
	MACDTrend     MACDTrend `json:"macdTrend"`
	SMA20         float64   `json:"sma20"`
	SMA50         *float64  `json:"sma50"`
	SMA200        *float64  `json:"sma200"`
	Trend         Trend     `json:"trend"`
	BBUpper       float64   `json:"bbUpper"`
	BBLower       float64   `json:"bbLower"`
	BBPercentB    float64   `json:"bbPercentB"`
}

type FactorScores struct {
	Value     float64 `json:"value"`     // 0-30
	Quality   float64 `json:"quality"`   // 0-30
	Momentum  float64 `json:"momentum"`  // 0-20
	Technical float64 `json:"technical"` // 0-30
	Risk      float64 `json:"risk"`      // 0-15
}

type StockScore struct {
	Symbol         string         `json:"symbol"`
	Exchange       Exchange       `json:"exchange"`
	Score          float64        `json:"score"`
	Recommendation Recommendation `json:"recommendation"`
	FactorScores   FactorScores   `json:"factorScores"`
	BullSignals    []string       `json:"bullSignals"`
	BearSignals    []string       `json:"bearSignals"`
	Timestamp      time.Time      `json:"timestamp"`
}
