from __future__ import annotations

from datetime import date
from statistics import mean, median, pstdev
from typing import Callable, Optional

_RSI_OVERBOUGHT = 70
_RSI_BULLISH_LOW = 50
_RSI_OVERSOLD = 30

_ADX_STRONG = 40
_ADX_TRENDING = 25
_ADX_WEAK = 20

_SLOPE_WINDOW = 20
_MOMENTUM_WINDOW = 5

_DIRECTION_EPSILON = 0.05
_MOMENTUM_EPSILON = 0.01
_ADX_TREND_EPSILON = 0.1


def summarize_technical_indicators(
    rsi: Optional[list[dict]],
    macd: Optional[list[dict]],
    ema: Optional[list[dict]],
    adx: Optional[list[dict]],
) -> dict:
    """Reduce raw indicator time-series into a quant-style summary.

    Each input is the raw output from MarketsStatsService.get_indicator_*:
    a list of daily entries. The output collapses each series into a compact
    dict (latest snapshot, window stats, slope, recent events, regime label)
    suitable for LLM consumption.
    """
    return {
        "rsi": _summarize_rsi(rsi or []),
        "macd": _summarize_macd(macd or []),
        "ema": _summarize_ema(ema or []),
        "adx": _summarize_adx(adx or []),
    }


def _empty_summary() -> dict:
    return {"latest": None, "stats": None, "trend": None, "recent_events": None}


def _summarize_rsi(series: list[dict]) -> dict:
    valid = [e for e in series if e.get("rsi") is not None]
    if not valid:
        return _empty_summary()

    last = valid[-1]
    values = [e["rsi"] for e in valid]
    regimes = [_rsi_regime(v) for v in values]
    window = values[-_SLOPE_WINDOW:]

    return {
        "latest": {
            "date": last["date"],
            "value": round(last["rsi"], 2),
            "regime": regimes[-1],
        },
        "stats": _basic_stats(values, target=last["rsi"]),
        "trend": {
            "slope_20d": _slope(window),
            "direction": _direction(window),
        },
        "recent_events": {
            "last_overbought_date": _last_date_where(
                valid, lambda r: r["rsi"] > _RSI_OVERBOUGHT
            ),
            "last_oversold_date": _last_date_where(
                valid, lambda r: r["rsi"] < _RSI_OVERSOLD
            ),
            "days_in_current_regime": _streak(regimes),
        },
    }


def _summarize_macd(series: list[dict]) -> dict:
    valid = [
        e
        for e in series
        if e.get("macd") is not None and e.get("signal") is not None
    ]
    if not valid:
        return _empty_summary()

    last = valid[-1]
    hist_values = [e["histogram"] for e in valid if e.get("histogram") is not None]
    regime = "BULLISH" if last["macd"] > last["signal"] else "BEARISH"

    bullish_cross, bearish_cross = _last_crossovers(
        valid, lambda r: r["macd"] - r["signal"]
    )
    days_since = _days_since(last["date"], bullish_cross, bearish_cross)

    return {
        "latest": {
            "date": last["date"],
            "macd": last["macd"],
            "signal": last["signal"],
            "histogram": last.get("histogram"),
            "regime": regime,
        },
        "stats": {
            "histogram_mean": _round(mean(hist_values)) if hist_values else None,
            "histogram_std": _round(pstdev(hist_values)) if len(hist_values) > 1 else 0.0,
            "histogram_min": _round(min(hist_values)) if hist_values else None,
            "histogram_max": _round(max(hist_values)) if hist_values else None,
        },
        "trend": {
            "histogram_slope_20d": _slope(hist_values[-_SLOPE_WINDOW:]),
            "momentum": _macd_momentum(hist_values),
        },
        "recent_events": {
            "last_bullish_cross_date": bullish_cross,
            "last_bearish_cross_date": bearish_cross,
            "days_since_last_cross": days_since,
        },
    }


def _summarize_ema(series: list[dict]) -> dict:
    valid = [
        e
        for e in series
        if e.get("ema_short") is not None and e.get("ema_long") is not None
    ]
    if not valid:
        return _empty_summary()

    last = valid[-1]
    gaps = [e["ema_short"] - e["ema_long"] for e in valid]
    last_gap = gaps[-1]
    last_long = last["ema_long"]

    bullish_cross, bearish_cross = _last_crossovers(
        valid, lambda r: r["ema_short"] - r["ema_long"]
    )
    days_since = _days_since(last["date"], bullish_cross, bearish_cross)

    return {
        "latest": {
            "date": last["date"],
            "ema_short": last["ema_short"],
            "ema_long": last["ema_long"],
            "gap": _round(last_gap),
            "gap_pct": _round(last_gap / last_long * 100) if last_long else 0.0,
            "regime": "BULLISH" if last_gap > 0 else "BEARISH",
        },
        "stats": {
            "gap_mean": _round(mean(gaps)),
            "gap_std": _round(pstdev(gaps)) if len(gaps) > 1 else 0.0,
        },
        "trend": None,
        "recent_events": {
            "last_bullish_cross_date": bullish_cross,
            "last_bearish_cross_date": bearish_cross,
            "days_since_last_cross": days_since,
        },
    }


def _summarize_adx(series: list[dict]) -> dict:
    valid = [e for e in series if e.get("adx") is not None]
    if not valid:
        return _empty_summary()

    last = valid[-1]
    adx_values = [e["adx"] for e in valid]
    last_plus = last.get("plus_di") or 0
    last_minus = last.get("minus_di") or 0
    window = adx_values[-_SLOPE_WINDOW:]

    return {
        "latest": {
            "date": last["date"],
            "adx": last["adx"],
            "plus_di": last.get("plus_di"),
            "minus_di": last.get("minus_di"),
            "regime": _adx_regime(last["adx"]),
            "direction": "BULLISH" if last_plus > last_minus else "BEARISH",
        },
        "stats": {
            "adx_mean": _round(mean(adx_values)),
            "adx_max": _round(max(adx_values)),
            "pct_time_trending": round(
                100 * sum(1 for v in adx_values if v > _ADX_TRENDING) / len(adx_values),
                1,
            ),
        },
        "trend": {
            "adx_slope_20d": _slope(window),
            "trend_strength_change": _trend_strength_change(window),
        },
        "recent_events": None,
    }


def _basic_stats(values: list[float], target: float) -> dict:
    return {
        "mean": _round(mean(values)),
        "median": _round(median(values)),
        "std": _round(pstdev(values)) if len(values) > 1 else 0.0,
        "min": _round(min(values)),
        "max": _round(max(values)),
        "percentile_rank": _percentile_rank(values, target),
    }


def _rsi_regime(v: float) -> str:
    if v > _RSI_OVERBOUGHT:
        return "OVERBOUGHT"
    if v >= _RSI_BULLISH_LOW:
        return "BULLISH"
    if v >= _RSI_OVERSOLD:
        return "BEARISH"
    return "OVERSOLD"


def _adx_regime(v: float) -> str:
    if v > _ADX_STRONG:
        return "STRONG_TREND"
    if v > _ADX_TRENDING:
        return "TRENDING"
    if v > _ADX_WEAK:
        return "WEAK_TREND"
    return "RANGING"


def _slope(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    sx = sum(xs)
    sy = sum(values)
    sxy = sum(x * y for x, y in zip(xs, values))
    sxx = sum(x * x for x in xs)
    denom = n * sxx - sx * sx
    if denom == 0:
        return 0.0
    return _round((n * sxy - sx * sy) / denom, ndigits=4)


def _direction(values: list[float]) -> str:
    s = _slope(values)
    if s > _DIRECTION_EPSILON:
        return "RISING"
    if s < -_DIRECTION_EPSILON:
        return "FALLING"
    return "FLAT"


def _percentile_rank(values: list[float], target: float) -> int:
    n = len(values)
    if n == 0:
        return 0
    below = sum(1 for v in values if v < target)
    equal = sum(1 for v in values if v == target)
    return round(100 * (below + 0.5 * equal) / n)


def _last_date_where(
    rows: list[dict], predicate: Callable[[dict], bool]
) -> Optional[str]:
    for r in reversed(rows):
        if predicate(r):
            return r["date"]
    return None


def _streak(labels: list[str]) -> int:
    if not labels:
        return 0
    last = labels[-1]
    count = 0
    for label in reversed(labels):
        if label != last:
            break
        count += 1
    return count


def _last_crossovers(
    rows: list[dict], diff_fn: Callable[[dict], float]
) -> tuple[Optional[str], Optional[str]]:
    last_bull = None
    last_bear = None
    prev = None
    for r in rows:
        cur = diff_fn(r)
        if prev is not None:
            if prev < 0 <= cur:
                last_bull = r["date"]
            elif prev >= 0 > cur:
                last_bear = r["date"]
        prev = cur
    return last_bull, last_bear


def _days_since(latest_date: str, *event_dates: Optional[str]) -> Optional[int]:
    candidates = [d for d in event_dates if d is not None]
    if not candidates:
        return None
    latest = date.fromisoformat(latest_date)
    most_recent = max(date.fromisoformat(d) for d in candidates)
    return (latest - most_recent).days


def _macd_momentum(hist_values: list[float]) -> str:
    if len(hist_values) < 2:
        return "FLAT"
    tail = hist_values[-min(_MOMENTUM_WINDOW, len(hist_values)) :]
    s = _slope(tail)
    if abs(s) < _MOMENTUM_EPSILON:
        return "FLAT"
    last_sign = 1 if hist_values[-1] >= 0 else -1
    return "STRENGTHENING" if last_sign * s > 0 else "FADING"


def _trend_strength_change(adx_window: list[float]) -> str:
    if len(adx_window) < 2:
        return "FLAT"
    s = _slope(adx_window)
    if s > _ADX_TREND_EPSILON:
        return "STRENGTHENING"
    if s < -_ADX_TREND_EPSILON:
        return "WEAKENING"
    return "FLAT"


def _round(value: float, ndigits: int = 2) -> float:
    return round(value, ndigits)
