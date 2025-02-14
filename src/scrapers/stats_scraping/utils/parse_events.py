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
from .scrape_event import main as scrape_event_main
from datetime import datetime

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
    filtered_event_urls = []
    # Find each row corresponding to an event.
    rows = soup.find_all("tr", class_="b-statistics__table-row")
    cutoff_date = datetime(2021, 1, 15)
    for row in rows:
        date_span = row.find("span", class_="b-statistics__date")
        if date_span:
            date_str = date_span.get_text(strip=True)
            try:
                event_date = datetime.strptime(date_str, "%B %d, %Y")
            except ValueError:
                continue  # skip if date format is unexpected
            if event_date <= cutoff_date:
                link = row.find("a", class_="b-link b-link_style_black")
                if link:
                    href = link.get("href", "")
                    if "event-details" in href:
                        filtered_event_urls.append(href.strip())

    return filtered_event_urls

def extract_event_id(event_url):
    """
    Given an event URL like "http://ufcstats.com/event-details/39f68882def7a507",
    return the substring after "event-details/".
    """
    m = re.search(r"/event-details/([a-zA-Z0-9]+)", event_url)
    if m:
        return m.group(1)
    return ""

def pull_upcoming_events():
    url = "http://ufcstats.com/statistics/events/upcoming"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/90.0.4430.212 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Print the HTML to see if the events are even there
    # print(soup.prettify())

    # Gather event URLs by row
    rows = soup.find_all("tr", class_="b-statistics__table-row")
    event_urls = []
    for row in rows:
        link = row.find("a", class_="b-link b-link_style_black")
        if link:
            href = link.get("href", "")
            if "event-details" in href:
                event_urls.append(href.strip())

    # Now call your scrape_event.py main function on each
    for event_url in event_urls:
        # print(f"Scraping event: {event_url}")
        scrape_event_main(event_url)

def main():
    # This is the URL that lists all completed events (with pagination).
    # all_completed_url = "http://ufcstats.com/statistics/events/completed?page=all"
    
    # # 1. Gather all event URLs from that page.
    # event_urls = get_event_urls(all_completed_url)
    
    # # 2. For each event URL, run scrape_event_main(event_url).
    # #    Meanwhile, build a list of the event ids.
    # event_ids = []
    # for url in event_urls:
    #     # Run the main function from scrape_event.py on this URL.
    #     # This call presumably handles all your per-event scraping and JSON output
    #     # or any other logic you have in scrape_event.py.
    #     scrape_event_main(url)
        
    #     # Extract the event id from the URL and add to our list for final JSON output
    #     evt_id = extract_event_id(url)
    #     if evt_id:
    #         event_ids.append(evt_id)

    # 3. Build a JSON object with the structure:
    #    {
    #      "completed_events": [
    #         "39f68882def7a507",
    #         "12ab34cdef561234",
    #         ...
    #      ]
    #    }
    # final_json = {
    #     "completed_events": event_ids
    # }
    
    # with open("stats_scrape.json", "w") as f:
    #     f.write(json.dumps(final_json, indent=2))

    # # 4. Print or return the final JSON
    # return json.dumps(final_json, indent=2)
    pull_upcoming_events()


if __name__ == "__main__":
    print(main())
