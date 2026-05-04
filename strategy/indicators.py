"""
Technical indicators using TA-Lib
"""
import pandas as pd
import ta

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """EMA20, RSI14"""
    df['ema20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    return df
