import os
import requests
import json
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.validators import validate_analyst_output

logger = logging.getLogger(__name__)

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
MODEL_ID = "llama-3.3-70b-versatile"

class AnalystAgent:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.warning("GROQ_API_KEY is not set.")

    def _call_groq(self, messages: list, max_tokens=1024, temperature=0.1):
        """
        Call Groq Chat Completions API.
        """
        if not self.api_key:
            raise ValueError("Groq API key missing")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODEL_ID,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {"type": "json_object"} # Enforce JSON mode
        }

        try:
            response = requests.post(GROQ_ENDPOINT, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Groq API call failed: {e}")
            if response.text:
                logger.error(f"Groq Error details: {response.text}")
            raise

    def analyze(self, company: str, price_summary: dict, doc_snippets: list):
        """
        Generate intelligence report.
        """
        # Format documents for prompt
        docs_text = ""
        for d in doc_snippets:
            docs_text += f"---\nID: {d['id']}\nURL: {d['metadata']['url']}\nCONTENT: {d['snippet']}...\n"

        # System Prompt
        system_prompt = f"""
You are an expert Financial Analyst. Your task is to analyze the provided company news and stock price data to produce a structured intelligence report.

You will be given:
1. Company Name
2. Stock Price Summary
3. Relevant Document Snippets (with IDs and URLs)

INSTRUCTIONS:
1. Analyze the sentiment and key drivers affecting the stock.
2. Identify major risks.
3. MOST IMPORTANT: Provide evidence for your claims. Every piece of evidence MUST include the exact `article_id` and `url` from the provided documents.
4. Output strict JSON exactly matching the schema.
5. If there is insufficient data to form a conclusion, set confidence to low (0.0 - 0.3) and state that in the summary.
6. Do NOT hallucinate article IDs or facts not present in the documents.

JSON SCHEMA:
{{
  "summary": "Executive summary (3-5 sentences).",
  "sentiment": "positive" | "neutral" | "negative",
  "key_drivers": ["driver 1", "driver 2"],
  "risks": ["risk 1", "risk 2"],
  "evidence": [
    {{
      "article_id": "exact_id_from_doc",
      "quote": "short relevant quote",
      "url": "exact_url_from_doc"
    }}
  ],
  "confidence": 0.0 to 1.0
}}
"""
        
        user_message = f"""
COMPANY: {company}

PRICE DATA:
{json.dumps(price_summary, indent=2)}

DOCUMENTS:
{docs_text}

Analyze and generate the JSON report.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        try:
            # Call Groq
            logger.info("Sending analysis request to Groq...")
            result = self._call_groq(messages)
            
            content = result['choices'][0]['message']['content']
            
            # Parse JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                logger.error("Failed to parse Groq output as JSON")
                logger.debug(f"Raw output: {content}")
                raise ValueError("Invalid JSON from LLM")

            # Validate
            validate_analyst_output(data)
            
            return data

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            # Return basic fallback to avoid crashing UI
            return {
                "summary": "Analysis failed due to technical error.",
                "sentiment": "neutral",
                "key_drivers": [],
                "risks": ["Analysis Error"],
                "evidence": [],
                "confidence": 0.0
            }
