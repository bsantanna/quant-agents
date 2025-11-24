variable "es_url" {
  description = "The endpoint URL for the Elasticsearch cluster"
  type        = string
}

variable "kb_url" {
  description = "The endpoint URL for the Kibana UI"
  type        = string
}

variable "es_api_key" {
  description = "The API key for authenticating to the Elasticsearch cluster"
  type        = string
  sensitive   = true
}

variable "kb_anonymous_username" {
  description = "The username for the anonymous access in Kibana"
  type        = string
  sensitive   = true
}

variable "kb_anonymous_password" {
  description = "The password for the anonymous access in Kibana"
  type        = string
  sensitive   = true
}
