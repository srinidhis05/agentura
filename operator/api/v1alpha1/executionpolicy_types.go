package v1alpha1

import (
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// ExecutionPolicySpec defines cluster-wide defaults for skill executions.
type ExecutionPolicySpec struct {
	RuntimeClassName        *string                     `json:"runtimeClassName,omitempty"`
	MaxConcurrentExecutions int                         `json:"maxConcurrentExecutions,omitempty"`
	DefaultTimeout          string                      `json:"defaultTimeout,omitempty"`
	ResourceDefaults        corev1.ResourceRequirements `json:"resourceDefaults,omitempty"`
	NetworkPolicy           *NetworkPolicySpec          `json:"networkPolicy,omitempty"`
}

type NetworkPolicySpec struct {
	AllowEgress []EgressRule `json:"allowEgress,omitempty"`
}

type EgressRule struct {
	To    []string `json:"to,omitempty"`
	Ports []int    `json:"ports,omitempty"`
}

// +kubebuilder:object:root=true

// ExecutionPolicy is the Schema for the executionpolicies API.
type ExecutionPolicy struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec ExecutionPolicySpec `json:"spec,omitempty"`
}

// +kubebuilder:object:root=true

// ExecutionPolicyList contains a list of ExecutionPolicy.
type ExecutionPolicyList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []ExecutionPolicy `json:"items"`
}

func init() {
	SchemeBuilder.Register(&ExecutionPolicy{}, &ExecutionPolicyList{})
}
