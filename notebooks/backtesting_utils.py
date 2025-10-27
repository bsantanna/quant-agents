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
