import os
import requests
import logging
import json
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logger = logging.getLogger(__name__)

BASE_URL = "https://google.serper.dev/search"

class SerperClient:
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            logger.warning("SERPER_API_KEY is not set.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search_web(self, query: str, num_results: int = 5):
        """
        Perform a web search using Serper API.
        """
        if not self.api_key:
            return []
            
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "q": query,
            "num": num_results
        })
        
        try:
            response = requests.post(BASE_URL, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            organic_results = data.get("organic", [])
            logger.info(f"Fetched {len(organic_results)} web search results for '{query}' from Serper")
            return organic_results
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Serper results: {e}")
            raise
