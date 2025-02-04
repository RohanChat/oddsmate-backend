import re
import json
import requests
from bs4 import BeautifulSoup

# Import the main function from your existing scrape_event script.
# Make sure scrape_event.py has something like:
#    def main(event_url=None):
#        # ...
#
# Then you can do:
from scrape_event import main as scrape_event_main

def get_event_urls(all_completed_url):
    """
    Fetch the completed events page and return a list of event URLs.
    Each event link is in an <a> tag with class "b-link b-link_style_black"
    and href like http://ufcstats.com/event-details/xxxxxx
    """
    response = requests.get(all_completed_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    event_urls = []
    links = soup.find_all("a", class_="b-link b-link_style_black")
    for link in links:
        href = link.get("href", "")
        # We only want those that match /event-details/<id>
        if "event-details" in href:
            event_urls.append(href.strip())
    return event_urls

def extract_event_id(event_url):
    """
    Given an event URL like "http://ufcstats.com/event-details/39f68882def7a507",
    return the substring after "event-details/".
    """
    m = re.search(r"/event-details/([a-zA-Z0-9]+)", event_url)
    if m:
        return m.group(1)
    return ""

def main():
    # This is the URL that lists all completed events (with pagination).
    all_completed_url = "http://ufcstats.com/statistics/events/completed?page=all"
    
    # 1. Gather all event URLs from that page.
    event_urls = get_event_urls(all_completed_url)
    
    # 2. For each event URL, run scrape_event_main(event_url).
    #    Meanwhile, build a list of the event ids.
    event_ids = []
    for url in event_urls:
        # Run the main function from scrape_event.py on this URL.
        # This call presumably handles all your per-event scraping and JSON output
        # or any other logic you have in scrape_event.py.
        scrape_event_main(url)
        
        # Extract the event id from the URL and add to our list for final JSON output
        evt_id = extract_event_id(url)
        if evt_id:
            event_ids.append(evt_id)

    # 3. Build a JSON object with the structure:
    #    {
    #      "completed_events": [
    #         "39f68882def7a507",
    #         "12ab34cdef561234",
    #         ...
    #      ]
    #    }
    final_json = {
        "completed_events": event_ids
    }
    
    # 4. Print or return the final JSON
    return json.dumps(final_json, indent=2)

if __name__ == "__main__":
    print(main())
