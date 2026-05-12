variable "quaks_namespace" {
  description = "Kubernetes namespace for Quaks deployment"
  type        = string
  default     = "quaks"
}

variable "agent_lab_chart_version" {
  description = "Helm chart version for Quaks"
  type        = string
}

variable "quaks_image_tag" {
  description = "Docker image tag for Quaks application"
  type        = string
  default     = "1.5.29"
}

variable "quaks_image_repository" {
  description = "Docker image repository for Quaks application"
  type        = string
  default     = "bsantanna/quaks-app"
}

variable "quaks_fqdn" {
  description = "Fully qualified domain name for Quaks ingress"
  type        = string
  default     = "quaks.ai"
}

variable "telemetry_endpoint" {
  description = "OpenTelemetry collector endpoint URL"
  type        = string
  default     = "http://otel-collector-opentelemetry-collector.otel.svc.cluster.local:4318"
}
