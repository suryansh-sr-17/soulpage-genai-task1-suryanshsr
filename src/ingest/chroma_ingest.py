import chromadb
from chromadb.config import Settings
import os
import uuid
import logging
from typing import List, Dict
from datetime import datetime

from src.ingest.embeddings import embed_texts

logger = logging.getLogger(__name__)

# Default persistence directory
CHROMA_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_db")

class ChromaIngest:
    def __init__(self, persist_dir=CHROMA_DIR):
        # Initialize Client
        # Using persistent client for local storage
        try:
            self.client = chromadb.PersistentClient(path=persist_dir)
            logger.info(f"Initialized ChromaDB at {persist_dir}")
        except Exception as e:
            logger.error(f"Failed to init ChromaDB: {e}")
            raise

    def ensure_collection(self, name: str):
        """
        Get or create a collection.
        """
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"} # Use cosine similarity
        )

    def ingest_articles(self, company_ticker: str, articles: List[Dict]):
        """
        Ingest a list of articles into a collection named after the ticker.
        """
        collection_name = f"ticker_{company_ticker.lower()}"
        col = self.ensure_collection(collection_name)
        
        if not articles:
            return

        # Prepare batch
        ids = []
        documents = []
        metadatas = []
        
        for art in articles:
            # Simple chunking: Use first 1000 chars if text is too long
            # In a real app, use a proper text splitter
            text_content = f"{art['title']}\n{art['text']}"
            
            # Using article ID as vector ID
            ids.append(art['id'])
            documents.append(text_content)
            metadatas.append({
                "source": art['source'],
                "url": art['url'],
                "published_at": art['published_at'], 
                "title": art['title']
            })

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(documents)} documents...")
        embeddings = embed_texts(documents).tolist()

        # Add to Chroma
        # upsert helps avoid duplicate key errors if re-running
        col.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )
        logger.info(f"Ingested {len(documents)} into collection '{collection_name}'")

    def query(self, company_ticker: str, query_text: str, top_k: int = 5):
        """
        Retrieve relevant documents.
        """
        collection_name = f"ticker_{company_ticker.lower()}"
        try:
            col = self.client.get_collection(collection_name)
        except ValueError:
             logger.warning(f"Collection {collection_name} not found.")
             return []

        query_embedding = embed_texts([query_text]).tolist()
        
        results = col.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        
        # Flatten results
        # results structure: {'ids': [[...]], 'documents': [[...]], 'metadatas': [[...]]}
        retrieved = []
        if results['ids']:
            ids = results['ids'][0]
            docs = results['documents'][0]
            metas = results['metadatas'][0]
            
            for i in range(len(ids)):
                retrieved.append({
                    "id": ids[i],
                    "snippet": docs[i][:500], # Return first 500 chars as snippet
                    "full_text": docs[i],
                    "metadata": metas[i]
                })
                
        return retrieved
