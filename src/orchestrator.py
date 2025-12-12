import logging
import json
import os
from datetime import datetime, timezone

from src.agents.data_collector import DataCollector
from src.ingest.chroma_ingest import ChromaIngest
from src.agents.analyst import AnalystAgent

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        self.collector = DataCollector()
        self.chroma = ChromaIngest()
        self.analyst = AnalystAgent()

    def run(self, company: str, ticker: str, from_date: str, to_date_param: str, top_k: int = 5):
        """
        Run the full pipeline:
        1. Collect Data
        2. Ingest
        3. Retrieve
        4. Analyze
        """
        logger.info(f"--- Starting Pipeline for {company} ({ticker}) ---")
        
        # 1. Collect
        logger.info("Phase 1: Data Collection")
        # Ensure dates are strings YYYY-MM-DD
        data = self.collector.collect(
            company_name=company,
            ticker=ticker,
            from_date=from_date,
            to_date=to_date_param
        )
        articles = data.get("articles", [])
        prices = data.get("prices", {})
        
        if not articles:
            logger.warning("No articles found. Proceeding with caution.")
        else:
            logger.info(f"Collected {len(articles)} articles.")

        # 2. Ingest
        logger.info("Phase 2: Ingestion")
        self.chroma.ingest_articles(ticker, articles)

        # 3. Retrieve
        logger.info("Phase 3: Retrieval")
        # Query for general company news + specific analysis context
        query_text = f"Latest financial performance, strategic moves, risks, and market outlook for {company}"
        retrieved_docs = self.chroma.query(ticker, query_text, top_k=top_k)
        
        # 4. Analyze
        logger.info("Phase 4: Analysis")
        report = self.analyst.analyze(
            company=company,
            price_summary=prices,
            doc_snippets=retrieved_docs
        )
        
        # Save run artifact (optional debug)
        self._save_result(ticker, report)
        
        return report

    def _save_result(self, ticker, report):
        os.makedirs("output", exist_ok=True)
        fname = f"output/report_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(fname, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to {fname}")
