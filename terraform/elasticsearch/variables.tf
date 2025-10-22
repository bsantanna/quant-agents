variable "es_url" {
  description = "The endpoint URL for the Elasticsearch cluster"
  type        = string
}

variable "es_api_key" {
  description = "The API key for authenticating to the Elasticsearch cluster"
  type        = string
  sensitive   = true
}
