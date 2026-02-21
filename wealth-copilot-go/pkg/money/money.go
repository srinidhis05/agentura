package money

import (
	"fmt"
	"math"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
)

// New creates a Money value with the given amount and currency.
func New(amount float64, currency domain.Currency) domain.Money {
	return domain.Money{
		Amount:   roundTo(amount, 2),
		Currency: currency,
	}
}

// Add returns the sum of two Money values. Panics on currency mismatch.
func Add(a, b domain.Money) domain.Money {
	if a.Currency != b.Currency {
		panic(fmt.Sprintf("currency mismatch: %s + %s", a.Currency, b.Currency))
	}
	return New(a.Amount+b.Amount, a.Currency)
}

// Sub returns the difference of two Money values. Panics on currency mismatch.
func Sub(a, b domain.Money) domain.Money {
	if a.Currency != b.Currency {
		panic(fmt.Sprintf("currency mismatch: %s - %s", a.Currency, b.Currency))
	}
	return New(a.Amount-b.Amount, a.Currency)
}

// Mul multiplies a Money value by a scalar.
func Mul(m domain.Money, factor float64) domain.Money {
	return New(m.Amount*factor, m.Currency)
}

// IsPositive returns true if the amount is greater than zero.
func IsPositive(m domain.Money) bool {
	return m.Amount > 0
}

func roundTo(val float64, places int) float64 {
	pow := math.Pow(10, float64(places))
	return math.Round(val*pow) / pow
}
