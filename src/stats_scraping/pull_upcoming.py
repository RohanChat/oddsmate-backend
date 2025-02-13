import re
import requests
from bs4 import BeautifulSoup

# Import the main function from your existing scrape_event script.
# Make sure scrape_event.py has something like:
#    def main(event_url=None):
#        # ...
from scrape_event import main as scrape_event_main

def main():
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

    print("Found event URLs:", event_urls)

    # Now call your scrape_event.py main function on each
    from scrape_event import main as scrape_event_main
    for event_url in event_urls:
        print(f"Scraping event: {event_url}")
        scrape_event_main(event_url)

if __name__ == "__main__":
    print(main())