from app.services.agent_types.quaks.insights.financial_analyst.v1.company_profile_summary import (
    _as_int,
    _consensus,
    summarize_company_profile,
)


def _sample_doc(**overrides):
    base = {
        "key_ticker": "NVDA",
        "name": "NVIDIA Corp",
        "description": "A very long company description " * 50,
        "address": "2788 San Tomas Expressway",
        "cik": "0001045810",
        "official_site": "https://nvidia.com",
        "asset_type": "Common Stock",
        "fiscal_year_end": "January",
        "latest_quarter": "2025-10-31",
        "exchange": "NASDAQ",
        "currency": "USD",
        "country": "USA",
        "sector": "Technology",
        "industry": "Semiconductors",
        "market_capitalization": 4_380_000_000_000,
        "shares_outstanding": 24_000_000_000,
        "shares_float": 23_500_000_000,
        "pe_ratio": 36.48,
        "trailing_pe": 36.48,
        "forward_pe": 274.21,
        "peg_ratio": 1.5,
        "price_to_book_ratio": 28.81,
        "price_to_sales_ratio_ttm": 20.28,
        "ev_to_ebitda": 35.0,
        "ev_to_revenue": 18.0,
        "book_value": 6.5,
        "profit_margin": 0.556,
        "operating_margin_ttm": 0.6038,
        "return_on_equity_ttm": 1.0437,
        "return_on_assets_ttm": 0.7576,
        "eps": 4.5,
        "diluted_eps_ttm": 4.4,
        "revenue_per_share_ttm": 8.2,
        "revenue_ttm": 200_000_000_000,
        "gross_profit_ttm": 150_000_000_000,
        "ebitda": 110_000_000_000,
        "quarterly_revenue_growth_yoy": 0.7321,
        "quarterly_earnings_growth_yoy": 0.9666,
        "beta": 2.39,
        "week_52_high": 212.19,
        "week_52_low": 86.62,
        "moving_average_50_day": 180.0,
        "moving_average_200_day": 150.0,
        "dividend_per_share": 0.04,
        "dividend_yield": 0.0002,
        "dividend_date": "2025-12-01",
        "ex_dividend_date": "2025-11-15",
        "percent_insiders": 4.2,
        "percent_institutions": 65.3,
        "analyst_target_price": 250.0,
        "analyst_rating_strong_buy": 25,
        "analyst_rating_buy": 30,
        "analyst_rating_hold": 8,
        "analyst_rating_sell": 1,
        "analyst_rating_strong_sell": 0,
    }
    base.update(overrides)
    return base


class TestSummarizeCompanyProfile:
    def test_empty_doc_returns_empty(self):
        assert summarize_company_profile(None) == {}
        assert summarize_company_profile({}) == {}

    def test_top_level_keys(self):
        result = summarize_company_profile(_sample_doc())
        assert set(result.keys()) == {
            "identity",
            "size",
            "valuation",
            "profitability",
            "earnings",
            "growth",
            "risk",
            "dividend",
            "ownership",
            "analyst",
        }

    def test_noise_fields_dropped(self):
        result = summarize_company_profile(_sample_doc())
        flat_str = str(result)
        assert "description" not in flat_str
        assert "address" not in flat_str
        assert "cik" not in flat_str
        assert "official_site" not in flat_str
        assert "asset_type" not in flat_str
        assert "fiscal_year_end" not in flat_str
        assert "latest_quarter" not in flat_str
        assert "dividend_date" not in flat_str
        assert "ex_dividend_date" not in flat_str

    def test_identity_block(self):
        result = summarize_company_profile(_sample_doc())
        assert result["identity"] == {
            "ticker": "NVDA",
            "name": "NVIDIA Corp",
            "sector": "Technology",
            "industry": "Semiconductors",
            "country": "USA",
            "exchange": "NASDAQ",
            "currency": "USD",
        }

    def test_valuation_pe_prefers_trailing_pe(self):
        doc = _sample_doc(pe_ratio=10.0, trailing_pe=20.0)
        result = summarize_company_profile(doc)
        assert result["valuation"]["pe"] == 20.0

    def test_valuation_falls_back_to_pe_ratio(self):
        doc = _sample_doc()
        del doc["trailing_pe"]
        result = summarize_company_profile(doc)
        assert result["valuation"]["pe"] == 36.48

    def test_dividend_payout_ratio_computed(self):
        doc = _sample_doc(dividend_per_share=2.0, eps=10.0)
        result = summarize_company_profile(doc)
        assert result["dividend"]["payout_ratio"] == 20.0

    def test_dividend_payout_ratio_none_when_no_eps(self):
        doc = _sample_doc(dividend_per_share=2.0, eps=None)
        result = summarize_company_profile(doc)
        assert result["dividend"]["payout_ratio"] is None

    def test_dividend_payout_ratio_none_when_eps_zero(self):
        doc = _sample_doc(dividend_per_share=2.0, eps=0)
        result = summarize_company_profile(doc)
        assert result["dividend"]["payout_ratio"] is None

    def test_analyst_consensus_bullish(self):
        result = summarize_company_profile(_sample_doc())
        assert result["analyst"]["bullish_count"] == 55
        assert result["analyst"]["bearish_count"] == 1
        assert result["analyst"]["hold_count"] == 8
        assert result["analyst"]["total"] == 64
        assert result["analyst"]["consensus"] == "BULLISH"

    def test_analyst_target_price_passed_through(self):
        result = summarize_company_profile(_sample_doc())
        assert result["analyst"]["target_price"] == 250.0

    def test_missing_optional_fields_become_none(self):
        doc = {"key_ticker": "XYZ", "name": "XYZ Corp"}
        result = summarize_company_profile(doc)
        assert result["valuation"]["pe"] is None
        assert result["profitability"]["roe"] is None
        assert result["risk"]["beta"] is None

    def test_analyst_with_no_ratings(self):
        doc = {"key_ticker": "XYZ"}
        result = summarize_company_profile(doc)
        assert result["analyst"]["consensus"] == "NO_COVERAGE"
        assert result["analyst"]["total"] == 0


class TestConsensus:
    def test_bullish_when_buys_dominate(self):
        assert _consensus(bullish=30, hold=5, bearish=2) == "BULLISH"

    def test_bearish_when_sells_dominate(self):
        assert _consensus(bullish=2, hold=5, bearish=30) == "BEARISH"

    def test_hold_when_balanced(self):
        assert _consensus(bullish=10, hold=15, bearish=8) == "HOLD"

    def test_hold_when_holds_dominate(self):
        assert _consensus(bullish=10, hold=30, bearish=2) == "HOLD"

    def test_no_coverage(self):
        assert _consensus(bullish=0, hold=0, bearish=0) == "NO_COVERAGE"


class TestAsInt:
    def test_none_to_zero(self):
        assert _as_int(None) == 0

    def test_int_passthrough(self):
        assert _as_int(5) == 5

    def test_str_to_int(self):
        assert _as_int("3") == 3

    def test_invalid_string_to_zero(self):
        assert _as_int("abc") == 0

    def test_float_to_int(self):
        assert _as_int(3.7) == 3
