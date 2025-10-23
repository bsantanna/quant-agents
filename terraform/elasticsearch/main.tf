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

resource "elasticstack_elasticsearch_index_template" "quant-agents_stocks-fundamental-income-statement_template" {
  name = "quant-agents_stocks-fundamental-income-statement_template"

  index_patterns = ["quant-agents_stocks-fundamental-income-statement_*"]

  template {
    mappings = jsonencode({
      dynamic = "strict"
      properties = {
        key_ticker                             = { type = "keyword" }
        fiscal_date_ending                     = { type = "date", format = "yyyy-MM-dd" }
        reported_currency                      = { type = "keyword" }

        gross_profit                           = { type = "long" }
        total_revenue                          = { type = "long" }
        cost_of_revenue                        = { type = "long" }
        cost_of_goods_and_services_sold        = { type = "long" }

        operating_income                       = { type = "long" }
        selling_general_and_administrative     = { type = "long" }
        research_and_development               = { type = "long" }
        operating_expenses                     = { type = "long" }

        investment_income_net                  = { type = "double" }
        net_interest_income                    = { type = "long" }
        interest_income                        = { type = "long" }
        interest_expense                       = { type = "long" }

        non_interest_income                    = { type = "double" }
        other_non_operating_income             = { type = "double" }
        depreciation                           = { type = "double" }
        depreciation_and_amortization          = { type = "long" }

        income_before_tax                      = { type = "long" }
        income_tax_expense                     = { type = "long" }
        interest_and_debt_expense              = { type = "double" }

        net_income_from_continuing_operations  = { type = "long" }
        comprehensive_income_net_of_tax        = { type = "double" }

        ebit                                   = { type = "long" }
        ebitda                                 = { type = "long" }
        net_income                             = { type = "long" }
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
