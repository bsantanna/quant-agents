import numpy as np
import pandas as pd


def get_sma(df: pd.DataFrame, short_window: int = 10, long_window: int = 20) -> pd.DataFrame:
    df_sma = df.copy()
    df_sma['sma_short'] = df_sma['val_close'].rolling(window=short_window).mean()
    df_sma['sma_long'] = df_sma['val_close'].rolling(window=long_window).mean()
    df_sma['position'] = np.where(df_sma['sma_short'] > df_sma['sma_long'], 1, -1)
    df_sma['returns'] = np.log(df_sma['val_close'] / df_sma['val_close'].shift(1))
    df_sma['strategy'] = df_sma['position'].shift(1) * df_sma['returns']
    df_sma.dropna(inplace=True)
    return df_sma


