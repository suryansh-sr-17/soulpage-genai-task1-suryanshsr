import pytest
import shutil
import os
from src.ingest.chroma_ingest import ChromaIngest

TEMP_CHROMA = "./test_chroma_db"

@pytest.fixture
def chroma_client():
    if os.path.exists(TEMP_CHROMA):
        shutil.rmtree(TEMP_CHROMA)
    client = ChromaIngest(persist_dir=TEMP_CHROMA)
    yield client
    if os.path.exists(TEMP_CHROMA):
        shutil.rmtree(TEMP_CHROMA)

def test_ingest_and_query(chroma_client):
    articles = [
        {
            "id": "test_1",
            "title": "AI in Finance",
            "text": "Deep learning is changing stock prediction.",
            "url": "http://test.com/ai",
            "source": "Tech",
            "published_at": "2023-01-01T00:00:00",
            "language": "en",
            "ingested_at": "2023-01-01T00:00:00"
        }
    ]
    
    # Ingest
    chroma_client.ingest_articles("TEST", articles)
    
    # Query
    results = chroma_client.query("TEST", "deep learning")
    assert len(results) >= 1
    assert "AI in Finance" in results[0]['snippet']
    assert results[0]['id'] == "test_1"
