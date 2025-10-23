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

resource "elasticstack_elasticsearch_index_lifecycle" "quant-agents_policy" {
  name = "quant-agents_policy"

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

  index_patterns = ["quant-agents_stocks-eod_*"]

  template {
    mappings = jsonencode({
      dynamic = "strict"
      properties = {
        key_ticker = {
          type = "keyword"
        }
        date_reference = {
          type   = "date"
          format = "yyyy-MM-dd"
        }
        val_open = {
          type = "double"
        }
        val_close = {
          type = "double"
        }
        val_high = {
          type = "double"
        }
        val_low = {
          type = "double"
        }
        val_volume = {
          type = "double"
        }
      }
    })

    settings = jsonencode({
      number_of_shards   = 1
      number_of_replicas = 1

      lifecycle = {
        name = elasticstack_elasticsearch_index_lifecycle.quant-agents_policy.name
      }
    })
  }
}

resource "elasticstack_elasticsearch_index_template" "quant-agents_stocks-insider-trades_template" {
  name = "quant-agents_stocks-insider-trades_template"

  index_patterns = ["quant-agents_stocks-insider-trades_*"]

  template {
    mappings = jsonencode({
      dynamic = "strict"
      properties = {
        key_ticker = {
          type = "keyword"
        }
        key_acquisition_disposal = {
          type = "keyword"
        }
        text_executive_name = {
          type = "text"
        }
        text_executive_title = {
          type = "text"
        }
        date_reference = {
          type   = "date"
          format = "yyyy-MM-dd"
        }
        val_share_quantity = {
          type = "double"
        }
        val_share_price = {
          type = "double"
        }
      }
    })

    settings = jsonencode({
      number_of_shards   = 1
      number_of_replicas = 1

      lifecycle = {
        name = elasticstack_elasticsearch_index_lifecycle.quant-agents_policy.name
      }
    })
  }
}
