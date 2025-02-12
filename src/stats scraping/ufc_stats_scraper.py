import re
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from scrape_bio import scrape_fighter_stats
from scrape_event import main as scrape_event_main  # assume scrape_event_main(event_url) handles an individual event

class UFCStatsScraper:
    def __init__(self,
                 upcoming_url: str = "http://ufcstats.com/statistics/events/upcoming",
                 completed_url: str = "http://ufcstats.com/statistics/events/completed?page=all",
                 user_agent: str = (
                     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/90.0.4430.212 Safari/537.36"
                 )):
        self.upcoming_url = upcoming_url
        self.completed_url = completed_url
        self.headers = {"User-Agent": user_agent}

    def _fetch_page(self, url: str) -> BeautifulSoup:
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def _get_event_urls_from_soup(self, soup: BeautifulSoup) -> list:
        """Extracts event URLs from the soup by searching for <a> tags with the appropriate class."""
        event_urls = []
        links = soup.find_all("a", class_="b-link b-link_style_black")
        for link in links:
            href = link.get("href", "")
            if "event-details" in href:
                event_urls.append(href.strip())
        return event_urls

    def _get_filtered_previous_event_urls(self, soup: BeautifulSoup, cutoff: datetime = None) -> list:
        """
        Extracts event URLs from completed events page,
        filtering those with event dates older than the specified cutoff.
        If cutoff is None, defaults to current date.
        """
        if cutoff is None:
            cutoff = datetime.today()
        filtered = []
        rows = soup.find_all("tr", class_="b-statistics__table-row")
        for row in rows:
            date_span = row.find("span", class_="b-statistics__date")
            if date_span:
                date_str = date_span.get_text(strip=True)
                try:
                    event_date = datetime.strptime(date_str, "%B %d, %Y")
                except ValueError:
                    continue  # skip on parsing error
                if event_date <= cutoff:
                    link = row.find("a", class_="b-link b-link_style_black")
                    if link:
                        href = link.get("href", "")
                        if "event-details" in href:
                            filtered.append((href.strip(), event_date))
        return filtered

    def get_upcoming(self):
        """
        Scrapes the upcoming events page.
        Calls scrape_event_main for each event URL found.
        """
        soup = self._fetch_page(self.upcoming_url)
        event_urls = self._get_event_urls_from_soup(soup)
        print(f"Found {len(event_urls)} upcoming events.")
        for url in event_urls:
            print(f"Scraping upcoming event: {url}")
            scrape_event_main(url)

    def get_latest(self):
        """
        Scrapes the completed events page and picks the most recent completed event.
        It does so by filtering event rows by date and selecting the event with
        the maximum (most recent) date. Then it calls scrape_event_main on that event.
        """
        soup = self._fetch_page(self.completed_url)
        events = self._get_filtered_previous_event_urls(soup)
        if not events:
            print("No previous events found.")
            return

        # Sort events by date descending (most recent first)
        events.sort(key=lambda x: x[1], reverse=True)
        most_recent_event, event_date = events[0]
        print(f"Scraping most recent completed event from {event_date.strftime('%Y-%m-%d')}: {most_recent_event}")
        scrape_event_main(most_recent_event)

    def get_fighter_stats(self, fighter_id: str) -> dict:
        """
        Retrieves fighter statistics by processing the fighter details page.
        The fighter_id is appended to the base URL to form:
            http://ufcstats.com/fighter-details/{fighter_id}
        This method calls scrape_fighter_stats from scrape_bio.py.
        """
        fighter_url = f"http://ufcstats.com/fighter-details/{fighter_id}"
        print(f"Fetching stats for fighter: {fighter_url}")
        return scrape_fighter_stats(fighter_url)

# Example usage:
if __name__ == "__main__":
    scraper = UFCStatsScraper()

    # print(scraper.get_fighter_stats("0d7b51c9d2649a6e"))  # Example fighter ID

    # # To pull all upcoming events:
    # scraper.get_upcoming()

    # # To pull the most recent completed event:
    # scraper.get_latest()