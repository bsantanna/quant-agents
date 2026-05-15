from __future__ import annotations

from typing import Optional

_BULLISH_RATIO = 2.0
_BEARISH_RATIO = 2.0


def summarize_company_profile(doc: Optional[dict]) -> dict:
    """Reshape a raw metadata document into a compact, quant-oriented profile.

    Drops free-text and administrative fields that a quant analyst does not
    consume (description, address, cik, fiscal_year_end, etc.), collapses the
    five analyst rating fields into a single consensus block, and groups the
    remaining metrics by analytical category.
    """
    if not doc:
        return {}

    return {
        "identity": _identity(doc),
        "size": _size(doc),
        "valuation": _valuation(doc),
        "profitability": _profitability(doc),
        "earnings": _earnings(doc),
        "growth": _growth(doc),
        "risk": _risk(doc),
        "dividend": _dividend(doc),
        "ownership": _ownership(doc),
        "analyst": _analyst(doc),
    }


def _identity(doc: dict) -> dict:
    return {
        "ticker": doc.get("key_ticker"),
        "name": doc.get("name"),
        "sector": doc.get("sector"),
        "industry": doc.get("industry"),
        "country": doc.get("country"),
        "exchange": doc.get("exchange"),
        "currency": doc.get("currency"),
    }


def _size(doc: dict) -> dict:
    return {
        "market_cap_usd": doc.get("market_capitalization"),
        "shares_outstanding": doc.get("shares_outstanding"),
        "shares_float": doc.get("shares_float"),
    }


def _valuation(doc: dict) -> dict:
    return {
        "pe": doc.get("trailing_pe") or doc.get("pe_ratio"),
        "forward_pe": doc.get("forward_pe"),
        "peg": doc.get("peg_ratio"),
        "pb": doc.get("price_to_book_ratio"),
        "ps": doc.get("price_to_sales_ratio_ttm"),
        "ev_to_ebitda": doc.get("ev_to_ebitda"),
        "ev_to_revenue": doc.get("ev_to_revenue"),
        "book_value": doc.get("book_value"),
    }


def _profitability(doc: dict) -> dict:
    return {
        "profit_margin": doc.get("profit_margin"),
        "operating_margin": doc.get("operating_margin_ttm"),
        "roe": doc.get("return_on_equity_ttm"),
        "roa": doc.get("return_on_assets_ttm"),
    }


def _earnings(doc: dict) -> dict:
    return {
        "eps": doc.get("eps"),
        "diluted_eps_ttm": doc.get("diluted_eps_ttm"),
        "revenue_per_share": doc.get("revenue_per_share_ttm"),
        "revenue_ttm": doc.get("revenue_ttm"),
        "gross_profit_ttm": doc.get("gross_profit_ttm"),
        "ebitda": doc.get("ebitda"),
    }


def _growth(doc: dict) -> dict:
    return {
        "revenue_growth_yoy": doc.get("quarterly_revenue_growth_yoy"),
        "earnings_growth_yoy": doc.get("quarterly_earnings_growth_yoy"),
    }


def _risk(doc: dict) -> dict:
    return {
        "beta": doc.get("beta"),
        "week_52_high": doc.get("week_52_high"),
        "week_52_low": doc.get("week_52_low"),
        "ma_50d": doc.get("moving_average_50_day"),
        "ma_200d": doc.get("moving_average_200_day"),
    }


def _dividend(doc: dict) -> dict:
    per_share = doc.get("dividend_per_share")
    eps = doc.get("eps")
    payout = None
    if per_share is not None and eps is not None and eps > 0:
        payout = round(per_share / eps * 100, 2)
    return {
        "yield": doc.get("dividend_yield"),
        "per_share": per_share,
        "payout_ratio": payout,
    }


def _ownership(doc: dict) -> dict:
    return {
        "percent_insiders": doc.get("percent_insiders"),
        "percent_institutions": doc.get("percent_institutions"),
    }


def _analyst(doc: dict) -> dict:
    strong_buy = _as_int(doc.get("analyst_rating_strong_buy"))
    buy = _as_int(doc.get("analyst_rating_buy"))
    hold = _as_int(doc.get("analyst_rating_hold"))
    sell = _as_int(doc.get("analyst_rating_sell"))
    strong_sell = _as_int(doc.get("analyst_rating_strong_sell"))

    bullish = strong_buy + buy
    bearish = sell + strong_sell
    total = bullish + hold + bearish

    return {
        "target_price": doc.get("analyst_target_price"),
        "bullish_count": bullish,
        "hold_count": hold,
        "bearish_count": bearish,
        "total": total,
        "consensus": _consensus(bullish, hold, bearish),
    }


def _consensus(bullish: int, hold: int, bearish: int) -> str:
    if bullish + hold + bearish == 0:
        return "NO_COVERAGE"
    if bullish > _BULLISH_RATIO * bearish and bullish >= hold:
        return "BULLISH"
    if bearish > _BEARISH_RATIO * bullish and bearish >= hold:
        return "BEARISH"
    return "HOLD"


def _as_int(value) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
