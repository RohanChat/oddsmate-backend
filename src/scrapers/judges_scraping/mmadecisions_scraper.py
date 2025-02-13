import json
import os
import datetime
import asyncio

# Import your scraper implementations.
from scrape_judges import SyncJudgeScraper
from fast_scrape_judges import AsyncJudgeScraper

class MMAdecisionsScraper:
    """
    A scraper for MMA Decisions events that delegates either to a synchronous or asynchronous judge scraper.
    
    Depending on the mode ('sync' or 'async'), it calls the appropriate underlying methods.
    """

    def __init__(self, mode: str = "sync"):
        """
        Initialize with the desired mode.

        Args:
            mode (str): Either 'sync' or 'async'.
        """
        self.mode = mode.lower()
        if self.mode == "sync":
            self.judge_scraper = SyncJudgeScraper()
        elif self.mode == "async":
            self.judge_scraper = AsyncJudgeScraper()
        else:
            raise ValueError("Invalid mode. Use 'sync' or 'async'.")

    def get_latest_event(self) -> dict:
        """
        Scrapes and returns the latest event.

        Returns:
            dict: Parsed event data.
        """
        if self.mode == "sync":
            event_data = self.judge_scraper.parse_latest_event()
        else:
            # For async, we run the coroutine in an event loop.
            event_data = asyncio.run(self.judge_scraper.run_latest())
        if event_data is None:
            print("No latest event found.")
        else:
            print("Successfully scraped the latest event.")
        return event_data

    def get_events_range(self, start_year: int, end_year: int) -> list:
        """
        Scrapes events within the specified range of years.

        Args:
            start_year (int): The starting year.
            end_year (int): The ending year.

        Returns:
            list: A list of parsed event data dictionaries.
        """
        if self.mode == "sync":
            events = self.judge_scraper.parse_all_events(start_year=start_year, end_year=end_year)
        else:
            events = asyncio.run(self.judge_scraper.run_all(start_year=start_year, end_year=end_year))
        print(f"Processed {len(events)} events between {start_year} and {end_year}.")
        return events


# -------------------------------------------------------------------------------
# Example usage:
# Change the mode below to "sync" or "async" as desired.
# -------------------------------------------------------------------------------
if __name__ == "__main__":
    # Instantiate MMAdecisionsScraper in either "sync" or "async" mode.
    scraper = MMAdecisionsScraper(mode="sync")  # or mode="async"
    
    # Pull the latest event.
    latest_event = scraper.get_latest_event()
    if latest_event:
        timestamp = datetime.datetime.now().isoformat()
        output_dir = os.path.join(os.path.dirname(__file__), '../../data/raw/judging', timestamp)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "latest_event.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(latest_event, f, indent=2)
    
    # # Pull all events from 2021 down to 2000.
    # start_year, end_year = 2021, 2000
    # events = scraper.get_events_range(start_year, end_year)
    # timestamp = datetime.datetime.now().isoformat()
    # output_dir = os.path.join(os.path.dirname(__file__), '../../data/raw/judging', timestamp)
    # os.makedirs(output_dir, exist_ok=True)
    # output_path = os.path.join(output_dir, f"{start_year}_{end_year}.json")
    # with open(output_path, "w", encoding="utf-8") as f:
    #     json.dump(events, f, indent=2)
