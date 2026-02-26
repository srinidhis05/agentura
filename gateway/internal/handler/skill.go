package handler

import (
	"encoding/json"
	"io"
	"net/http"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

type SkillHandler struct {
	executor   *executor.Client
	dispatcher executor.ExecutionDispatcher
}

func NewSkillHandler(exec *executor.Client, dispatcher executor.ExecutionDispatcher) *SkillHandler {
	return &SkillHandler{executor: exec, dispatcher: dispatcher}
}

func (h *SkillHandler) CreateSkill(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}
	raw, err := h.executor.CreateSkill(r.Context(), json.RawMessage(body))
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	w.Write(raw)
}

func (h *SkillHandler) ListSkills(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.ListSkills(r.Context())
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

func (h *SkillHandler) GetSkill(w http.ResponseWriter, r *http.Request) {
	domain := r.PathValue("domain")
	skill := r.PathValue("skill")

	raw, err := h.executor.GetSkill(r.Context(), domain, skill)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

func (h *SkillHandler) ListExecutions(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.ListExecutions(r.Context(), r.URL.RawQuery)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

func (h *SkillHandler) GetExecution(w http.ResponseWriter, r *http.Request) {
	execID := r.PathValue("execution_id")

	raw, err := h.executor.GetExecution(r.Context(), execID)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

func (h *SkillHandler) GetAnalytics(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.GetAnalytics(r.Context())
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

func (h *SkillHandler) ExecuteSkill(w http.ResponseWriter, r *http.Request) {
	domain := r.PathValue("domain")
	skill := r.PathValue("skill")

	var req executor.ExecuteRequest
	if err := httputil.DecodeJSON(r, &req); err != nil {
		httputil.RespondError(w, http.StatusBadRequest, err.Error())
		return
	}

	// Use dispatcher if available (docker/k8s modes), else fall back to proxy
	if h.dispatcher != nil {
		dispatchReq := executor.ExecutionDispatchRequest{
			Domain:    domain,
			Skill:     skill,
			InputData: req.InputData,
			DryRun:    req.DryRun,
		}
		result, err := h.dispatcher.Dispatch(r.Context(), dispatchReq)
		if err != nil {
			httputil.RespondError(w, http.StatusBadGateway, err.Error())
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write(result)
		return
	}

	result, err := h.executor.Execute(r.Context(), domain, skill, req)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(result)
}

func (h *SkillHandler) ApproveExecution(w http.ResponseWriter, r *http.Request) {
	execID := r.PathValue("execution_id")

	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}

	raw, err := h.executor.ApproveExecution(r.Context(), execID, json.RawMessage(body))
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

func (h *SkillHandler) Correct(w http.ResponseWriter, r *http.Request) {
	domain := r.PathValue("domain")
	skill := r.PathValue("skill")

	var req executor.CorrectRequest
	if err := httputil.DecodeJSON(r, &req); err != nil {
		httputil.RespondError(w, http.StatusBadRequest, err.Error())
		return
	}

	result, err := h.executor.Correct(r.Context(), domain, skill, req)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(result)
}
