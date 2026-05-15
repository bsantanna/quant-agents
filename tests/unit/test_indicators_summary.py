from app.services.agent_types.quaks.insights.financial_analyst.v1.indicators_summary import (
    _adx_regime,
    _direction,
    _last_crossovers,
    _last_date_where,
    _macd_momentum,
    _percentile_rank,
    _rsi_regime,
    _slope,
    _streak,
    _trend_strength_change,
    summarize_technical_indicators,
)


def _date(i: int) -> str:
    day = (i % 28) + 1
    month = (i // 28) % 12 + 1
    return f"2025-{month:02d}-{day:02d}"


def _build_rsi_series(values):
    return [{"date": _date(i), "rsi": v, "position": 1} for i, v in enumerate(values)]


def _build_macd_series(macds, signals, histograms=None):
    histograms = histograms if histograms is not None else [m - s for m, s in zip(macds, signals)]
    return [
        {
            "date": _date(i),
            "macd": m,
            "signal": s,
            "histogram": h,
            "short_ema": 0.0,
            "long_ema": 0.0,
            "position": 1,
        }
        for i, (m, s, h) in enumerate(zip(macds, signals, histograms))
    ]


def _build_ema_series(shorts, longs):
    return [
        {"date": _date(i), "ema_short": sh, "ema_long": ln, "position": 1}
        for i, (sh, ln) in enumerate(zip(shorts, longs))
    ]


def _build_adx_series(adxs, pluses=None, minuses=None):
    pluses = pluses if pluses is not None else [20.0] * len(adxs)
    minuses = minuses if minuses is not None else [15.0] * len(adxs)
    return [
        {
            "date": _date(i),
            "adx": a,
            "plus_di": p,
            "minus_di": m,
            "position": 1,
        }
        for i, (a, p, m) in enumerate(zip(adxs, pluses, minuses))
    ]


class TestPureHelpers:
    def test_rsi_regime_boundaries(self):
        assert _rsi_regime(71) == "OVERBOUGHT"
        assert _rsi_regime(70) == "BULLISH"
        assert _rsi_regime(50) == "BULLISH"
        assert _rsi_regime(49.9) == "BEARISH"
        assert _rsi_regime(30) == "BEARISH"
        assert _rsi_regime(29.9) == "OVERSOLD"

    def test_adx_regime_boundaries(self):
        assert _adx_regime(41) == "STRONG_TREND"
        assert _adx_regime(40) == "TRENDING"
        assert _adx_regime(26) == "TRENDING"
        assert _adx_regime(25) == "WEAK_TREND"
        assert _adx_regime(21) == "WEAK_TREND"
        assert _adx_regime(20) == "RANGING"

    def test_slope_rising(self):
        assert _slope([1.0, 2.0, 3.0, 4.0]) == 1.0

    def test_slope_falling(self):
        assert _slope([4.0, 3.0, 2.0, 1.0]) == -1.0

    def test_slope_flat(self):
        assert _slope([5.0, 5.0, 5.0]) == 0.0

    def test_slope_single_point_returns_zero(self):
        assert _slope([5.0]) == 0.0

    def test_slope_empty_returns_zero(self):
        assert _slope([]) == 0.0

    def test_direction(self):
        assert _direction([1.0, 2.0, 3.0]) == "RISING"
        assert _direction([3.0, 2.0, 1.0]) == "FALLING"
        assert _direction([5.0, 5.0, 5.0]) == "FLAT"

    def test_percentile_rank_median(self):
        assert _percentile_rank([1.0, 2.0, 3.0, 4.0, 5.0], 3.0) == 50

    def test_percentile_rank_top(self):
        assert _percentile_rank([1.0, 2.0, 3.0, 4.0, 5.0], 5.0) == 90

    def test_percentile_rank_bottom(self):
        assert _percentile_rank([1.0, 2.0, 3.0, 4.0, 5.0], 1.0) == 10

    def test_percentile_rank_empty(self):
        assert _percentile_rank([], 1.0) == 0

    def test_streak_basic(self):
        assert _streak(["A", "A", "B", "B", "B"]) == 3

    def test_streak_single(self):
        assert _streak(["A"]) == 1

    def test_streak_empty(self):
        assert _streak([]) == 0

    def test_streak_all_same(self):
        assert _streak(["X", "X", "X"]) == 3

    def test_last_date_where_finds_recent(self):
        rows = [
            {"date": "2025-01-01", "v": 10},
            {"date": "2025-01-02", "v": 50},
            {"date": "2025-01-03", "v": 5},
        ]
        assert _last_date_where(rows, lambda r: r["v"] > 30) == "2025-01-02"

    def test_last_date_where_no_match(self):
        rows = [{"date": "2025-01-01", "v": 1}]
        assert _last_date_where(rows, lambda r: r["v"] > 30) is None

    def test_last_crossovers_bullish_then_bearish(self):
        rows = [
            {"date": "2025-01-01", "d": -1},
            {"date": "2025-01-02", "d": 1},  # bullish cross
            {"date": "2025-01-03", "d": 2},
            {"date": "2025-01-04", "d": -1},  # bearish cross
        ]
        bull, bear = _last_crossovers(rows, lambda r: r["d"])
        assert bull == "2025-01-02"
        assert bear == "2025-01-04"

    def test_last_crossovers_no_cross(self):
        rows = [{"date": "2025-01-01", "d": 1}, {"date": "2025-01-02", "d": 2}]
        bull, bear = _last_crossovers(rows, lambda r: r["d"])
        assert bull is None
        assert bear is None

    def test_macd_momentum_strengthening_positive(self):
        assert _macd_momentum([0.1, 0.2, 0.3, 0.4, 0.5]) == "STRENGTHENING"

    def test_macd_momentum_fading_positive(self):
        assert _macd_momentum([0.5, 0.4, 0.3, 0.2, 0.1]) == "FADING"

    def test_macd_momentum_strengthening_negative(self):
        assert _macd_momentum([-0.1, -0.2, -0.3, -0.4, -0.5]) == "STRENGTHENING"

    def test_macd_momentum_fading_negative(self):
        assert _macd_momentum([-0.5, -0.4, -0.3, -0.2, -0.1]) == "FADING"

    def test_macd_momentum_flat(self):
        assert _macd_momentum([0.1, 0.1, 0.1, 0.1, 0.1]) == "FLAT"

    def test_trend_strength_change(self):
        assert _trend_strength_change([20.0, 22.0, 24.0, 26.0, 28.0]) == "STRENGTHENING"
        assert _trend_strength_change([28.0, 26.0, 24.0, 22.0, 20.0]) == "WEAKENING"
        assert _trend_strength_change([25.0, 25.0, 25.0]) == "FLAT"


class TestSummarizeRsi:
    def test_empty_returns_empty_summary(self):
        result = summarize_technical_indicators([], [], [], [])
        assert result["rsi"]["latest"] is None
        assert result["rsi"]["stats"] is None
        assert result["rsi"]["trend"] is None
        assert result["rsi"]["recent_events"] is None

    def test_all_null_returns_empty_summary(self):
        rsi = [{"date": "2025-01-01", "rsi": None, "position": None}]
        result = summarize_technical_indicators(rsi, [], [], [])
        assert result["rsi"]["latest"] is None

    def test_latest_snapshot(self):
        rsi = _build_rsi_series([45.0, 55.0, 65.0])
        result = summarize_technical_indicators(rsi, [], [], [])
        assert result["rsi"]["latest"]["value"] == 65.0
        assert result["rsi"]["latest"]["regime"] == "BULLISH"

    def test_overbought_regime(self):
        rsi = _build_rsi_series([72.0])
        result = summarize_technical_indicators(rsi, [], [], [])
        assert result["rsi"]["latest"]["regime"] == "OVERBOUGHT"

    def test_recent_events_overbought_date(self):
        rsi = _build_rsi_series([50.0, 75.0, 60.0, 55.0])
        result = summarize_technical_indicators(rsi, [], [], [])
        assert result["rsi"]["recent_events"]["last_overbought_date"] == _date(1)

    def test_recent_events_oversold_date(self):
        rsi = _build_rsi_series([50.0, 25.0, 35.0, 40.0])
        result = summarize_technical_indicators(rsi, [], [], [])
        assert result["rsi"]["recent_events"]["last_oversold_date"] == _date(1)

    def test_recent_events_no_extremes(self):
        rsi = _build_rsi_series([45.0, 55.0, 50.0])
        result = summarize_technical_indicators(rsi, [], [], [])
        assert result["rsi"]["recent_events"]["last_overbought_date"] is None
        assert result["rsi"]["recent_events"]["last_oversold_date"] is None

    def test_stats_percentile_rank(self):
        rsi = _build_rsi_series([10.0, 20.0, 30.0, 40.0, 50.0])
        result = summarize_technical_indicators(rsi, [], [], [])
        assert result["rsi"]["stats"]["percentile_rank"] == 90
        assert result["rsi"]["stats"]["min"] == 10.0
        assert result["rsi"]["stats"]["max"] == 50.0

    def test_days_in_current_regime(self):
        rsi = _build_rsi_series([45.0, 55.0, 60.0, 65.0])
        result = summarize_technical_indicators(rsi, [], [], [])
        assert result["rsi"]["recent_events"]["days_in_current_regime"] == 3


class TestSummarizeMacd:
    def test_empty(self):
        result = summarize_technical_indicators([], [], [], [])
        assert result["macd"]["latest"] is None

    def test_bullish_regime(self):
        macd = _build_macd_series([1.0, 2.0], [0.5, 1.0])
        result = summarize_technical_indicators([], macd, [], [])
        assert result["macd"]["latest"]["regime"] == "BULLISH"

    def test_bearish_regime(self):
        macd = _build_macd_series([1.0, 0.5], [2.0, 1.5])
        result = summarize_technical_indicators([], macd, [], [])
        assert result["macd"]["latest"]["regime"] == "BEARISH"

    def test_bullish_crossover_detected(self):
        macd = _build_macd_series([-1.0, -0.5, 0.3, 0.5], [0.0, 0.0, 0.0, 0.0])
        result = summarize_technical_indicators([], macd, [], [])
        assert result["macd"]["recent_events"]["last_bullish_cross_date"] == _date(2)

    def test_bearish_crossover_detected(self):
        macd = _build_macd_series([1.0, 0.5, -0.3, -0.5], [0.0, 0.0, 0.0, 0.0])
        result = summarize_technical_indicators([], macd, [], [])
        assert result["macd"]["recent_events"]["last_bearish_cross_date"] == _date(2)

    def test_no_crossover(self):
        macd = _build_macd_series([1.0, 1.2, 1.5], [0.0, 0.0, 0.0])
        result = summarize_technical_indicators([], macd, [], [])
        assert result["macd"]["recent_events"]["last_bullish_cross_date"] is None
        assert result["macd"]["recent_events"]["last_bearish_cross_date"] is None


class TestSummarizeEma:
    def test_empty(self):
        result = summarize_technical_indicators([], [], [], [])
        assert result["ema"]["latest"] is None

    def test_bullish_when_short_above_long(self):
        ema = _build_ema_series([110.0, 115.0], [105.0, 110.0])
        result = summarize_technical_indicators([], [], ema, [])
        assert result["ema"]["latest"]["regime"] == "BULLISH"
        assert result["ema"]["latest"]["gap"] == 5.0

    def test_bearish_when_short_below_long(self):
        ema = _build_ema_series([100.0, 95.0], [105.0, 100.0])
        result = summarize_technical_indicators([], [], ema, [])
        assert result["ema"]["latest"]["regime"] == "BEARISH"
        assert result["ema"]["latest"]["gap"] == -5.0

    def test_gap_pct_calculation(self):
        ema = _build_ema_series([110.0], [100.0])
        result = summarize_technical_indicators([], [], ema, [])
        assert result["ema"]["latest"]["gap_pct"] == 10.0

    def test_crossover_detection(self):
        ema = _build_ema_series([95.0, 98.0, 102.0, 105.0], [100.0, 100.0, 100.0, 100.0])
        result = summarize_technical_indicators([], [], ema, [])
        assert result["ema"]["recent_events"]["last_bullish_cross_date"] == _date(2)


class TestSummarizeAdx:
    def test_empty(self):
        result = summarize_technical_indicators([], [], [], [])
        assert result["adx"]["latest"] is None

    def test_trending_regime_with_bullish_direction(self):
        adx = _build_adx_series([30.0], pluses=[25.0], minuses=[15.0])
        result = summarize_technical_indicators([], [], [], adx)
        assert result["adx"]["latest"]["regime"] == "TRENDING"
        assert result["adx"]["latest"]["direction"] == "BULLISH"

    def test_ranging_regime(self):
        adx = _build_adx_series([15.0], pluses=[10.0], minuses=[12.0])
        result = summarize_technical_indicators([], [], [], adx)
        assert result["adx"]["latest"]["regime"] == "RANGING"
        assert result["adx"]["latest"]["direction"] == "BEARISH"

    def test_strong_trend(self):
        adx = _build_adx_series([45.0])
        result = summarize_technical_indicators([], [], [], adx)
        assert result["adx"]["latest"]["regime"] == "STRONG_TREND"

    def test_pct_time_trending(self):
        adx = _build_adx_series([10.0, 20.0, 30.0, 30.0])
        result = summarize_technical_indicators([], [], [], adx)
        assert result["adx"]["stats"]["pct_time_trending"] == 50.0


class TestNoneInputs:
    def test_all_none_inputs(self):
        result = summarize_technical_indicators(None, None, None, None)
        for key in ("rsi", "macd", "ema", "adx"):
            assert result[key]["latest"] is None


class TestFullPipelineShape:
    def test_keys_present(self):
        rsi = _build_rsi_series([50.0, 55.0])
        macd = _build_macd_series([1.0, 2.0], [0.5, 1.0])
        ema = _build_ema_series([110.0, 115.0], [105.0, 110.0])
        adx = _build_adx_series([25.0, 30.0])
        result = summarize_technical_indicators(rsi, macd, ema, adx)
        assert set(result.keys()) == {"rsi", "macd", "ema", "adx"}
        for key in result:
            assert set(result[key].keys()) >= {"latest", "stats"}
