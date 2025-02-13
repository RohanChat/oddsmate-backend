import os
import time
import json
import requests
from dotenv import load_dotenv

class LiveOddsListener:
    """
    A listener that records live MMA odds from The Odds API.
    
    It continuously polls the API at a specified interval and appends the JSON response
    along with a timestamp to an output file (in JSON Lines format).
    """

    BASE_URL = "https://api.the-odds-api.com/v4/sports/mma_mixed_martial_arts/odds"

    def __init__(self, output_file="live_odds_output.jsonl", poll_interval=15):
        """
        Initializes the live odds listener.
        
        Args:
            output_file (str): The file path where the records will be appended.
            poll_interval (int): The delay (in seconds) between polls.
        """
        load_dotenv()
        self.odds_api_key = os.getenv("ODDS_API_KEY")
        if not self.odds_api_key:
            raise Exception("ODDS_API_KEY not found in environment variables.")
        self.output_file = output_file
        self.poll_interval = poll_interval

    def fetch_live_odds(self):
        """
        Fetches live odds from the API.
        
        Returns:
            dict or None: The JSON response from the API if successful, otherwise None.
        """
        params = {
            "apiKey": self.odds_api_key,
            "regions": "us,us2",
            "markets": "h2h",
            "dateFormat": "iso",
            "oddsFormat": "decimal",
            "includeLinks": "true",
            "includeSids": "true",
            "includeBetLimits": "true"
        }
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching live odds: {e}")
            return None

    def run(self):
        """
        Starts the live odds listener. This method will continuously poll the API
        and record the results to the output file until interrupted.
        """
        print("Starting live odds listener. Press Ctrl+C to stop.")
        while True:
            odds_data = self.fetch_live_odds()
            if odds_data is not None:
                record = {
                    "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    "live_odds": odds_data
                }
                with open(self.output_file, "a") as f:
                    f.write(json.dumps(record) + "\n")
                    f.flush()
                print(f"Recorded live odds at {record['timestamp']}")
            time.sleep(self.poll_interval)

if __name__ == "__main__":
    listener = LiveOddsListener()
    listener.run()
