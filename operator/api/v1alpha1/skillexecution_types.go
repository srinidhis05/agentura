package v1alpha1

import (
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// SkillExecutionSpec defines the desired state of a skill execution.
type SkillExecutionSpec struct {
	Skill   SkillRef            `json:"skill"`
	Input   ExecutionInput      `json:"input"`
	Runner  RunnerSpec          `json:"runner"`
	Secrets *SecretsSpec        `json:"secrets,omitempty"`
}

type SkillRef struct {
	Domain string `json:"domain"`
	Name   string `json:"name"`
	Role   string `json:"role,omitempty"`
}

type ExecutionInput struct {
	Message    string            `json:"message,omitempty"`
	Parameters map[string]string `json:"parameters,omitempty"`
}

type RunnerSpec struct {
	Image            string                      `json:"image"`
	RuntimeClassName *string                     `json:"runtimeClassName,omitempty"`
	Resources        corev1.ResourceRequirements `json:"resources,omitempty"`
	Timeout          string                      `json:"timeout,omitempty"`
}

type SecretsSpec struct {
	EnvFrom []corev1.EnvFromSource `json:"envFrom,omitempty"`
}

// ExecutionPhase represents the current phase of a skill execution.
type ExecutionPhase string

const (
	ExecutionPhasePending   ExecutionPhase = "Pending"
	ExecutionPhaseRunning   ExecutionPhase = "Running"
	ExecutionPhaseSucceeded ExecutionPhase = "Succeeded"
	ExecutionPhaseFailed    ExecutionPhase = "Failed"
)

// SkillExecutionStatus defines the observed state of a skill execution.
type SkillExecutionStatus struct {
	Phase          ExecutionPhase `json:"phase,omitempty"`
	StartTime      *metav1.Time   `json:"startTime,omitempty"`
	CompletionTime *metav1.Time   `json:"completionTime,omitempty"`
	Result         string         `json:"result,omitempty"`
	PodName        string         `json:"podName,omitempty"`
	Message        string         `json:"message,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="Phase",type=string,JSONPath=`.status.phase`
// +kubebuilder:printcolumn:name="Skill",type=string,JSONPath=`.spec.skill.name`
// +kubebuilder:printcolumn:name="Domain",type=string,JSONPath=`.spec.skill.domain`
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=`.metadata.creationTimestamp`

// SkillExecution is the Schema for the skillexecutions API.
type SkillExecution struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   SkillExecutionSpec   `json:"spec,omitempty"`
	Status SkillExecutionStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true

// SkillExecutionList contains a list of SkillExecution.
type SkillExecutionList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []SkillExecution `json:"items"`
}

func init() {
	SchemeBuilder.Register(&SkillExecution{}, &SkillExecutionList{})
}
