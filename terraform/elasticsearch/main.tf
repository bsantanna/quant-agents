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
        key_ticker     = { type = "keyword" }
        date_reference = { type = "date", format = "yyyy-MM-dd" }
        val_open       = { type = "double" }
        val_close      = { type = "double" }
        val_high       = { type = "double" }
        val_low        = { type = "double" }
        val_volume     = { type = "double" }
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
        key_ticker               = { type = "keyword" }
        key_acquisition_disposal = { type = "keyword" }
        text_executive_name      = { type = "text" }
        text_executive_title     = { type = "text" }
        date_reference           = { type = "date", format = "yyyy-MM-dd" }
        val_share_quantity       = { type = "double" }
        val_share_price          = { type = "double" }
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

resource "elasticstack_elasticsearch_index_template" "quant-agents_stocks-metadata_template" {
  name = "quant-agents_stocks-metadata_template"

  index_patterns = ["quant-agents_stocks-metadata_*"]

  template {
    mappings = jsonencode({
      dynamic = "strict"
      properties = {
        key_ticker      = { type = "keyword" }
        asset_type      = { type = "keyword" }
        name            = { type = "text" }
        description     = { type = "text" }
        cik             = { type = "keyword" }
        exchange        = { type = "keyword" }
        currency        = { type = "keyword" }
        country         = { type = "keyword" }
        sector          = { type = "keyword" }
        industry        = { type = "keyword" }
        address         = { type = "text" }
        official_site   = { type = "keyword" }
        fiscal_year_end = { type = "keyword" }
        latest_quarter  = { type = "date", format = "yyyy-MM-dd" }

        market_capitalization = { type = "long" }
        ebitda                = { type = "double" }
        pe_ratio              = { type = "double" }
        peg_ratio             = { type = "double" }
        book_value            = { type = "double" }
        dividend_per_share    = { type = "double" }
        dividend_yield        = { type = "double" }
        eps                   = { type = "double" }
        revenue_per_share_ttm = { type = "double" }
        profit_margin         = { type = "double" }
        operating_margin_ttm  = { type = "double" }
        return_on_assets_ttm  = { type = "double" }
        return_on_equity_ttm  = { type = "double" }

        revenue_ttm      = { type = "long" }
        gross_profit_ttm = { type = "long" }
        diluted_eps_ttm  = { type = "double" }

        quarterly_earnings_growth_yoy = { type = "double" }
        quarterly_revenue_growth_yoy  = { type = "double" }

        analyst_target_price       = { type = "double" }
        analyst_rating_strong_buy  = { type = "integer" }
        analyst_rating_buy         = { type = "integer" }
        analyst_rating_hold        = { type = "integer" }
        analyst_rating_sell        = { type = "integer" }
        analyst_rating_strong_sell = { type = "integer" }

        trailing_pe              = { type = "double" }
        forward_pe               = { type = "double" }
        price_to_sales_ratio_ttm = { type = "double" }
        price_to_book_ratio      = { type = "double" }
        ev_to_revenue            = { type = "double" }
        ev_to_ebitda             = { type = "double" }
        beta                     = { type = "double" }

        week_52_high           = { type = "double" }
        week_52_low            = { type = "double" }
        moving_average_50_day  = { type = "double" }
        moving_average_200_day = { type = "double" }

        shares_outstanding   = { type = "long" }
        shares_float         = { type = "long" }
        percent_insiders     = { type = "double" }
        percent_institutions = { type = "double" }

        dividend_date    = { type = "date", format = "yyyy-MM-dd" }
        ex_dividend_date = { type = "date", format = "yyyy-MM-dd" }
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
