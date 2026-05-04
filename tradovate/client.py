"""
Tradovate API Client - REST endpoints
"""
import requests
import logging
from typing import Dict, Any, List, Optional
from config.settings import config
from utils.logger import logger

class TradovateClient:
    def __init__(self):
        self.access_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.account_id: Optional[int] = None
    
    def authenticate(self) -> bool:
        """OAuth2 authentication"""
        auth_url = f"{config.BASE_URL}/auth/accesstokenrequest"
        payload = {
            'name': config.USER,
            'password': config.PASS,
            'appId': config.APP_ID,
            'appVersion': '1.0',
            'cid': config.CID,
            'sec': config.SECRET,
            'deviceId': config.DEVICE_ID
        }
        try:
            resp = requests.post(auth_url, json=payload, timeout=10).json()
            self.access_token = resp['accessToken']
            self.user_id = resp['userId']
            self.account_id = self._get_accounts()[0]['id']
            logger.info(f"Authenticated - User: {self.user_id}, Account: {self.account_id}")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        return {'Authorization': f'Bearer {self.access_token}'}
    
    def _get_accounts(self) -> List[Dict]:
        url = f"{config.BASE_URL}/account/list?userId={self.user_id}"
        return requests.get(url, headers=self._get_headers(), timeout=10).json()
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        url = f"{config.BASE_URL}/md/quote/{symbol}?symbol={symbol}"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=5).json()
            return resp[0] if resp else None
        except:
            return None
    
    def get_bars(self, symbol: str, days: int = 2) -> 'pd.DataFrame':
        import pandas as pd
        end = int(time.time() * 1000)
        start = end - (days * 86400 * 1000)
        url = f"{config.BASE_URL}/md/getChart?symbol={symbol}&interval={config.INTERVAL}&start={start}&end={end}"
        try:
            bars = requests.get(url, headers=self._get_headers(), timeout=10).json()
            df = pd.DataFrame(bars)
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            df.set_index('time', inplace=True)
            return df[['open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            logger.error(f"Bars fetch failed: {e}")
            return pd.DataFrame()
    
    def place_order(self, side: str, qty: int, sl_ticks: Optional[int] = None, 
                    tp_ticks: Optional[int] = None) -> Dict:
        url = f"{config.BASE_URL}/order/placeorder"
        payload = {
            'accountId': self.account_id,
            'contractId': self._get_contract_id(),
            'action': side,
            'orderType': 'Market',
            'qty': qty,
            'timeInForce': 'GTC'
        }
        if sl_ticks:
            payload['bracket1OrdType'] = 'Stop'
            payload['bracket1Offset'] = sl_ticks * config.TICK_SIZE
        if tp_ticks:
            payload['bracket2OrdType'] = 'Limit'
            payload['bracket2Offset'] = tp_ticks * config.TICK_SIZE
        
        resp = requests.post(url, headers=self._get_headers(), json=payload, timeout=10).json()
        logger.info(f"Order: {side} {qty} -> {resp.get('orderId', 'N/A')}")
        return resp
    
    def get_positions(self) -> List[Dict]:
        url = f"{config.BASE_URL}/account/positions?accountId={self.account_id}"
        return requests.get(url, headers=self._get_headers(), timeout=5).json()
    
    def get_pnl(self) -> float:
        url = f"{config.BASE_URL}/account/unrealizedPnlSummary?accountId={self.account_id}"
        try:
            data = requests.get(url, headers=self._get_headers(), timeout=5).json()
            return data.get('unrealizedPl', 0.0)
        except:
            return 0.0
    
    def _get_contract_id(self) -> int:
        # Prod: Cache from /md/instrument/{config.SYMBOL}
        # Demo placeholder
        return 109090  # MET contract ID (verify via API)
