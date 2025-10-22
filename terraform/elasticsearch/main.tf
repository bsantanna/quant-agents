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
    min_age = "365d"
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
        tech_sma = {
          type = "double"
        }
        tech_ema = {
          type = "double"
        }
        tech_rsi = {
          type = "double"
        }
        tech_adx = {
          type = "double"
        }
        tech_cci = {
          type = "double"
        }
        tech_chaikin_ad = {
          type = "double"
        }
        tech_obv = {
          type = "double"
        }
        tech_mama = {
          type = "double"
        }
        tech_fama = {
          type = "double"
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
