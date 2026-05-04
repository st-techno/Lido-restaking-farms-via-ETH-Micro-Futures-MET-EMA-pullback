"""
Lido Restaking Strategy Engine
"""
import pandas as pd
import logging
from typing import Optional
from config.settings import config
from utils.logger import logger
from tradovate.client import TradovateClient
from strategy.indicators import calculate_indicators
from strategy.risk_manager import RiskManager

class LidoRestakingStrategy:
    def __init__(self, client: TradovateClient):
        self.client = client
        self.risk_mgr = RiskManager(client)
        self.data: pd.DataFrame = pd.DataFrame()
    
    def update_data(self):
        """Fetch & compute indicators"""
        bars = self.client.get_bars(config.SYMBOL, days=2)
        if not bars.empty:
            self.data = calculate_indicators(bars).tail(50)
    
    def generate_signal(self) -> Optional[str]:
        """Core signal logic"""
        if len(self.data) < max(config.EMA_PERIOD, config.RSI_PERIOD) + 1:
            return None
        
        latest = self.data.iloc[-1]
        prev = self.data.iloc[-2]
        
        uptrend = latest['close'] > latest['ema20'] and latest['rsi'] > config.RSI_UPTREND
        pullback = prev['close'] > prev['ema20'] and latest['low'] <= latest['ema20']
        
        if uptrend and pullback and self.risk_mgr.check_drawdown() and self._open_positions_count() == 0:
            return 'BUY'
        return None
    
    def _open_positions_count(self) -> int:
        positions = self.client.get_positions()
        return len([p for p in positions if p.get('contractSymbol') == config.SYMBOL and p['pos'] > 0])
    
    def execute_trade(self, signal: str, current_price: float):
        """Place bracket order"""
        sl_price = current_price - (config.INITIAL_SL_TICKS * config.TICK_SIZE)
        qty = self.risk_mgr.calc_position_size(current_price, sl_price)
        
        self.client.place_order(
            side='Buy' if signal == 'BUY' else 'Sell',
            qty=qty,
            sl_ticks=config.INITIAL_SL_TICKS,
            tp_ticks=config.TP_TICKS
        )
        logger.info(f"EXECUTED {signal}: {qty} @ {current_price:.2f}, SL: {sl_price:.2f}")
    
    def manage_positions(self):
        """Trail stops logic (simplified - enhance with WS)"""
        positions = self.client.get_positions()
        for pos in positions:
            if pos.get('contractSymbol') == config.SYMBOL and pos['pos'] > 0:
                # Trail logic: Update SL if profitable (API call to modify)
                profit_ticks = (pos.get('markPrice', 0) - pos['avgPrice']) / config.TICK_SIZE
                if profit_ticks >= config.BE_TICKS:
                    logger.info(f"Trail to BE for pos {pos['orderId']}")
                    # client.modify_order(pos['orderId'], new_sl=pos['avgPrice'] + config.TICK_SIZE * config.BE_TICKS)
    
    def run_cycle(self):
        """One strategy iteration"""
        self.update_data()
        quote = self.client.get_quote(config.SYMBOL)
        if not quote:
            return
        
        signal = self.generate_signal()
        if signal:
            self.execute_trade(signal, quote['last'])
        
        self.manage_positions()
