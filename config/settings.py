"""
Config module - Centralized, env-driven settings
"""
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

load_dotenv()

@dataclass
class TradingConfig:
    # API Credentials
    USER: str = os.getenv('TRADOVATE_USER')
    PASS: str = os.getenv('TRADOVATE_PASS')
    CID: str = os.getenv('TRADOVATE_CID')
    SECRET: str = os.getenv('TRADOVATE_SECRET')
    DEVICE_ID: str = 'lido-bot-prod-001'
    APP_ID: str = 'LidoRestakingBot'
    
    # Trading
    SYMBOL: str = 'MET'  # Micro ETH
    INTERVAL: str = '15m'
    EMA_PERIOD: int = 20
    RSI_PERIOD: int = 14
    RSI_UPTREND: float = 50.0
    TICK_SIZE: float = 0.01
    TICK_VALUE: float = 0.1
    INITIAL_SL_TICKS: int = 15
    BE_TICKS: int = 15
    TP_TICKS: int = 50
    MAX_RISK_PCT: float = 0.02
    MAX_POSITIONS: int = 1
    DAILY_DD_CAP: float = 0.05
    INITIAL_BALANCE: float = float(os.getenv('INITIAL_BALANCE', 50000))
    
    # Runtime
    LIVE: bool = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
    BASE_URL: str = 'https://live.tradovateapi.com/v1' if LIVE else 'https://demo.tradovateapi.com/v1'

config = TradingConfig()
