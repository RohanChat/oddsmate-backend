import json
import os, datetime
from scrape_judges import parse_latest_event, parse_all_events  # reuse the existing methods

class MMAdecisionsScraper:
    """
    A scraper for MMA Decisions events.
    
    Provides two main methods:
      - get_latest_event(): Processes and returns the latest event.
      - get_events_range(start_year, end_year): Processes events between the given years.
    """
    
    def __init__(self):
        # You can add additional configuration options if needed.
        pass

    def get_latest_event(self) -> dict:
        """
        Scrapes and returns the latest event.
        
        Returns:
            dict: Parsed event data from parse_latest_event().
        """
        event_data = parse_latest_event()
        if event_data is None:
            print("No latest event found.")
        else:
            print("Successfully scraped the latest event.")
        return event_data

    def get_events_range(self, start_year: int, end_year: int) -> list:
        """
        Scrapes events within the specified range of years.
        
        Args:
            start_year (int): The starting year for scraping.
            end_year (int): The ending year for scraping.

        Returns:
            list: A list of parsed event data dictionaries.
        """
        events = parse_all_events(start_year=start_year, end_year=end_year)
        print(f"Processed {len(events)} events between {start_year} and {end_year}.")
        return events

# Example usage:
if __name__ == "__main__":
    scraper = MMAdecisionsScraper()
    
    # Pull the latest event.
    latest_event = scraper.get_latest_event()
    if latest_event:
        timestamp = datetime.datetime.now().isoformat()
        output_dir = os.path.join(os.path.dirname(__file__), '../../data/raw/judging', timestamp)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "latest_event.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(latest_event, f, indent=2)
    
    # Pull all events from 2021 down to 2000.
    start_year, end_year = 2021, 2000
    events = scraper.get_events_range(start_year, end_year)
    timestamp = datetime.datetime.now().isoformat()
    output_dir = os.path.join(os.path.dirname(__file__), '../../data/raw/judging', timestamp)
    output_path = os.path.join(output_dir, f"{start_year}_{end_year}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)