# mvp
ODDS/MATE MVP Development

## Source Files

### Data Collection
- [src/pull_upcoming.py](src/pull_upcoming.py) - Fetches upcoming UFC events and fight cards
- [src/scrape_event.py](src/scrape_event.py) - Scrapes complete event data including all fights
- [src/scrape_totals.py](src/scrape_totals.py) - Collects fight statistics and totals
- [src/scrape_round.py](src/scrape_round.py) - Gathers round-by-round fight statistics
- [src/scrape_bio.py](src/scrape_bio.py) - Extracts fighter biographical information
- [src/parse_events.py](src/parse_events.py) - Processes and parses event data into structured format


## Setup

### Prerequisites
- Python 3.9+
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
pip install -r requirements.txt
