import argparse
import sys
import os
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestrator import Orchestrator

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Company Intelligence Agentic System")
    parser.add_argument("--company", required=True, help="Company Name")
    parser.add_argument("--ticker", required=True, help="Stock Ticker Symbol")
    parser.add_argument("--from-date", required=True, help="Start Date (YYYY-MM-DD)")
    parser.add_argument("--to-date", required=True, help="End Date (YYYY-MM-DD)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of docs to retrieve")
    
    args = parser.parse_args()
    
    orchestrator = Orchestrator()
    report = orchestrator.run(
        company=args.company,
        ticker=args.ticker,
        from_date=args.from_date,
        to_date_param=args.to_date,
        top_k=args.top_k
    )
    
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
