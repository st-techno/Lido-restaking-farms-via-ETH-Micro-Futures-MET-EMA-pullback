"""
P&L Reporting
"""
import pandas as pd
import os
from datetime import datetime
from utils.logger import logger

def log_pnl(pnl: float):
    os.makedirs('reports', exist_ok=True)
    with open('reports/pnl_log.csv', 'a') as f:
        f.write(f"{datetime.now().isoformat()},{pnl}\n")

def generate_weekly_report():
    try:
        df = pd.read_csv('reports/pnl_log.csv', names=['timestamp', 'pnl'], parse_dates=['timestamp'])
        weekly = df.tail(1008).set_index('timestamp')['pnl'].resample('W').sum().iloc[-1]  # ~7 days
        weekly_pct = (weekly / 50000) * 100  # $50k base
        df.to_csv('reports/weekly_pnl.csv', index=False)
        logger.info(f"Weekly Report: ${weekly:,.2f} ({weekly_pct:.2f}%)")
        return weekly_pct >= 22
    except Exception as e:
        logger.error(f"Report failed: {e}")
        return False
