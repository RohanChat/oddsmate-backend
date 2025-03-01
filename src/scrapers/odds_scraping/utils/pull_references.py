import os
import time
import json
import requests
from datetime import datetime, timezone
from calendar import monthrange
from dotenv import load_dotenv
from datetime import timedelta
from bs4 import BeautifulSoup

# Load API key from .env
load_dotenv()
ODDS_API_KEY = os.getenv('ODDS_API_KEY')
if not ODDS_API_KEY:
    raise Exception("ODDS_API_KEY not found in environment variables.")

# Base URL for historical MMA events (odds are not included)
BASE_URL = "https://api.the-odds-api.com/v4/historical/sports/mma_mixed_martial_arts/events"

def get_events_at_date(date):
    """
    Get MMA events at a specific date.
    """
    # Set snapshot_time to 10:05:00 for the given date (as in the bash request)
    snapshot_time = date.replace(hour=10, minute=5, second=0, microsecond=0)

    # Use one day before and after snapshot_time to calculate commenceTime window
    commence_from = (snapshot_time - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    commence_to = (snapshot_time + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=0)

    params = {
        'apiKey': ODDS_API_KEY,
        'dateFormat': 'iso',
        'commenceTimeFrom': commence_from.isoformat() + "Z",
        'commenceTimeTo': commence_to.isoformat() + "Z",
        'date': snapshot_time.isoformat() + "Z"
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching events: {e}")
        return None
    
def scrape_ufcstats_events():
    """
    Scrapes the UFCStats completed events page and returns a list of dictionaries,
    each containing the event name, link and date as a datetime object.
    """
    url = "http://ufcstats.com/statistics/events/completed?page=all"
    response = requests.get(url)
    if response.status_code != 200:
        print("Error fetching UFCStats page")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    events = []
    
    for row in soup.find_all('tr', class_='b-statistics__table-row'):
        # Get event link and name
        link_tag = row.find('a', class_='b-link b-link_style_black')
        if not link_tag:
            continue
        event_name = link_tag.text.strip()
        # The link (e.g., http://ufcstats.com/event-details/e6015889f50075d2)
        event_link = link_tag.get('href')
        
        # Get event date from the span
        date_span = row.find('span', class_='b-statistics__date')
        if date_span:
            date_str = date_span.text.strip()  # e.g. "February 08, 2025"
            try:
                event_date = datetime.strptime(date_str, "%B %d, %Y")
            except Exception as e:
                print(f"Error parsing date '{date_str}': {e}")
                continue

            events.append({
                "name": event_name,
                "link": event_link,
                "date": event_date  # store as datetime
            })
    return events

def process_all_ufcstats_events():
    """
    Loops through all events from UFCStats, converts each event date to ISO format,
    calls get_events_at_date() using that date, and collects the API data.
    Returns a list of result dictionaries.
    """
    ufc_events = scrape_ufcstats_events()
    results = []
    
    if not ufc_events:
        print("No UFCStats events found.")
        return results

    for event in ufc_events:
        print(f"Processing UFCStats event: {event['name']} on {event['date'].strftime('%Y-%m-%d')}")
        api_data = get_events_at_date(event['date'])
        results.append({
            "ufcstats_event": {
                "name": event["name"],
                "link": event["link"],
                "date": event["date"].isoformat()
            },
            "api_response": api_data
        })
        # Small delay to avoid hitting API rate limits
        time.sleep(1)
    return results

def main():
    output_file = "ufcstats_events_api_data.jsonl"  # using jsonlines format
    ufc_events = scrape_ufcstats_events()
    
    if not ufc_events:
        print("No UFCStats events found.")
        return
    
    with open(output_file, "a") as f:  # open file in append mode
        for event in ufc_events:
            print(f"Processing UFCStats event: {event['name']} on {event['date'].strftime('%Y-%m-%d')}")
            event_id = event["link"].split("/event-details/")[-1]
            api_data = get_events_at_date(event['date'])
            result = {
            "event_id": event_id,
            "name": event["name"],
            "date": event["date"].isoformat(),
            "response": api_data
        }
            f.write(json.dumps(result, indent=4) + "\n")
            f.flush()  # ensure data is written immediately
            # Delay to avoid hitting API rate limits
            time.sleep(1)
    print(f"Results have been continuously dumped to {output_file}")

if __name__ == "__main__":
    main()