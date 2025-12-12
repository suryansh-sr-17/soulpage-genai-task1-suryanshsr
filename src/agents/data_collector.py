import uuid
import logging
from datetime import datetime, timezone
import hashlib
from typing import List, Dict

from src.clients.finnhub_client import FinnhubClient
from src.clients.newsapi_client import NewsApiClient
from src.clients.serper_client import SerperClient
from src.utils.validators import validate_article

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        self.finnhub = FinnhubClient()
        self.newsapi = NewsApiClient()
        self.serper = SerperClient()

    def _normalize_finnhub_news(self, items: List[Dict]) -> List[Dict]:
        normalized = []
        for item in items:
            try:
                # Finnhub timestamps are seconds since epoch
                pub_ts = item.get('datetime', 0)
                pub_date = datetime.fromtimestamp(pub_ts, tz=timezone.utc).isoformat()
                
                article = {
                    "id": str(item.get('id', uuid.uuid4())),
                    "source": item.get('source', 'Finnhub'),
                    "title": item.get('headline', ''),
                    "text": item.get('summary', ''),
                    "url": item.get('url', ''),
                    "published_at": pub_date,
                    "language": "en", # Assumption
                    "ingested_at": datetime.now(timezone.utc).isoformat()
                }
                normalized.append(article)
            except Exception as e:
                logger.warning(f"Skipping malformed Finnhub item: {e}")
        return normalized

    def _normalize_newsapi_articles(self, items: List[Dict]) -> List[Dict]:
        normalized = []
        for item in items:
            try:
                article = {
                    "id": str(uuid.uuid4()), # NewsAPI doesn't always perform IDs
                    "source": item.get('source', {}).get('name', 'NewsAPI'),
                    "title": item.get('title', ''),
                    "text": item.get('description', '') or item.get('content', '') or '', 
                    "url": item.get('url', ''),
                    "published_at": item.get('publishedAt', datetime.now(timezone.utc).isoformat()),
                    "language": "en",
                    "ingested_at": datetime.now(timezone.utc).isoformat()
                }
                normalized.append(article)
            except Exception as e:
                 logger.warning(f"Skipping malformed NewsAPI item: {e}")
        return normalized

    def _normalize_serper_results(self, items: List[Dict]) -> List[Dict]:
        normalized = []
        for item in items:
            try:
                # Serper doesn't give a date always, use current time as fallback or try to extract
                date_str = item.get('date', '')
                # Minimal parsing or fallback
                pub_date = datetime.now(timezone.utc).isoformat()

                article = {
                    "id": str(uuid.uuid4()),
                    "source": "SerperWeb",
                    "title": item.get('title', ''),
                    "text": item.get('snippet', ''),
                    "url": item.get('link', ''),
                    "published_at": pub_date,
                    "language": "en",
                    "ingested_at": datetime.now(timezone.utc).isoformat()
                }
                normalized.append(article)
            except Exception as e:
                logger.warning(f"Skipping malformed Serper item: {e}")
        return normalized

    def _deduplicate(self, articles: List[Dict]) -> List[Dict]:
        seen_urls = set()
        seen_titles = set()
        unique_articles = []

        for art in articles:
            # Check for bad data
            if not art['url'] or not art['title']:
                continue

            # Simple hash for duplicate checking
            url_hash = art['url'].strip().lower()
            title_hash = art['title'].strip().lower()

            if url_hash in seen_urls:
                continue
            if title_hash in seen_titles:
                continue
            
            seen_urls.add(url_hash)
            seen_titles.add(title_hash)
            unique_articles.append(art)
            
        return unique_articles

    def collect(self, company_name: str, ticker: str, from_date: str, to_date: str) -> Dict:
        """
        Collects data from all sources, normalizes, and deduplicates.
        Returns a dict with 'articles' and 'price_data'.
        """
        logger.info(f"Starting data collection for {company_name} ({ticker})")
        
        all_articles = []

        # 1. Finnhub News
        try:
            finnhub_news = self.finnhub.fetch_company_news(ticker, from_date, to_date)
            all_articles.extend(self._normalize_finnhub_news(finnhub_news))
        except Exception as e:
            logger.error(f"Finnhub collection failed: {e}")

        # 2. NewsAPI
        try:
            newsapi_articles = self.newsapi.search_articles(f"{company_name} {ticker}", from_date, to_date)
            all_articles.extend(self._normalize_newsapi_articles(newsapi_articles))
        except Exception as e:
            logger.error(f"NewsAPI collection failed: {e}")

        # 3. Serper Fallback (if raw collection low)
        if len(all_articles) < 5:
            logger.info("Low article count, triggering Serper fallback...")
            try:
                serper_results = self.serper.search_web(f"{company_name} {ticker} news")
                all_articles.extend(self._normalize_serper_results(serper_results))
            except Exception as e:
                logger.error(f"Serper collection failed: {e}")

        # Deduplicate
        unique_articles = self._deduplicate(all_articles)
        logger.info(f"Collected {len(all_articles)} raw articles, {len(unique_articles)} after dedupe.")

        # Validate
        valid_articles = []
        for art in unique_articles:
            try:
                validate_article(art)
                valid_articles.append(art)
            except Exception:
                pass # Already logged in validator

        # Fetch Prices
        price_summary = {}
        try:
            # Finnhub requires unix timestamp for candles
            dt_from = datetime.fromisoformat(from_date) if 'T' in from_date else datetime.strptime(from_date, "%Y-%m-%d")
            dt_to = datetime.fromisoformat(to_date) if 'T' in to_date else datetime.strptime(to_date, "%Y-%m-%d")
            
            ts_from = int(dt_from.timestamp())
            ts_to = int(dt_to.timestamp())
            
            price_data = self.finnhub.fetch_prices(ticker, from_timestamp=ts_from, to_timestamp=ts_to)
            if price_data:
                # Calculate simple summary
                closes = price_data.get('c', [])
                if closes:
                    price_summary = {
                        "current_price": closes[-1],
                        "start_price": closes[0],
                        "high": max(closes),
                        "low": min(closes),
                        "change_percent": ((closes[-1] - closes[0]) / closes[0]) * 100
                    }
        except Exception as e:
            logger.error(f"Price collection failed: {e}")

        return {
            "articles": valid_articles,
            "prices": price_summary
        }
