variable "airflow_namespace" {
  description = "Kubernetes namespace for Airflow deployment"
  type        = string
  default     = "airflow"
}

variable "airflow_fqdn" {
  description = "Fully qualified domain name for Airflow ingress"
  type        = string
}

variable "quaks_dags_image_tag" {
  description = "Docker image tag for quaks-dags"
  type        = string
  default     = "1.5.27"
}

variable "airflow_admin_username" {
  description = "Username for the Airflow admin user"
  type        = string
  sensitive   = true
}

variable "airflow_admin_password" {
  description = "Password for the Airflow admin user"
  type        = string
  sensitive   = true
}

variable "airflow_admin_email" {
  description = "Email for the Airflow admin user"
  type        = string
  sensitive   = true
}

variable "es_url" {
  description = "Elasticsearch endpoint URL used by DAGs"
  type        = string
  sensitive   = true
}

variable "alpaca_api_key_id" {
  description = "Alpaca Markets API key ID (APCA-API-KEY-ID)"
  type        = string
  sensitive   = true
}

variable "alpaca_api_secret_key" {
  description = "Alpaca Markets API secret key (APCA-API-SECRET-KEY)"
  type        = string
  sensitive   = true
}

variable "finnhub_api_key" {
  description = "Finnhub API key for earnings estimates"
  type        = string
  sensitive   = true
}

variable "pg_image" {
  type        = string
  default     = "bsantanna/cloudnative-pg-vector:17.4"
  description = "PostgreSQL image with pgvector (adjust if needed)"
}

variable "quaks_fqdn" {
  description = "Quaks backend API URL used by DAGs"
  type        = string
  sensitive   = true
}

variable "auth_service_account_username" {
  description = "Quaks service account username for DAG authentication"
  type        = string
  sensitive   = true
}

variable "auth_service_account_secret" {
  description = "Quaks service account password for DAG authentication"
  type        = string
  sensitive   = true
}

variable "quaks_integration_type" {
  description = "LLM integration type used by insights DAGs (e.g. xai_api_v1, openai_api_v1)"
  type        = string
  default     = "xai_api_v1"
}

variable "quaks_integration_api_key" {
  description = "LLM provider API key used by insights DAGs"
  type        = string
  sensitive   = true
}

variable "auth_url" {
  description = "Keycloak base URL for admin REST API (e.g. https://auth.quaks.ai)"
  type        = string
  sensitive   = true
}

variable "auth_admin_username" {
  description = "Keycloak admin username for waiting list user provisioning"
  type        = string
  sensitive   = true
}

variable "auth_admin_secret" {
  description = "Keycloak admin password for waiting list user provisioning"
  type        = string
  sensitive   = true
}

variable "keycloak_realm" {
  description = "Keycloak realm name for waiting list user provisioning"
  type        = string
  default     = "quaks"
}

variable "x_consumer_key" {
  description = "X (Twitter) OAuth 1.0a consumer key (API Key) for @quaksai"
  type        = string
  sensitive   = true
}

variable "x_consumer_secret" {
  description = "X (Twitter) OAuth 1.0a consumer secret (API Key Secret) for @quaksai"
  type        = string
  sensitive   = true
}

variable "x_access_token" {
  description = "X (Twitter) OAuth 1.0a access token for @quaksai"
  type        = string
  sensitive   = true
}

variable "x_access_token_secret" {
  description = "X (Twitter) OAuth 1.0a access token secret for @quaksai"
  type        = string
  sensitive   = true
}
