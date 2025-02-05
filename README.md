# mvp
ODDS/MATE MVP Development

## Source Files

### Data Collection
- `src/scrape_bio.py`: Extracts fighter biographical data
  - Scrapes height, reach, stance, record
  - Formats data into standardized JSON
  - Uses Playwright for reliable data extraction

- `src/live_python.py`: Real-time fight statistics scraping
  - Monitors live UFC events
  - Collects round-by-round statistics
  - Outputs JSON formatted fight data

- `src/scrape_totals.py`: Fight totals collection
  - Gathers significant strikes, takedowns, control time
  - Processes both fighters' statistics
  - Handles different fight outcome scenarios

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

# Install Playwright
playwright install chromium