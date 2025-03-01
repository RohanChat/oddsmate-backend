#!/usr/bin/env python3
import json
import os
import requests
import time
import dotenv

# ----- CONFIGURATION -----
dotenv.load_dotenv()
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4/historical/"
OUTPUT_FILE = "processed_events_2020_2025.jsonl"  # Change this path if desired

# ----- HELPER FUNCTIONS -----

def get_odds(date, event_ids):
    """
    Retrieve historical odds for a specific MMA event.

    Parameters:
        event_date (str): The date to use in the API call (typically the event's "commence_time").
        event_id (str): The event ID from the JSON "data" item.

    Returns:
        dict: The API's JSON response (or an empty dict on error).
    """
    url = f"{BASE_URL}" + "sports/mma_mixed_martial_arts/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "dateFormat": "iso",
        "regions": "us,us2",
        "oddsFormat": "decimal",
        "markets": "h2h,spreads",
        "eventIds": ",".join(event_ids),
        "date": date + "Z",
    }
    try:
        response = requests.get(url, params=params)
        # print(response.url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching odds for date {date}: {e}")
        return {}

def process_event(event_json):

    ids = []
    if 'response' in event_json and 'data' in event_json['response']:
        ids = [item['id'] for item in event_json['response']['data']]
    
    print(ids)
    
    return get_odds(event_json.get("date"), ids)


def write_event_to_file(event, file_path):
    """
    Appends the processed event as a JSON object (one per line) to the specified file.
    """
    with open(file_path, "a") as f:
        # You can remove the indent if you prefer compact JSON.
        f.write(json.dumps(event, indent=4) + "\n")

def parse_multiple_json_objects(file_path):
    """
    Generator that extracts multiple JSON objects from a file.

    This function works even if each JSON object spans multiple lines.
    """
    with open(file_path, "r") as f:
        content = f.read()

    decoder = json.JSONDecoder()
    pos = 0
    length = len(content)
    while pos < length:
        # Skip whitespace between objects.
        while pos < length and content[pos].isspace():
            pos += 1
        if pos >= length:
            break
        try:
            obj, idx = decoder.raw_decode(content, pos)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON starting at position {pos}: {e}")
            break
        yield obj
        pos = idx

def process_file(input_file_path, output_file_path, sleep_time=1):
    """
    Processes the input file containing multiple JSON objects and writes each processed event to the output file.

    Parameters:
        input_file_path (str): Path to the input file.
        output_file_path (str): Path where processed events will be appended.
        sleep_time (float): Delay between processing events (useful for API rate limits).

    Returns:
        list: A list of processed event objects.
    """
    # Clear the output file before starting (so you start fresh).
    open(output_file_path, "w").close()

    processed_events = []
    for idx, event_json in enumerate(parse_multiple_json_objects(input_file_path), start=1):
        print(f"Processing event #{idx} ...")
        processed = process_event(event_json)
        processed_events.append(processed)
        write_event_to_file(processed, output_file_path)
        time.sleep(sleep_time)
    return processed_events

# ----- MAIN SCRIPT -----

def main():
    input_file_path = "odds_references_2020_2025.jsonl"  # Update with your input file path
    process_file(input_file_path, OUTPUT_FILE)

if __name__ == "__main__":
    main()
