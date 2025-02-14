import argparse
import os
import sys
import asyncio
from scrapers.stats_scraping.espn_scraper import ESPNHistoricalScrapper, LiveESPNScraper
from scrapers.judges_scraping.mmadecisions_scraper import MMAdecisionsScraper
# from scrapers.stats_scraping.espn_scraper import ESPNStatsScraper, LiveESPNScraper
# from scrapers.odds_scraping.live_odds import LiveOddsListener
from scrapers.stats_scraping.ufc_stats_scraper import UFCStatsScraper

def main():
    """
    Main entry point for the script.
    Can create an ESPNScraper, OddsScraper, UFCScraper or a JudgeScraper
    for historical or upcoming fights 
    """
    parser = argparse.ArgumentParser(description="Run UFC scrapers with different modes.")
    
    parser.add_argument("--scraper", type=str, choices=["ESPN", "ufcstats", "judge", "odds"], 
                        default=os.getenv("SCRAPER_TYPE"), required=True, help="Which scraper to run.")
    
    parser.add_argument("--mode", type=str, choices=["sync", "async"], 
                        default=os.getenv("SCRAPER_MODE"), help="Mode to run the scraper in.")
    
    parser.add_argument("--timeframe", type=str, choices=["upcoming", "latest", "historical"], 
                        default=os.getenv("SCRAPER_TIMEFRAME", "latest"), help="Timeframe for the scraper.")

    args = parser.parse_args()

    if args.scraper == "ESPN":
        if args.mode == "sync":
            ESPNHistoricalScrapper().get_historical_fight_info()
        elif args.mode == "async":
            print("-- Monitoring live fights --")
            asyncio.run(LiveESPNScraper().monitor_fight())
        else:
            sys.exit("Error: ESPN scraper requires a mode.")

    elif args.scraper == "judge":
        scraper = MMAdecisionsScraper(mode=args.mode)
        if args.timeframe == "latest":
            scraper.get_latest_event()
        elif args.timeframe == "historical":
            scraper.get_events_range(int(os.getenv("START_YEAR")), int(os.getenv("END_YEAR")))
        else:
            sys.exit("Error: Invalid timeframe for judge scraper.")

    elif args.scraper == "odds":
        LiveOddsListener().run()

    elif args.scraper == "ufcstats":
        scraper = UFCStatsScraper()
        if args.timeframe == "upcoming":
            scraper.get_upcoming()
        elif args.timeframe == "latest":
            scraper.get_latest()
        else:
            sys.exit("Error: Invalid timeframe for UFCStats scraper.")

if __name__ == "__main__":
    main()
