import os
import requests
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logger = logging.getLogger(__name__)

BASE_URL = "https://newsapi.org/v2"

class NewsApiClient:
    def __init__(self):
        self.api_key = os.getenv("NEWSAPI_KEY")
        if not self.api_key:
            logger.warning("NEWSAPI_KEY is not set.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search_articles(self, query: str, from_date: str, to_date: str):
        """
        Search for articles using NewsAPI Everything endpoint.
        Dates should be in 'YYYY-MM-DD' format.
        """
        if not self.api_key:
            return []
            
        url = f"{BASE_URL}/everything"
        params = {
            "q": query,
            "from": from_date,
            "to": to_date,
            "sortBy": "relevancy",
            "language": "en",
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            articles = data.get("articles", [])
            logger.info(f"Fetched {len(articles)} articles for '{query}' from NewsAPI")
            return articles
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching NewsAPI articles: {e}")
            raise
