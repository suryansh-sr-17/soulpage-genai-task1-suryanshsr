from jsonschema import validate, ValidationError
from .schemas import ARTICLE_SCHEMA, ANALYST_OUTPUT_SCHEMA
import logging

logger = logging.getLogger(__name__)

def validate_article(data):
    """
    Validate an article object against ARTICLE_SCHEMA.
    """
    try:
        validate(instance=data, schema=ARTICLE_SCHEMA)
        return True
    except ValidationError as e:
        logger.error(f"Article validation failed: {e.message}")
        raise

def validate_analyst_output(data):
    """
    Validate analyst output against ANALYST_OUTPUT_SCHEMA.
    """
    try:
        validate(instance=data, schema=ANALYST_OUTPUT_SCHEMA)
        return True
    except ValidationError as e:
        logger.error(f"Analyst output validation failed: {e.message}")
        raise
