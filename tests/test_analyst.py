import pytest
import json
from unittest.mock import MagicMock, patch
from src.agents.analyst import AnalystAgent

@pytest.fixture
def analyst():
    return AnalystAgent()

def test_analyze_flow(analyst):
    mock_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "summary": "Test Summary",
                    "sentiment": "positive",
                    "key_drivers": ["Growth"],
                    "risks": ["Competition"],
                    "evidence": [],
                    "confidence": 0.8
                })
            }
        }]
    }
    
    with patch.object(analyst, '_call_groq', return_value=mock_response):
        report = analyst.analyze("Test Corp", {}, [{"id": "1", "metadata": {"url": "u"}, "snippet": "s"}])
        assert report["sentiment"] == "positive"
        assert report["summary"] == "Test Summary"
        assert report["confidence"] == 0.8
