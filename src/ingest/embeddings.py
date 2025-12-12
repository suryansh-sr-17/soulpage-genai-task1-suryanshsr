from sentence_transformers import SentenceTransformer
import os
import logging
from typing import List
import numpy as np

logger = logging.getLogger(__name__)

# Singleton wrapper
MODEL = None
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

def get_model():
    global MODEL
    if MODEL is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        MODEL = SentenceTransformer(MODEL_NAME)
    return MODEL

def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Generate embeddings for a list of texts.
    Returns a numpy array of embeddings.
    """
    if not texts:
        return np.array([])
        
    model = get_model()
    # show_progress_bar=False to keep logs clean
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings
