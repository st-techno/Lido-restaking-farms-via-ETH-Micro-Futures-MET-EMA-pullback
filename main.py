"""
Main entrypoint - Scheduler & orchestration
"""
import argparse
import time
import signal
import sys
from apscheduler.schedulers.background import BackgroundScheduler
from config.settings import config
from tradovate.client import TradovateClient
from strategy.engine import LidoRestakingStrategy
from utils.logger import logger
from utils.reporter import log_pnl, generate_weekly_report

client: TradovateClient = None
strategy: LidoRestakingStrategy = None
scheduler: BackgroundScheduler = None

def signal_handler(sig, frame):
    logger.info("Shutdown signal received")
    if scheduler:
        scheduler.shutdown()
    sys.exit(0)

def strategy_cycle():
    strategy.run_cycle()

def pnl_logger():
    pnl = client.get_pnl()
    log_pnl(pnl)
    logger.debug(f"Current PnL: ${pnl:,.2f}")

def main():
    global client, strategy, scheduler
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['demo', 'live'], default='demo')
    args = parser.parse_args()
    
    config.LIVE = args.mode == 'live'
    logger.info(f"Starting Lido Bot - Mode: {args.mode}")
    
    # Init
    client = TradovateClient()
    if not client.authenticate():
        logger.error("Auth failed - Exiting")
        return
    
    strategy = LidoRestakingStrategy(client)
    
    # Scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(strategy_cycle, 'interval', minutes=1)
    scheduler.add_job(pnl_logger, 'interval', minutes=15)
    scheduler.add_job(generate_weekly_report, 'cron', day_of_week='sun', hour=23, timezone='US/Eastern')
    scheduler.start()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
