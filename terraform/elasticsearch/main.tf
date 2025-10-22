terraform {
  required_providers {
    elasticstack = {
      source  = "elastic/elasticstack"
      version = "~> 0.11"
    }
  }
}

provider "elasticstack" {
  elasticsearch {
    endpoints = [var.es_url]
    api_key   = var.es_api_key
  }
}

resource "elasticstack_elasticsearch_index_lifecycle" "quant-agents_stocks-eod_policy" {
  name = "quant-agents_stocks-eod_policy"

  hot {
    set_priority {
      priority = 100
    }
  }

  delete {
    min_age = "7d"
    delete {}
  }
}

resource "elasticstack_elasticsearch_index_template" "quant-agents_stocks-eod_template" {
  name = "quant-agents_stocks-eod_template"

  index_patterns = ["quant-agents_stocks-eod-*"]

  template {
    mappings = jsonencode({
      properties = {
        ticker = {
          type = "keyword"
        }
        date = {
          type   = "date"
          format = "yyyy-MM-dd"
        }
        eod_value = {
          type = "double"
        }
        financial_data = {
          type    = "object"
          enabled = false
        }
      }
    })

    settings = jsonencode({
      number_of_shards   = 1
      number_of_replicas = 1
      lifecycle = {
        name = elasticstack_elasticsearch_index_lifecycle.quant-agents_stocks-eod_policy.name
      }
    })
  }
}
