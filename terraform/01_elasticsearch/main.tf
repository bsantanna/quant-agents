terraform {
  required_providers {
    elasticstack = {
      source  = "elastic/elasticstack"
      version = "~> 0.12"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0.0"
    }
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

data "kubernetes_secret_v1" "es_elastic_user" {
  metadata {
    name      = "elasticsearch-es-elastic-user"
    namespace = "elastic"
  }
}

provider "elasticstack" {
  elasticsearch {
    endpoints = [var.es_url]
    username  = "elastic"
    password  = data.kubernetes_secret_v1.es_elastic_user.data["elastic"]
  }
}

locals {
  search_templates = {
    get_eod_ohlcv_template = "get_eod_ohlcv.mustache"
    get_eod_indicator_ad_template = "get_eod_indicator_ad.mustache"
    get_eod_indicator_adx_template = "get_eod_indicator_adx.mustache"
    get_eod_indicator_cci_template = "get_eod_indicator_cci.mustache"
    get_eod_indicator_ema_template = "get_eod_indicator_ema.mustache"
    get_eod_indicator_macd_template = "get_eod_indicator_macd.mustache"
    get_eod_indicator_obv_template = "get_eod_indicator_obv.mustache"
    get_eod_indicator_rsi_template = "get_eod_indicator_rsi.mustache"
    get_eod_indicator_stoch_template = "get_eod_indicator_stoch.mustache"
    get_markets_news_template = "get_markets_news.mustache"
    get_stats_close_template = "get_stats_close.mustache"
    get_stats_close_bulk_template = "get_stats_close_bulk.mustache"
    get_metadata_market_caps_template = "get_metadata_market_caps.mustache"
    get_metadata_profile_template = "get_metadata_profile.mustache"
    get_insights_news_template = "get_insights_news.mustache"
    get_waiting_list_unprocessed_template = "get_waiting_list_unprocessed.mustache"
    get_published_content_unprocessed_template = "get_published_content_unprocessed.mustache"
  }
}

resource "elasticstack_elasticsearch_script" "search_templates" {
  for_each = local.search_templates
  script_id = each.key
  lang      = "mustache"
  source    = file("${path.module}/search_templates/${each.value}")
}

resource "elasticstack_elasticsearch_index_lifecycle" "quaks_policy" {
  name = "quaks_policy"

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

resource "elasticstack_elasticsearch_index_lifecycle" "quaks_ephemeral_policy" {
  name = "quaks_ephemeral_policy"

  hot {
    set_priority {
      priority = 50
    }
  }

  delete {
    min_age = "2d"
    delete {}
  }
}

resource "elasticstack_elasticsearch_index_template" "quaks_markets-news_template" {
  name = "quaks_markets-news_template"

  index_patterns = ["quaks_markets-news_*"]

  template {
    mappings = jsonencode({
      dynamic = "strict"
      properties = {
        key_ticker     = { type = "keyword" }
        key_url        = { type = "keyword" }
        key_source     = { type = "keyword" }
        date_reference = { type = "date", format = "yyyy-MM-dd" }
        obj_images     = { type = "object", dynamic="true" }
        text_headline  = { type = "text" }
        text_author    = { type = "text" }
        text_summary   = { type = "text" }
        text_content   = { type = "text" }
      }
    })

    settings = jsonencode({
      number_of_shards   = 1
      number_of_replicas = 1

      lifecycle = {
        name = elasticstack_elasticsearch_index_lifecycle.quaks_policy.name
      }
    })
  }
}

resource "elasticstack_elasticsearch_index_template" "quaks_stocks-eod_template" {
  name = "quaks_stocks-eod_template"

  index_patterns = ["quaks_stocks-eod_*"]

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
        name = elasticstack_elasticsearch_index_lifecycle.quaks_policy.name
      }
    })
  }
}

resource "elasticstack_elasticsearch_index_template" "quaks_stocks-insider-trades_template" {
  name = "quaks_stocks-insider-trades_template"

  index_patterns = ["quaks_stocks-insider-trades_*"]

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
        name = elasticstack_elasticsearch_index_lifecycle.quaks_policy.name
      }
    })
  }
}

resource "elasticstack_elasticsearch_index_template" "quaks_stocks-metadata_template" {
  name = "quaks_stocks-metadata_template"

  index_patterns = ["quaks_stocks-metadata_*"]

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
        name = elasticstack_elasticsearch_index_lifecycle.quaks_policy.name
      }
    })
  }
}

resource "elasticstack_elasticsearch_index_template" "quaks_stocks-fundamental-income-statement_template" {
  name = "quaks_stocks-fundamental-income-statement_template"

  index_patterns = ["quaks_stocks-fundamental-income-statement_*"]

  template {
    mappings = jsonencode({
      dynamic = "strict"
      properties = {
        key_ticker         = { type = "keyword" }
        fiscal_date_ending = { type = "date", format = "yyyy-MM-dd" }
        reported_currency  = { type = "keyword" }

        gross_profit                    = { type = "long" }
        total_revenue                   = { type = "long" }
        cost_of_revenue                 = { type = "long" }
        cost_of_goods_and_services_sold = { type = "long" }

        operating_income                   = { type = "long" }
        selling_general_and_administrative = { type = "long" }
        research_and_development           = { type = "long" }
        operating_expenses                 = { type = "long" }

        investment_income_net = { type = "double" }
        net_interest_income   = { type = "long" }
        interest_income       = { type = "long" }
        interest_expense      = { type = "long" }

        non_interest_income           = { type = "double" }
        other_non_operating_income    = { type = "double" }
        depreciation                  = { type = "double" }
        depreciation_and_amortization = { type = "long" }

        income_before_tax         = { type = "long" }
        income_tax_expense        = { type = "long" }
        interest_and_debt_expense = { type = "double" }

        net_income_from_continuing_operations = { type = "long" }
        comprehensive_income_net_of_tax       = { type = "double" }

        ebit       = { type = "long" }
        ebitda     = { type = "long" }
        net_income = { type = "long" }
      }
    })

    settings = jsonencode({
      number_of_shards   = 1
      number_of_replicas = 1

      lifecycle = {
        name = elasticstack_elasticsearch_index_lifecycle.quaks_policy.name
      }
    })
  }
}

resource "elasticstack_elasticsearch_index_template" "quaks_stocks-fundamental-balance-sheet_template" {
  name = "quaks_stocks-fundamental-balance-sheet_template"

  index_patterns = ["quaks_stocks-fundamental-balance-sheet_*"]

  template {
    mappings = jsonencode({
      dynamic = "strict"
      properties = {
        key_ticker         = { type = "keyword" }
        fiscal_date_ending = { type = "date", format = "yyyy-MM-dd" }
        reported_currency  = { type = "keyword" }

        total_assets                                = { type = "long" }
        total_current_assets                        = { type = "long" }
        cash_and_cash_equivalents_at_carrying_value = { type = "long" }
        cash_and_short_term_investments             = { type = "long" }
        inventory                                   = { type = "long" }
        current_net_receivables                     = { type = "long" }
        total_non_current_assets                    = { type = "long" }
        property_plant_equipment                    = { type = "long" }
        accumulated_depreciation_amortization_ppe   = { type = "long" }
        intangible_assets                           = { type = "long" }
        intangible_assets_excluding_goodwill        = { type = "long" }
        goodwill                                    = { type = "long" }
        investments                                 = { type = "long" }
        long_term_investments                       = { type = "long" }
        short_term_investments                      = { type = "long" }
        other_current_assets                        = { type = "long" }
        other_non_current_assets                    = { type = "long" }

        total_liabilities             = { type = "long" }
        total_current_liabilities     = { type = "long" }
        current_accounts_payable      = { type = "long" }
        deferred_revenue              = { type = "long" }
        current_debt                  = { type = "long" }
        short_term_debt               = { type = "long" }
        total_non_current_liabilities = { type = "long" }
        capital_lease_obligations     = { type = "long" }
        long_term_debt                = { type = "long" }
        current_long_term_debt        = { type = "long" }
        long_term_debt_noncurrent     = { type = "long" }
        short_long_term_debt_total    = { type = "long" }
        other_current_liabilities     = { type = "long" }
        other_non_current_liabilities = { type = "long" }

        total_shareholder_equity        = { type = "long" }
        treasury_stock                  = { type = "long" }
        retained_earnings               = { type = "long" }
        common_stock                    = { type = "long" }
        common_stock_shares_outstanding = { type = "long" }
      }
    })

    settings = jsonencode({
      number_of_shards   = 1
      number_of_replicas = 1

      lifecycle = {
        name = elasticstack_elasticsearch_index_lifecycle.quaks_policy.name
      }
    })
  }
}


resource "elasticstack_elasticsearch_index_template" "quaks_stocks-fundamental-cash-flow_template" {
  name = "quaks_stocks-fundamental-cash-flow_template"

  index_patterns = ["quaks_stocks-fundamental-cash-flow_*"]

  template {
    mappings = jsonencode({
      dynamic = "strict"
      properties = {
        key_ticker                                                          = { type = "keyword" }
        fiscal_date_ending                                                  = { type = "date", format = "yyyy-MM-dd" }
        reported_currency                                                   = { type = "keyword" }
        operating_cashflow                                                  = { type = "long" }
        payments_for_operating_activities                                   = { type = "long" }
        proceeds_from_operating_activities                                  = { type = "long" }
        change_in_operating_liabilities                                     = { type = "long" }
        change_in_operating_assets                                          = { type = "long" }
        depreciation_depletion_and_amortization                             = { type = "long" }
        capital_expenditures                                                = { type = "long" }
        change_in_receivables                                               = { type = "long" }
        change_in_inventory                                                 = { type = "long" }
        profit_loss                                                         = { type = "long" }
        cashflow_from_investment                                            = { type = "long" }
        cashflow_from_financing                                             = { type = "long" }
        proceeds_from_repayments_of_short_term_debt                         = { type = "long" }
        payments_for_repurchase_of_common_stock                             = { type = "long" }
        payments_for_repurchase_of_equity                                   = { type = "long" }
        payments_for_repurchase_of_preferred_stock                          = { type = "long" }
        dividend_payout                                                     = { type = "long" }
        dividend_payout_common_stock                                        = { type = "long" }
        dividend_payout_preferred_stock                                     = { type = "long" }
        proceeds_from_issuance_of_common_stock                              = { type = "long" }
        proceeds_from_issuance_of_long_term_debt_and_capital_securities_net = { type = "long" }
        proceeds_from_issuance_of_preferred_stock                           = { type = "long" }
        proceeds_from_repurchase_of_equity                                  = { type = "long" }
        proceeds_from_sale_of_treasury_stock                                = { type = "long" }
        change_in_cash_and_cash_equivalents                                 = { type = "long" }
        change_in_exchange_rate                                             = { type = "long" }
        net_income                                                          = { type = "long" }

      }
    })

    settings = jsonencode({
      number_of_shards   = 1
      number_of_replicas = 1

      lifecycle = {
        name = elasticstack_elasticsearch_index_lifecycle.quaks_policy.name
      }
    })
  }
}



resource "elasticstack_elasticsearch_index_template" "quaks_stocks-fundamental-estimated-earnings_template" {
  name = "quaks_stocks-fundamental-estimated-earnings_template"

  index_patterns = ["quaks_stocks-fundamental-estimated-earnings_*"]

  template {
    mappings = jsonencode({
      dynamic = "strict"
      properties = {
        key_ticker                                  = { type = "keyword" }
        date                                        = { type = "date", format = "yyyy-MM-dd" }
        horizon                                     = { type = "keyword" }
        eps_estimate_average                        = { type = "double" }
        eps_estimate_high                           = { type = "double" }
        eps_estimate_low                            = { type = "double" }
        eps_estimate_analyst_count                  = { type = "double" }
        eps_estimate_average_7_days_ago             = { type = "double" }
        eps_estimate_average_30_days_ago            = { type = "double" }
        eps_estimate_average_60_days_ago            = { type = "double" }
        eps_estimate_average_90_days_ago            = { type = "double" }
        eps_estimate_revision_up_trailing_7_days    = { type = "double" }
        eps_estimate_revision_down_trailing_7_days  = { type = "double" }
        eps_estimate_revision_up_trailing_30_days   = { type = "double" }
        eps_estimate_revision_down_trailing_30_days = { type = "double" }
        revenue_estimate_average                    = { type = "double" }
        revenue_estimate_high                       = { type = "double" }
        revenue_estimate_low                        = { type = "double" }
        revenue_estimate_analyst_count              = { type = "double" }

      }
    })

    settings = jsonencode({
      number_of_shards   = 1
      number_of_replicas = 1

      lifecycle = {
        name = elasticstack_elasticsearch_index_lifecycle.quaks_policy.name
      }
    })
  }
}

resource "elasticstack_elasticsearch_index" "stocks_eod_nyse" {
  name = "quaks_stocks-eod_nyse"
  alias = [{
    name = "quaks_stocks-eod_latest"
  }]
  deletion_protection = false
  depends_on = [elasticstack_elasticsearch_index_template.quaks_stocks-eod_template]
}

resource "elasticstack_elasticsearch_index" "stocks_eod_nasdaq" {
  name = "quaks_stocks-eod_nasdaq"
  alias = [{
    name = "quaks_stocks-eod_latest"
  }]
  deletion_protection = false
  depends_on = [elasticstack_elasticsearch_index_template.quaks_stocks-eod_template]
}

resource "elasticstack_elasticsearch_index" "stocks_eod_amex" {
  name = "quaks_stocks-eod_amex"
  alias = [{
    name = "quaks_stocks-eod_latest"
  }]
  deletion_protection = false
  depends_on = [elasticstack_elasticsearch_index_template.quaks_stocks-eod_template]
}

resource "elasticstack_elasticsearch_index" "markets_news_nyse" {
  name = "quaks_markets-news_nyse"
  alias = [{
    name = "quaks_markets-news_latest"
  }]
  deletion_protection = false
  depends_on = [elasticstack_elasticsearch_index_template.quaks_markets-news_template]
}

resource "elasticstack_elasticsearch_index" "markets_news_nasdaq" {
  name = "quaks_markets-news_nasdaq"
  alias = [{
    name = "quaks_markets-news_latest"
  }]
  deletion_protection = false
  depends_on = [elasticstack_elasticsearch_index_template.quaks_markets-news_template]
}

resource "elasticstack_elasticsearch_index" "markets_news_amex" {
  name = "quaks_markets-news_amex"
  alias = [{
    name = "quaks_markets-news_latest"
  }]
  deletion_protection = false
  depends_on = [elasticstack_elasticsearch_index_template.quaks_markets-news_template]
}

resource "elasticstack_elasticsearch_index" "stocks_metadata_nyse" {
  name = "quaks_stocks-metadata_nyse"
  alias = [{
    name = "quaks_stocks-metadata_latest"
  }]
  deletion_protection = false
  depends_on = [elasticstack_elasticsearch_index_template.quaks_stocks-metadata_template]
}

resource "elasticstack_elasticsearch_index" "stocks_metadata_nasdaq" {
  name = "quaks_stocks-metadata_nasdaq"
  alias = [{
    name = "quaks_stocks-metadata_latest"
  }]
  deletion_protection = false
  depends_on = [elasticstack_elasticsearch_index_template.quaks_stocks-metadata_template]
}

resource "elasticstack_elasticsearch_index" "stocks_metadata_amex" {
  name = "quaks_stocks-metadata_amex"
  alias = [{
    name = "quaks_stocks-metadata_latest"
  }]
  deletion_protection = false
  depends_on = [elasticstack_elasticsearch_index_template.quaks_stocks-metadata_template]
}

resource "elasticstack_elasticsearch_index_template" "quaks_insights-news_template" {
  name = "quaks_insights-news_template"

  index_patterns = ["quaks_insights-news_*"]

  template {
    mappings = jsonencode({
      dynamic = "strict"
      properties = {
        key_author_username     = { type = "keyword" }
        key_skill_name          = { type = "keyword" }
        key_language_model_name = { type = "keyword" }
        date_reference          = { type = "date", format = "yyyy-MM-dd" }
        text_executive_summary  = { type = "text" }
        text_report_html        = { type = "text" }
      }
    })

    settings = jsonencode({
      number_of_shards   = 1
      number_of_replicas = 1

      lifecycle = {
        name = elasticstack_elasticsearch_index_lifecycle.quaks_policy.name
      }
    })
  }
}

resource "elasticstack_elasticsearch_index" "insights_news" {
  name = "quaks_insights-news"
  mappings = jsonencode({
    dynamic = "strict"
    properties = {
      key_author_username     = { type = "keyword" }
      key_skill_name          = { type = "keyword" }
      key_language_model_name = { type = "keyword" }
      date_reference          = { type = "date", format = "yyyy-MM-dd" }
      text_executive_summary  = { type = "text" }
      text_report_html        = { type = "text" }
    }
  })
  deletion_protection = false
  depends_on = [elasticstack_elasticsearch_index_template.quaks_insights-news_template]
}

resource "elasticstack_elasticsearch_index_template" "quaks_insights-finance_template" {
  name = "quaks_insights-finance_template"

  index_patterns = ["quaks_insights-finance*"]

  template {
    mappings = jsonencode({
      dynamic = "strict"
      properties = {
        key_author_username     = { type = "keyword" }
        key_skill_name          = { type = "keyword" }
        key_language_model_name = { type = "keyword" }
        date_reference          = { type = "date", format = "yyyy-MM-dd" }
        text_executive_summary  = { type = "text" }
        text_report_html        = { type = "text" }
      }
    })

    settings = jsonencode({
      number_of_shards   = 1
      number_of_replicas = 1

      lifecycle = {
        name = elasticstack_elasticsearch_index_lifecycle.quaks_policy.name
      }
    })
  }
}

resource "elasticstack_elasticsearch_index" "insights_finance" {
  name = "quaks_insights-finance"
  mappings = jsonencode({
    dynamic = "strict"
    properties = {
      key_author_username     = { type = "keyword" }
      key_skill_name          = { type = "keyword" }
      key_language_model_name = { type = "keyword" }
      date_reference          = { type = "date", format = "yyyy-MM-dd" }
      text_executive_summary  = { type = "text" }
      text_report_html        = { type = "text" }
    }
  })
  deletion_protection = false
  depends_on = [elasticstack_elasticsearch_index_template.quaks_insights-finance_template]
}

resource "elasticstack_elasticsearch_index_template" "quaks_waiting-list_template" {
  name = "quaks_waiting-list_template"

  index_patterns = ["quaks_waiting-list_*"]

  template {
    mappings = jsonencode({
      dynamic = "strict"
      properties = {
        key_email       = { type = "keyword" }
        key_username    = { type = "keyword" }
        text_first_name = { type = "text" }
        text_last_name  = { type = "text" }
        date_timestamp  = { type = "date", format = "strict_date_optional_time" }
        flag_processed  = { type = "boolean" }
      }
    })

    settings = jsonencode({
      number_of_shards   = 1
      number_of_replicas = 1

      lifecycle = {
        name = elasticstack_elasticsearch_index_lifecycle.quaks_ephemeral_policy.name
      }
    })
  }
}

resource "elasticstack_elasticsearch_index" "waiting_list_initial" {
  name = "quaks_waiting-list_initial"
  alias = [{
    name = "quaks_waiting-list_latest"
  }]
  deletion_protection = false
  depends_on = [elasticstack_elasticsearch_index_template.quaks_waiting-list_template]
}

resource "elasticstack_elasticsearch_index_template" "quaks_published-content_template" {
  name = "quaks_published-content_template"

  index_patterns = ["quaks_published-content_*"]

  template {
    mappings = jsonencode({
      dynamic = "strict"
      properties = {
        key_skill_name          = { type = "keyword" }
        key_author_username     = { type = "keyword" }
        key_language_model_name = { type = "keyword" }
        text_executive_summary  = { type = "text" }
        text_report_html        = { type = "text" }
        date_timestamp          = { type = "date", format = "strict_date_optional_time" }
        flag_processed          = { type = "boolean" }
        flag_cancelled          = { type = "boolean" }
      }
    })

    settings = jsonencode({
      number_of_shards   = 1
      number_of_replicas = 1

      lifecycle = {
        name = elasticstack_elasticsearch_index_lifecycle.quaks_ephemeral_policy.name
      }
    })
  }
}

resource "elasticstack_elasticsearch_index" "published_content_initial" {
  name = "quaks_published-content_initial"
  deletion_protection = false
  depends_on = [elasticstack_elasticsearch_index_template.quaks_published-content_template]
}

resource "elasticstack_elasticsearch_security_api_key" "quaks_api_key" {
  name = "quaks-api-key"

  role_descriptors = jsonencode({
    quaks_role = {
      cluster = ["monitor", "manage_security"]
      indices = [
        {
          names      = ["quaks_*"]
          privileges = ["read", "write", "create_index", "manage"]
        },
        {
          names      = [".kibana*"]
          privileges = ["all"]
        }
      ]
      applications = [
        {
          application = "kibana-.kibana"
          privileges  = ["all"]
          resources   = ["*"]
        }
      ]
    }
  })
}

resource "kubernetes_secret_v1" "quaks_elastic_api_secret" {
  metadata {
    name      = "quaks-elastic-api-secret"
    namespace = "quaks"
  }

  data = {
    api-key = elasticstack_elasticsearch_security_api_key.quaks_api_key.encoded
  }
}
