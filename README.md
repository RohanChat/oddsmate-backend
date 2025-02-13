# mvp
ODDS/MATE MVP Development

## Source Files

### Data Collection

Judges Scraping:
- [src/judges_scraping/mmadecisions_scraper.py](src/judges_scraping/mmadecisions_scraper.py) - Creates a scraper that can asynchronously or synchronously pull MMA data



Odds Scraping:
- [src/odds_scraping/live_odds.py](src/stats_scraping/pull_upcoming.py)Connects to a Live Odds API and pulls from it.



Stats Scraping: 
- [src/stats_scraping/pull_upcoming.py](src/stats_scraping/pull_upcoming.py) - Fetches upcoming UFC events and fight cards
- [src/stats_scraping/scrape_event.py](src/stats_scraping/scrape_event.py) - Scrapes complete event data including all fights
- [src/stats_scraping/scrape_totals.py](src/stats_scraping/scrape_totals.py) - Collects fight statistics and totals
- [src/stats_scraping/scrape_round.py](src/stats_scraping/scrape_round.py) - Gathers round-by-round fight statistics
- [src/stats_scraping/scrape_bio.py](src/stats_scraping/scrape_bio.py) - Extracts fighter biographical information
- [src/stats_scraping/parse_events.py](src/stats_scraping/parse_events.py) - Processes and parses event data into structured format
- [src/stats_scraping/espn_scraper.py](src/stats_scraping/espn_scraper.py) - Creates an ESPNScraperObject to fetch data from ESPN. Can fetch live data or other historical events.
- [src/stats_scraping/ufc_stats_scraper.py](src/stats_scraping/ufc_stats_scraper.py) - Creates an UFCStatsScraper to fetch data from UFC stats. Can fetch live data or other historical events.


## Setup

### Prerequisites
- Python 3.11+
- Chrome/Chromium browser
- Mac OS X 10.15+

### Installation
```bash
# Clone repository
git clone https://github.com/username/oddsmate-backend.git
cd oddsmate-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
python3.11 -m pip install -r requirements.txt
playwright install 