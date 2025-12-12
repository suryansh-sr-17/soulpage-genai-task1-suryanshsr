import os
import requests
import logging
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://finnhub.io/api/v1"

class FinnhubClient:
    def __init__(self):
        self.api_key = os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            logger.warning("FINNHUB_API_KEY is not set.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch_company_news(self, symbol: str, from_date: str, to_date: str):
        """
        Fetch company news from Finnhub.
        Dates should be in 'YYYY-MM-DD' format.
        """
        if not self.api_key:
            return []
            
        url = f"{BASE_URL}/company-news"
        params = {
            "symbol": symbol,
            "from": from_date,
            "to": to_date,
            "token": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Fetched {len(data)} news items for {symbol} from Finnhub")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Finnhub news: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch_prices(self, symbol: str, resolution: str = "D", from_timestamp: int = None, to_timestamp: int = None):
        """
        Fetch stock candles (prices) from Finnhub.
        Resolution: Supported resolution includes 1, 5, 15, 30, 60, D, W, M.
        Timestamps are UNIX timestamps.
        """
        if not self.api_key:
            return {}

        url = f"{BASE_URL}/stock/candle"
        params = {
            "symbol": symbol,
            "resolution": resolution,
            "from": from_timestamp,
            "to": to_timestamp,
            "token": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('s') == 'ok':
                logger.info(f"Fetched price data for {symbol} from Finnhub")
                return data
            else:
                logger.warning(f"No price data found for {symbol}")
                return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Finnhub prices: {e}")
            raise
