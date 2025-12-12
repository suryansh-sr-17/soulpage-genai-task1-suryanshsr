ARTICLE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "source": {"type": "string"},
        "title": {"type": "string"},
        "text": {"type": "string"},
        "url": {"type": "string", "format": "uri"},
        "published_at": {"type": "string", "format": "date-time"},
        "language": {"type": "string"},
        "ingested_at": {"type": "string", "format": "date-time"}
    },
    "required": ["id", "source", "title", "text", "url", "published_at", "ingested_at"]
}

ANALYST_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative"]},
        "key_drivers": {"type": "array", "items": {"type": "string"}},
        "risks": {"type": "array", "items": {"type": "string"}},
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "article_id": {"type": "string"},
                    "quote": {"type": "string"},
                    "url": {"type": "string", "format": "uri"}
                },
                "required": ["article_id", "quote", "url"]
            }
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "required": ["summary", "sentiment", "key_drivers", "risks", "evidence", "confidence"]
}
