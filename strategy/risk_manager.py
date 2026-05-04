"""
Risk management engine
"""
import logging
from datetime import datetime
import pytz
from typing import Optional
from config.settings import config
from utils.logger import logger
from tradovate.client import TradovateClient

class RiskManager:
    def __init__(self, client: TradovateClient):
        self.client = client
        self.initial_balance = config.INITIAL_BALANCE
        self.daily_start_balance = self.initial_balance
        self.daily_high = self.initial_balance
        self.timezone = pytz.timezone('US/Eastern')
        self.last_reset = None
    
    def reset_daily(self):
        now = datetime.now(self.timezone).date()
        if self.last_reset == now:
            return
        pnl = self.client.get_pnl()
        self.daily_start_balance = self.initial_balance + pnl
        self.daily_high = self.daily_start_balance
        self.last_reset = now
        logger.info(f"Daily reset: Start balance ${self.daily_start_balance:,.2f}")
    
    def calc_position_size(self, entry_price: float, sl_price: float) -> int:
        """Dynamic sizing for 2% risk"""
        self.reset_daily()
        balance = self.initial_balance  # Prod: Fetch real balance
        risk_usd = balance * config.MAX_RISK_PCT
        sl_distance_ticks = abs(entry_price - sl_price) / config.TICK_SIZE
        size = int(risk_usd / (sl_distance_ticks * config.TICK_VALUE))
        return max(1, min(size, 10))  # Micros cap
    
    def check_drawdown(self) -> bool:
        self.reset_daily()
        pnl = self.client.get_pnl()
        self.daily_high = max(self.daily_high, self.daily_start_balance + pnl)
        dd_pct = (self.daily_high - (self.daily_start_balance + pnl)) / self.initial_balance
        if dd_pct > config.DAILY_DD_CAP:
            logger.warning(f"DD Alert: {dd_pct:.2%} > {config.DAILY_DD_CAP:.0%}")
            return False
        return True
