import pytest
from unittest.mock import MagicMock, patch
from src.agents.data_collector import DataCollector

@pytest.fixture
def collector():
    with patch('src.agents.data_collector.FinnhubClient'), \
         patch('src.agents.data_collector.NewsApiClient'), \
         patch('src.agents.data_collector.SerperClient'):
        return DataCollector()

def test_normalize_finnhub(collector):
    raw_data = [{
        "datetime": 1698228000,
        "headline": "Test Headline",
        "summary": "Test Summary",
        "url": "http://test.com",
        "source": "Test Source"
    }]
    normalized = collector._normalize_finnhub_news(raw_data)
    assert len(normalized) == 1
    assert normalized[0]['title'] == "Test Headline"
    assert "published_at" in normalized[0]

def test_deduplicate(collector):
    articles = [
        {"url": "http://a.com", "title": "A", "id": "1", "source": "s", "text": "t", "published_at": "d", "ingested_at": "d", "language": "en"},
        {"url": "http://a.com", "title": "A Duplicate", "id": "2", "source": "s", "text": "t", "published_at": "d", "ingested_at": "d", "language": "en"},
        {"url": "http://b.com", "title": "B", "id": "3", "source": "s", "text": "t", "published_at": "d", "ingested_at": "d", "language": "en"}
    ]
    unique = collector._deduplicate(articles)
    assert len(unique) == 2
    urls = [a['url'] for a in unique]
    assert "http://a.com" in urls
    assert "http://b.com" in urls
