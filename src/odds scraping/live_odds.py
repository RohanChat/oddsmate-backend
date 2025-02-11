## LISTENER THAT RECORDES LIVE ODDS FROM THE API FOR MMA

import os
import time
import json
import requests
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
if not ODDS_API_KEY:
    raise Exception("ODDS_API_KEY not found in environment variables.")

# Endpoint for live MMA odds (sport: mma_mixed_martial_arts)
BASE_URL = "https://api.the-odds-api.com/v4/sports/mma_mixed_martial_arts/odds"

def fetch_live_odds():
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us,us2",            # Regions to cover
        "markets": "h2h",               # Odds market (head to head)
        "dateFormat": "iso",            # Response date format
        "oddsFormat": "decimal",        # Odds format
        "includeLinks": "true",         # Optionally include links
        "includeSids": "true",          # Optionally include source ids
        "includeBetLimits": "true"      # Optionally include bet limits
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching live odds: {e}")
        return None

def main():
    output_file = "live_odds_output.jsonl"  # New record for each poll (jsonlines format)
    print("Starting live odds listener. Press Ctrl+C to stop.")
    
    while True:
        odds_data = fetch_live_odds()
        if odds_data is not None:
            # Record a timestamp with the data
            record = {
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                "live_odds": odds_data
            }
            # Append the record immediately to the output file.
            with open(output_file, "a") as f:
                f.write(json.dumps(record) + "\n")
                f.flush()
            print(f"Recorded live odds at {record['timestamp']}")
        # Sleep before polling again (adjust delay as needed)
        time.sleep(15)

if __name__ == "__main__":
    main()