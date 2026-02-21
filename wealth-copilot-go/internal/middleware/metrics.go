package middleware

import (
	"net/http"
	"strconv"
	"sync/atomic"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	httpRequestsTotal = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "http_requests_total",
		Help: "Total HTTP requests (traffic)",
	}, []string{"method", "path", "status"})

	httpRequestDuration = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name:    "http_request_duration_seconds",
		Help:    "HTTP request latency",
		Buckets: []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5},
	}, []string{"method", "path"})

	httpRequestErrors = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "http_request_errors_total",
		Help: "Total HTTP 5xx errors",
	}, []string{"method", "path"})

	httpInFlight int64
	httpInFlightGauge = promauto.NewGaugeFunc(prometheus.GaugeOpts{
		Name: "http_requests_in_flight",
		Help: "Current in-flight HTTP requests (saturation)",
	}, func() float64 {
		return float64(atomic.LoadInt64(&httpInFlight))
	})
)

// suppress unused variable warning
var _ = httpInFlightGauge

func Metrics(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt64(&httpInFlight, 1)
		defer atomic.AddInt64(&httpInFlight, -1)

		start := time.Now()
		sw := &statusWriter{ResponseWriter: w, status: http.StatusOK}

		next.ServeHTTP(sw, r)

		duration := time.Since(start).Seconds()
		status := strconv.Itoa(sw.status)
		path := r.URL.Path

		httpRequestsTotal.WithLabelValues(r.Method, path, status).Inc()
		httpRequestDuration.WithLabelValues(r.Method, path).Observe(duration)

		if sw.status >= 500 {
			httpRequestErrors.WithLabelValues(r.Method, path).Inc()
		}
	})
}
