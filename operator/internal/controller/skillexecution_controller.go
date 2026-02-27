package controller

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	batchv1 "k8s.io/api/batch/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"

	agenturav1alpha1 "agentura.io/operator/api/v1alpha1"
)

const (
	jobOwnerKey   = ".metadata.controller"
	ttlAfterDone  = 1 * time.Hour
)

// SkillExecutionReconciler reconciles a SkillExecution object.
type SkillExecutionReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// +kubebuilder:rbac:groups=agentura.io,resources=skillexecutions,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=agentura.io,resources=skillexecutions/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=agentura.io,resources=executionpolicies,verbs=get;list;watch
// +kubebuilder:rbac:groups=batch,resources=jobs,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=pods;pods/log,verbs=get;list;watch
// +kubebuilder:rbac:groups="",resources=configmaps,verbs=get;list;watch;create;delete

func (r *SkillExecutionReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	var exec agenturav1alpha1.SkillExecution
	if err := r.Get(ctx, req.NamespacedName, &exec); err != nil {
		if errors.IsNotFound(err) {
			return ctrl.Result{}, nil
		}
		return ctrl.Result{}, err
	}

	// Terminal states — no further reconciliation needed
	if exec.Status.Phase == agenturav1alpha1.ExecutionPhaseSucceeded ||
		exec.Status.Phase == agenturav1alpha1.ExecutionPhaseFailed {
		return r.handleTTLCleanup(ctx, &exec)
	}

	// Look for existing Job owned by this SkillExecution
	jobName := exec.Name + "-runner"
	var existingJob batchv1.Job
	jobFound := true
	if err := r.Get(ctx, types.NamespacedName{Name: jobName, Namespace: exec.Namespace}, &existingJob); err != nil {
		if errors.IsNotFound(err) {
			jobFound = false
		} else {
			return ctrl.Result{}, err
		}
	}

	if !jobFound {
		// Apply policy defaults
		if err := r.applyPolicyDefaults(ctx, &exec); err != nil {
			logger.Error(err, "failed to apply execution policy defaults")
		}

		// Create Job
		job, err := r.buildJob(&exec, jobName)
		if err != nil {
			return ctrl.Result{}, r.updateStatus(ctx, &exec, agenturav1alpha1.ExecutionPhaseFailed,
				fmt.Sprintf("failed to build job: %v", err))
		}

		if err := ctrl.SetControllerReference(&exec, job, r.Scheme); err != nil {
			return ctrl.Result{}, err
		}

		logger.Info("creating job", "job", jobName)
		if err := r.Create(ctx, job); err != nil {
			return ctrl.Result{}, err
		}

		return ctrl.Result{}, r.updateStatus(ctx, &exec, agenturav1alpha1.ExecutionPhasePending, "Job created")
	}

	// Job exists — check status
	return r.reconcileJobStatus(ctx, &exec, &existingJob)
}

func (r *SkillExecutionReconciler) reconcileJobStatus(ctx context.Context, exec *agenturav1alpha1.SkillExecution, job *batchv1.Job) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	// Job is still active
	if job.Status.Active > 0 {
		if exec.Status.Phase != agenturav1alpha1.ExecutionPhaseRunning {
			now := metav1.Now()
			exec.Status.StartTime = &now
			return ctrl.Result{}, r.updateStatus(ctx, exec, agenturav1alpha1.ExecutionPhaseRunning, "Job is running")
		}
		return ctrl.Result{RequeueAfter: 5 * time.Second}, nil
	}

	// Job succeeded
	if job.Status.Succeeded > 0 {
		result, err := r.extractResultFromPodLogs(ctx, exec, job)
		if err != nil {
			logger.Error(err, "failed to extract result from pod logs")
			result = fmt.Sprintf(`{"error": "failed to extract result: %v"}`, err)
		}

		now := metav1.Now()
		exec.Status.CompletionTime = &now
		exec.Status.Result = result
		exec.Status.PodName = r.getPodName(job)
		return ctrl.Result{}, r.updateStatus(ctx, exec, agenturav1alpha1.ExecutionPhaseSucceeded, "Completed successfully")
	}

	// Job failed
	if job.Status.Failed > 0 {
		now := metav1.Now()
		exec.Status.CompletionTime = &now
		exec.Status.PodName = r.getPodName(job)

		result, _ := r.extractResultFromPodLogs(ctx, exec, job)
		exec.Status.Result = result

		msg := "Job failed"
		if len(job.Status.Conditions) > 0 {
			msg = job.Status.Conditions[0].Message
		}
		return ctrl.Result{}, r.updateStatus(ctx, exec, agenturav1alpha1.ExecutionPhaseFailed, msg)
	}

	// Still pending — requeue
	return ctrl.Result{RequeueAfter: 5 * time.Second}, nil
}

func (r *SkillExecutionReconciler) buildJob(exec *agenturav1alpha1.SkillExecution, jobName string) (*batchv1.Job, error) {
	// Build the execution request JSON for stdin
	execRequest := map[string]any{
		"domain":  exec.Spec.Skill.Domain,
		"skill":   exec.Spec.Skill.Name,
		"role":    exec.Spec.Skill.Role,
		"message": exec.Spec.Input.Message,
	}
	if exec.Spec.Input.Parameters != nil {
		params := make(map[string]any, len(exec.Spec.Input.Parameters))
		for k, v := range exec.Spec.Input.Parameters {
			params[k] = v
		}
		execRequest["parameters"] = params
	}

	requestJSON, err := json.Marshal(execRequest)
	if err != nil {
		return nil, fmt.Errorf("marshaling execution request: %w", err)
	}

	var backoffLimit int32 = 0
	var ttlSeconds int32 = int32(ttlAfterDone.Seconds())

	podSpec := corev1.PodSpec{
		RestartPolicy: corev1.RestartPolicyNever,
		Containers: []corev1.Container{
			{
				Name:            "skill-runner",
				Image:           exec.Spec.Runner.Image,
				ImagePullPolicy: corev1.PullIfNotPresent,
				Env: []corev1.EnvVar{
					{
						Name:  "EXECUTION_REQUEST",
						Value: string(requestJSON),
					},
				},
				Resources: r.buildResources(exec),
			},
		},
	}

	// Set runtime class (gVisor, Kata, etc.)
	if exec.Spec.Runner.RuntimeClassName != nil && *exec.Spec.Runner.RuntimeClassName != "" {
		podSpec.RuntimeClassName = exec.Spec.Runner.RuntimeClassName
	}

	// Mount secrets
	if exec.Spec.Secrets != nil {
		podSpec.Containers[0].EnvFrom = exec.Spec.Secrets.EnvFrom
	}

	job := &batchv1.Job{
		ObjectMeta: metav1.ObjectMeta{
			Name:      jobName,
			Namespace: exec.Namespace,
			Labels: map[string]string{
				"app.kubernetes.io/name":       "skill-runner",
				"app.kubernetes.io/managed-by": "agentura-operator",
				"agentura.io/execution":        exec.Name,
				"agentura.io/domain":           exec.Spec.Skill.Domain,
				"agentura.io/skill":            exec.Spec.Skill.Name,
			},
		},
		Spec: batchv1.JobSpec{
			BackoffLimit:            &backoffLimit,
			TTLSecondsAfterFinished: &ttlSeconds,
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{
						"app.kubernetes.io/name":       "skill-runner",
						"app.kubernetes.io/managed-by": "agentura-operator",
						"agentura.io/execution":        exec.Name,
					},
				},
				Spec: podSpec,
			},
		},
	}

	return job, nil
}

func (r *SkillExecutionReconciler) buildResources(exec *agenturav1alpha1.SkillExecution) corev1.ResourceRequirements {
	if exec.Spec.Runner.Resources.Limits != nil || exec.Spec.Runner.Resources.Requests != nil {
		return exec.Spec.Runner.Resources
	}
	return corev1.ResourceRequirements{
		Limits: corev1.ResourceList{
			corev1.ResourceMemory: resource.MustParse("512Mi"),
			corev1.ResourceCPU:    resource.MustParse("1"),
		},
		Requests: corev1.ResourceList{
			corev1.ResourceMemory: resource.MustParse("256Mi"),
			corev1.ResourceCPU:    resource.MustParse("250m"),
		},
	}
}

func (r *SkillExecutionReconciler) applyPolicyDefaults(ctx context.Context, exec *agenturav1alpha1.SkillExecution) error {
	var policies agenturav1alpha1.ExecutionPolicyList
	if err := r.List(ctx, &policies, client.InNamespace(exec.Namespace)); err != nil {
		return err
	}
	if len(policies.Items) == 0 {
		return nil
	}

	policy := policies.Items[0]

	if exec.Spec.Runner.RuntimeClassName == nil && policy.Spec.RuntimeClassName != nil {
		exec.Spec.Runner.RuntimeClassName = policy.Spec.RuntimeClassName
	}
	if exec.Spec.Runner.Timeout == "" && policy.Spec.DefaultTimeout != "" {
		exec.Spec.Runner.Timeout = policy.Spec.DefaultTimeout
	}
	if exec.Spec.Runner.Resources.Limits == nil && policy.Spec.ResourceDefaults.Limits != nil {
		exec.Spec.Runner.Resources.Limits = policy.Spec.ResourceDefaults.Limits
	}
	if exec.Spec.Runner.Resources.Requests == nil && policy.Spec.ResourceDefaults.Requests != nil {
		exec.Spec.Runner.Resources.Requests = policy.Spec.ResourceDefaults.Requests
	}

	return nil
}

func (r *SkillExecutionReconciler) extractResultFromPodLogs(ctx context.Context, exec *agenturav1alpha1.SkillExecution, job *batchv1.Job) (string, error) {
	// Find pods belonging to the job
	var pods corev1.PodList
	if err := r.List(ctx, &pods, client.InNamespace(exec.Namespace),
		client.MatchingLabels{"agentura.io/execution": exec.Name}); err != nil {
		return "", fmt.Errorf("listing pods: %w", err)
	}

	if len(pods.Items) == 0 {
		return "", fmt.Errorf("no pods found for job %s", job.Name)
	}

	// Pod log reading requires the corev1 REST client, which needs the raw clientset.
	// In the operator context, we store the result from the pod's stdout.
	// For now, return a placeholder — the K8sDispatcher reads logs via clientset.
	return fmt.Sprintf(`{"note": "result in pod %s logs"}`, pods.Items[0].Name), nil
}

func (r *SkillExecutionReconciler) getPodName(job *batchv1.Job) string {
	if job.Status.Succeeded > 0 || job.Status.Failed > 0 {
		return job.Name + "-pod"
	}
	return ""
}

func (r *SkillExecutionReconciler) handleTTLCleanup(ctx context.Context, exec *agenturav1alpha1.SkillExecution) (ctrl.Result, error) {
	if exec.Status.CompletionTime == nil {
		return ctrl.Result{}, nil
	}
	elapsed := time.Since(exec.Status.CompletionTime.Time)
	if elapsed > ttlAfterDone {
		log.FromContext(ctx).Info("cleaning up completed execution", "name", exec.Name)
		return ctrl.Result{}, r.Delete(ctx, exec)
	}
	remaining := ttlAfterDone - elapsed
	return ctrl.Result{RequeueAfter: remaining}, nil
}

func (r *SkillExecutionReconciler) updateStatus(ctx context.Context, exec *agenturav1alpha1.SkillExecution, phase agenturav1alpha1.ExecutionPhase, message string) error {
	exec.Status.Phase = phase
	exec.Status.Message = message
	return r.Status().Update(ctx, exec)
}

func (r *SkillExecutionReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&agenturav1alpha1.SkillExecution{}).
		Owns(&batchv1.Job{}).
		Complete(r)
}
