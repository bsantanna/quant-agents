import numpy as np
import pandas as pd


def get_crossovers(
        df: pd.DataFrame
) -> pd.DataFrame:
    df_crossovers = df.copy()
    df_crossovers['prev_position'] = df_crossovers['position'].shift(1)
    df_crossovers = df_crossovers[df_crossovers['position'] != df_crossovers['prev_position']]
    df_crossovers.dropna(inplace=True)
    return df_crossovers


def get_sma(
        df: pd.DataFrame,
        short_window: int = 10,
        long_window: int = 20
) -> (pd.DataFrame, pd.DataFrame):
    df_sma = df.copy()
    df_sma['sma_short'] = df_sma['val_close'].rolling(window=short_window).mean()
    df_sma['sma_long'] = df_sma['val_close'].rolling(window=long_window).mean()
    df_sma['position'] = np.where(df_sma['sma_short'] > df_sma['sma_long'], 1, -1)
    df_sma['returns'] = np.log(df_sma['val_close'] / df_sma['val_close'].shift(1))
    df_sma['strategy'] = df_sma['position'].shift(1) * df_sma['returns']
    df_sma.dropna(inplace=True)
    return df_sma, get_crossovers(df_sma)


def get_ema(
        df: pd.DataFrame,
        short_window: int = 10,
        long_window: int = 20
) -> (pd.DataFrame, pd.DataFrame):
    df_ema = df.copy()
    df_ema['ema_short'] = df_ema['val_close'].ewm(span=short_window, adjust=False).mean()
    df_ema['ema_long'] = df_ema['val_close'].ewm(span=long_window, adjust=False).mean()
    df_ema['position'] = np.where(df_ema['ema_short'] > df_ema['ema_long'], 1, -1)
    df_ema['returns'] = np.log(df_ema['val_close'] / df_ema['val_close'].shift(1))
    df_ema['strategy'] = df_ema['position'].shift(1) * df_ema['returns']
    df_ema.dropna(inplace=True)
    return df_ema, get_crossovers(df_ema)


def get_stoch(
        df: pd.DataFrame,
        lookback: int = 10,
        smooth_k: int = 10,
        smooth_d: int = 10
) -> (pd.DataFrame, pd.DataFrame):
    # Reference https://www.fmlabs.com/reference/default.htm?url=StochasticOscillator.htm
    df_stoch = df.copy()
    lowest_low = df_stoch['val_low'].rolling(window=lookback).min()
    highest_high = df_stoch['val_high'].rolling(window=lookback).max()
    raw_k = 100 * (df_stoch['val_close'] - lowest_low) / (highest_high - lowest_low)
    slow_k = raw_k.rolling(window=smooth_k).mean()
    slow_d = slow_k.rolling(window=smooth_d).mean()
    df_stoch['slow_k'] = slow_k
    df_stoch['slow_d'] = slow_d
    df_stoch['position'] = np.where(df_stoch['slow_k'] > df_stoch['slow_d'], 1, -1)
    df_stoch['returns'] = np.log(df_stoch['val_close'] / df_stoch['val_close'].shift(1))
    df_stoch['strategy'] = df_stoch['position'].shift(1) * df_stoch['returns']
    df_stoch.dropna(inplace=True)
    return df_stoch, get_crossovers(df_stoch)


def get_rsi(
        df: pd.DataFrame,
        period: int = 7,
) -> (pd.DataFrame, pd.DataFrame):
    # Reference: https://www.fmlabs.com/reference/default.htm?url=RSI.htm
    df_rsi = df.copy()
    delta = df_rsi['val_close'].diff()
    up = delta.clip(lower=0)
    dn = -delta.clip(upper=0)
    upavg = up.ewm(com=period - 1, adjust=False).mean()
    dnavg = dn.ewm(com=period - 1, adjust=False).mean()
    rs = upavg / dnavg
    df_rsi['rsi'] = 100 - 100 / (1 + rs)
    df_rsi['position'] = np.where(df_rsi['rsi'] < 30, 1, np.where(df_rsi['rsi'] > 70, -1, 1))
    df_rsi['returns'] = np.log(df_rsi['val_close'] / df_rsi['val_close'].shift(1))
    df_rsi['strategy'] = df_rsi['position'].shift(1) * df_rsi['returns']
    df_rsi.dropna(inplace=True)
    return df_rsi, get_crossovers(df_rsi)


def get_adx(
        df: pd.DataFrame,
        period: int = 14,
) -> (pd.DataFrame, pd.DataFrame):
    # Reference: https://www.fmlabs.com/reference/default.htm?url=ADX.htm
    # Calculate +DM, -DM, and TR
    df_adx = df.copy()
    df_adx['prev_high'] = df_adx['val_high'].shift(1)
    df_adx['prev_low'] = df_adx['val_low'].shift(1)
    df_adx['prev_close'] = df_adx['val_close'].shift(1)

    df_adx['plus_dm'] = np.where(
        (df_adx['val_high'] - df_adx['prev_high']) > (df_adx['prev_low'] - df_adx['val_low']),
        df_adx['val_high'] - df_adx['prev_high'], 0
    )

    df_adx['plus_dm'] = np.where(df_adx['plus_dm'] > 0, df_adx['plus_dm'], 0)  # Ensure non-negative

    df_adx['minus_dm'] = np.where(
        (df_adx['prev_low'] - df_adx['val_low']) > (df_adx['val_high'] - df_adx['prev_high']),
        df_adx['prev_low'] - df_adx['val_low'], 0
    )

    df_adx['minus_dm'] = np.where(df_adx['minus_dm'] > 0, df_adx['minus_dm'], 0)  # Ensure non-negative

    df_adx['tr'] = np.maximum(
        df_adx['val_high'] - df_adx['val_low'],
        np.maximum(abs(df_adx['val_high'] - df_adx['prev_close']),
                   abs(df_adx['val_low'] - df_adx['prev_close']))
    )

    df_adx.dropna(inplace=True)

    # Smooth using Wilder's method (ewm equivalent)
    plus_dm_smooth = df_adx['plus_dm'].ewm(com=period - 1, adjust=False).mean()
    minus_dm_smooth = df_adx['minus_dm'].ewm(com=period - 1, adjust=False).mean()
    tr_smooth = df_adx['tr'].ewm(com=period - 1, adjust=False).mean()

    # Calculate +DI and -DI
    df_adx['plus_di'] = 100 * (plus_dm_smooth / tr_smooth)
    df_adx['minus_di'] = 100 * (minus_dm_smooth / tr_smooth)

    # Calculate DX
    dx = 100 * abs(df_adx['plus_di'] - df_adx['minus_di']) / (df_adx['plus_di'] + df_adx['minus_di'])

    # Calculate ADX (smooth DX)
    df_adx['adx'] = dx.ewm(com=period - 1, adjust=False).mean()

    df_adx['position'] = np.where(
        (df_adx['adx'] > 25) & (df_adx['plus_di'] > df_adx['minus_di']), 1,
        np.where((df_adx['adx'] > 25) & (df_adx['minus_di'] > df_adx['plus_di']), -1, 1)
    )

    df_adx['returns'] = np.log(df_adx['val_close'] / df_adx['val_close'].shift(1))
    df_adx['strategy'] = df_adx['position'].shift(1) * df_adx['returns']
    return df_adx, get_crossovers(df_adx)


def get_cci(
        df: pd.DataFrame,
        period: int = 14,
        constant: float = 0.015
) -> (pd.DataFrame, pd.DataFrame):
    # Reference: https://www.fmlabs.com/reference/default.htm?url=CCI.htm
    df_cci = df.copy()

    # Calculate Typical Price (TP)
    df_cci['tp'] = (df_cci['val_high'] + df_cci['val_low'] + df_cci['val_close']) / 3

    # Calculate ATP (Simple Moving Average of TP)
    df_cci['atp'] = df_cci['tp'].rolling(window=period).mean()

    # Calculate Mean Deviation (MD)
    df_cci['dev'] = abs(df_cci['tp'] - df_cci['atp'])
    df_cci['md'] = df_cci['dev'].rolling(window=period).mean()

    # Calculate CCI
    df_cci['cci'] = (df_cci['tp'] - df_cci['atp']) / (constant * df_cci['md'])
    df_cci['position'] = np.where(df_cci['cci'] < -100, 1, np.where(df_cci['cci'] > 100, -1, 1))
    df_cci['returns'] = np.log(df_cci['val_close'] / df_cci['val_close'].shift(1))
    df_cci['strategy'] = df_cci['position'].shift(1) * df_cci['returns']
    df_cci.dropna(inplace=True)
    return df_cci, get_crossovers(df_cci)


def get_aroon(
        df: pd.DataFrame,
        period: int = 14,
) -> (pd.DataFrame, pd.DataFrame):
    # Reference https://www.fmlabs.com/reference/default.htm?url=Aroon.htm
    df_aroon = df.copy()
    # Calculate Periods Since Highest High
    df_aroon['periods_since_hh'] = df_aroon['val_high'].rolling(window=period).apply(
        lambda x: len(x) - 1 - np.argmax(x), raw=True
    )

    # Calculate Periods Since Lowest Low
    df_aroon['periods_since_ll'] = df_aroon['val_low'].rolling(window=period).apply(lambda x: len(x) - 1 - np.argmin(x),
                                                                                    raw=True)
    # Calculate Aroon Up and Aroon Down
    df_aroon['aroon_up'] = 100 * (period - df_aroon['periods_since_hh']) / period
    df_aroon['aroon_down'] = 100 * (period - df_aroon['periods_since_ll']) / period
    df_aroon['position'] = np.where(
        (df_aroon['aroon_up'] > 70) & (df_aroon['aroon_down'] < 30), 1,
        np.where((df_aroon['aroon_down'] > 70) & (df_aroon['aroon_up'] < 30), -1, 1)
    )
    df_aroon['returns'] = np.log(df_aroon['val_close'] / df_aroon['val_close'].shift(1))
    df_aroon['strategy'] = df_aroon['position'].shift(1) * df_aroon['returns']
    df_aroon.dropna(inplace=True)
    return df_aroon, get_crossovers(df_aroon)


def get_bbands(
        df: pd.DataFrame,
        period: int = 14,
        std_dev: int = 2
) -> pd.DataFrame:
    # Reference: https://www.fmlabs.com/reference/default.htm?url=Bollinger.htm
    df_bbands = df.copy()
    # Calculate Typical Price (TP)
    df_bbands['tp'] = (df_bbands['val_high'] + df_bbands['val_low'] + df_bbands['val_close']) / 3

    # Calculate Middle Band (SMA of TP)
    df_bbands['middle_band'] = df_bbands['tp'].rolling(window=period).mean()

    # Calculate Standard Deviation of TP
    df_bbands['sd'] = df_bbands['tp'].rolling(window=period).std()

    # Calculate Upper and Lower Bands
    df_bbands['upper_band'] = df_bbands['middle_band'] + (std_dev * df_bbands['sd'])
    df_bbands['lower_band'] = df_bbands['middle_band'] - (std_dev * df_bbands['sd'])

    # Calculate Band Width (%)
    df_bbands['band_width'] = ((df_bbands['upper_band'] - df_bbands['lower_band']) / df_bbands['middle_band']) * 100
    df_bbands['prev_close'] = df_bbands['val_close'].shift(1)
    df_bbands['prev_middle'] = df_bbands['middle_band'].shift(1)
    df_bbands['position'] = 0
    # Bullish: Price was below lower, now crosses above middle
    df_bbands['position'] = np.where(
        (df_bbands['prev_close'] < df_bbands['lower_band']) &
        (df_bbands['prev_close'] < df_bbands['prev_middle']) &
        (df_bbands['val_close'] > df_bbands['middle_band']), 1, df_bbands['position']
    )
    # Bearish: Price was above upper, now crosses below middle
    df_bbands['position'] = np.where(
        (df_bbands['prev_close'] > df_bbands['upper_band']) &
        (df_bbands['prev_close'] > df_bbands['prev_middle']) &
        (df_bbands['val_close'] < df_bbands['middle_band']), -1, df_bbands['position']
    )
    df_bbands.dropna(inplace=True)

    return df_bbands


def get_ad(
        df: pd.DataFrame,
) -> (pd.DataFrame, pd.DataFrame):
    # Reference: https://www.fmlabs.com/reference/default.htm?url=AccumDist.htm
    df_ad = df.copy()
    # Calculate Close Location Value (CLV)
    df_ad['clv'] = ((df_ad['val_close'] - df_ad['val_low']) - (df_ad['val_high'] - df_ad['val_close'])) / (
            df_ad['val_high'] - df_ad['val_low'])

    # Handle division by zero or NaN (if high == low)
    df_ad['clv'] = df_ad['clv'].fillna(0)

    # Calculate daily A/D contribution (CLV * volume)
    df_ad['ad_contrib'] = df_ad['clv'] * df_ad['val_volume']

    # Calculate Accumulation/Distribution Line (cumulative sum)
    df_ad['ad_line'] = df_ad['ad_contrib'].cumsum()
    df_ad['ad_change'] = df_ad['ad_line'].diff()
    df_ad['position'] = np.where(df_ad['ad_change'] > 0, 1, np.where(df_ad['ad_change'] < 0, -1, 0))
    df_ad['returns'] = np.log(df_ad['val_close'] / df_ad['val_close'].shift(1))
    df_ad['strategy'] = df_ad['position'].shift(1) * df_ad['returns']
    # Drop NaN rows (if any from initial data)
    df_ad.dropna(inplace=True)
    return df_ad, get_crossovers(df_ad)


def get_obv(
        df: pd.DataFrame,
) -> (pd.DataFrame, pd.DataFrame):
    # Reference https://www.fmlabs.com/reference/default.htm?url=OBV.htm
    df_obv = df.copy()

    # Calculate daily close change
    df_obv['prev_close'] = df_obv['val_close'].shift(1)
    df_obv['close_change'] = df_obv['val_close'] - df_obv['prev_close']

    # Calculate signed volume: +volume if up, -volume if down, 0 if flat
    df_obv['signed_volume'] = np.where(
        df_obv['close_change'] > 0, df_obv['val_volume'],
        np.where(df_obv['close_change'] < 0, -df_obv['val_volume'], 0)
    )

    # Calculate OBV (cumulative sum of signed volume)
    df_obv['obv'] = df_obv['signed_volume'].cumsum()

    # Generate positions for the strategy (1 for up OBV, -1 for down, 0 flat)
    df_obv['obv_change'] = df_obv['obv'].diff()
    df_obv['position'] = np.where(df_obv['obv_change'] > 0, 1, np.where(df_obv['obv_change'] < 0, -1, 0))
    df_obv['returns'] = np.log(df_obv['val_close'] / df_obv['val_close'].shift(1))
    df_obv['strategy'] = df_obv['position'].shift(1) * df_obv['returns']
    # Drop NaN rows (initial prev_close is NaN)
    df_obv.dropna(inplace=True)

    return df_obv, get_crossovers(df_obv)


def get_macd(
        df: pd.DataFrame,
        short_period=7,
        long_period=20,
        signal_period=6
) -> (pd.DataFrame, pd.DataFrame):
    # Reference: https://www.fmlabs.com/reference/default.htm?url=MACD.htm
    df_macd = df.copy()

    # Calculate Short EMA (12-period)
    df_macd['short_ema'] = df_macd['val_close'].ewm(span=short_period, adjust=False).mean()

    # Calculate Long EMA (26-period)
    df_macd['long_ema'] = df_macd['val_close'].ewm(span=long_period, adjust=False).mean()

    # Calculate MACD Line
    df_macd['macd'] = df_macd['short_ema'] - df_macd['long_ema']

    # Calculate Signal Line (9-period EMA of MACD)
    df_macd['signal'] = df_macd['macd'].ewm(span=signal_period, adjust=False).mean()

    # Calculate Histogram
    df_macd['histogram'] = df_macd['macd'] - df_macd['signal']

    df_macd['prev_macd'] = df_macd['macd'].shift(1)
    df_macd['prev_signal'] = df_macd['signal'].shift(1)
    df_macd['position'] = np.where(
        (df_macd['prev_macd'] < df_macd['prev_signal']) & (df_macd['macd'] > df_macd['signal']), 1,
        np.where((df_macd['prev_macd'] > df_macd['prev_signal']) & (df_macd['macd'] < df_macd['signal']), -1, 1))
    df_macd['returns'] = np.log(df_macd['val_close'] / df_macd['val_close'].shift(1))
    df_macd['strategy'] = df_macd['position'].shift(1) * df_macd['returns']

    # Drop NaN rows (due to ewm)
    df_macd.dropna(inplace=True)
    return df_macd, get_crossovers(df_macd)
