package service

import (
	"context"
	"log/slog"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/robfig/cron/v3"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/internal/config"
)

var (
	cronExecutionsTotal = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "agentura_cron_executions_total",
		Help: "Total cron-triggered skill executions",
	}, []string{"domain", "skill", "status"})

	cronExecutionDuration = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name:    "agentura_cron_execution_duration_seconds",
		Help:    "Duration of cron-triggered executions",
		Buckets: prometheus.DefBuckets,
	}, []string{"domain", "skill"})
)

// JobInfo describes a registered cron job for the status API.
type JobInfo struct {
	Domain   string    `json:"domain"`
	Skill    string    `json:"skill"`
	Schedule string    `json:"schedule"`
	NextRun  time.Time `json:"next_run"`
	PrevRun  time.Time `json:"prev_run"`
}

// SchedulerStatus reports scheduler health.
type SchedulerStatus struct {
	Running  bool   `json:"running"`
	Timezone string `json:"timezone"`
	JobCount int    `json:"job_count"`
	LastSync string `json:"last_sync"`
}

// Scheduler manages cron-triggered skill executions.
type Scheduler struct {
	executor     *executor.Client
	cfg          config.TriggersConfig
	cron         *cron.Cron
	mu           sync.RWMutex
	jobs         []JobInfo
	running      bool
	lastSync     time.Time
	stopPollCh   chan struct{}
	pollInterval time.Duration
}

// NewScheduler creates a scheduler that discovers cron triggers from the executor.
func NewScheduler(exec *executor.Client, cfg config.TriggersConfig) *Scheduler {
	loc, err := time.LoadLocation(cfg.Timezone)
	if err != nil {
		slog.Warn("invalid timezone, falling back to UTC", "timezone", cfg.Timezone, "error", err)
		loc = time.UTC
	}

	return &Scheduler{
		executor:     exec,
		cfg:          cfg,
		cron:         cron.New(cron.WithLocation(loc)),
		stopPollCh:   make(chan struct{}),
		pollInterval: time.Duration(cfg.Cron.PollInterval) * time.Second,
	}
}

// Start discovers triggers from the executor and begins the cron scheduler.
func (s *Scheduler) Start(ctx context.Context) {
	if !s.cfg.Enabled || !s.cfg.Cron.Enabled {
		slog.Info("cron scheduler disabled")
		return
	}

	slog.Info("starting cron scheduler", "timezone", s.cfg.Timezone, "poll_interval", s.pollInterval)

	s.syncTriggers(ctx)
	s.cron.Start()

	s.mu.Lock()
	s.running = true
	s.mu.Unlock()

	slog.Info("cron scheduler started", "job_count", len(s.jobs))

	go s.pollLoop(ctx)
}

// Stop gracefully shuts down the scheduler.
func (s *Scheduler) Stop() {
	s.mu.Lock()
	s.running = false
	s.mu.Unlock()

	close(s.stopPollCh)

	ctx := s.cron.Stop()
	<-ctx.Done()
	slog.Info("cron scheduler stopped")
}

// ListJobs returns registered cron jobs with timing info.
func (s *Scheduler) ListJobs() []JobInfo {
	s.mu.RLock()
	defer s.mu.RUnlock()

	result := make([]JobInfo, 0, len(s.jobs))
	entries := s.cron.Entries()

	for i, job := range s.jobs {
		j := job
		if i < len(entries) {
			j.NextRun = entries[i].Next
			j.PrevRun = entries[i].Prev
		}
		result = append(result, j)
	}
	return result
}

// Status returns scheduler health.
func (s *Scheduler) Status() SchedulerStatus {
	s.mu.RLock()
	defer s.mu.RUnlock()

	lastSync := ""
	if !s.lastSync.IsZero() {
		lastSync = s.lastSync.Format(time.RFC3339)
	}

	return SchedulerStatus{
		Running:  s.running,
		Timezone: s.cfg.Timezone,
		JobCount: len(s.jobs),
		LastSync: lastSync,
	}
}

func (s *Scheduler) pollLoop(ctx context.Context) {
	ticker := time.NewTicker(s.pollInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			s.resync(ctx)
		case <-s.stopPollCh:
			return
		case <-ctx.Done():
			return
		}
	}
}

func (s *Scheduler) resync(ctx context.Context) {
	// Stop existing cron, rebuild with fresh triggers
	stopCtx := s.cron.Stop()
	<-stopCtx.Done()

	loc, _ := time.LoadLocation(s.cfg.Timezone)
	if loc == nil {
		loc = time.UTC
	}
	s.cron = cron.New(cron.WithLocation(loc))

	s.syncTriggers(ctx)
	s.cron.Start()

	slog.Info("cron scheduler resynced", "job_count", len(s.jobs))
}

func (s *Scheduler) syncTriggers(ctx context.Context) {
	fetchCtx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	triggers, err := s.executor.FetchTriggers(fetchCtx)
	if err != nil {
		slog.Error("failed to fetch triggers from executor", "error", err)
		return
	}

	s.mu.Lock()
	s.jobs = nil
	s.lastSync = time.Now()
	s.mu.Unlock()

	for _, t := range triggers {
		for _, td := range t.Triggers {
			if td.Type != "cron" || td.Schedule == "" {
				continue
			}

			domain := t.Domain
			skill := t.Skill
			schedule := td.Schedule

			_, err := s.cron.AddFunc(schedule, func() {
				s.executeCronJob(domain, skill)
			})
			if err != nil {
				slog.Error("failed to register cron job",
					"domain", domain, "skill", skill,
					"schedule", schedule, "error", err)
				continue
			}

			job := JobInfo{
				Domain:   domain,
				Skill:    skill,
				Schedule: schedule,
			}
			s.mu.Lock()
			s.jobs = append(s.jobs, job)
			s.mu.Unlock()

			slog.Info("registered cron job",
				"domain", domain, "skill", skill,
				"schedule", schedule)
		}
	}
}

func (s *Scheduler) executeCronJob(domain, skill string) {
	slog.Info("cron executing", "domain", domain, "skill", skill)

	start := time.Now()
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	req := executor.ExecuteRequest{
		InputData: map[string]any{"trigger": "cron"},
	}

	_, err := s.executor.Execute(ctx, domain, skill, req)
	duration := time.Since(start).Seconds()
	cronExecutionDuration.WithLabelValues(domain, skill).Observe(duration)

	if err != nil {
		cronExecutionsTotal.WithLabelValues(domain, skill, "error").Inc()
		slog.Error("cron execution failed",
			"domain", domain, "skill", skill,
			"duration_s", duration, "error", err)
		return
	}

	cronExecutionsTotal.WithLabelValues(domain, skill, "success").Inc()
	slog.Info("cron execution completed",
		"domain", domain, "skill", skill,
		"duration_s", duration)
}
