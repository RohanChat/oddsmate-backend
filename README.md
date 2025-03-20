# ODDS/MATE MMA MVP Backend
A data collection, processing, and analytics engine for MMA statistics, fight scores, and betting odds. Built with Python, PostgreSQL, and Docker.

## Architecture
The backend for this MVP is built using a containerised architecture with:

- Docker-based microservices for data collection and processing
- PostgreSQL database for structured data storage
- SQLAlchemy ORM for object-based database interactions
- Repository pattern for clean data access abstraction

### Key Components
- Data Collection Services: Multiple scrapers for different data sources
- Database Layer: Object-oriented models and repositories
- API Interface: Access to processed fight data and analytics

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Git
- Python 3.11+ (for local development)

### Installation

#### 1. Clone repository
git clone https://github.com/username/oddsmate-backend.git  
cd oddsmate-backend  

#### 2. Start the database only
docker-compose up -d postgres_db

#### 3. Start all services
docker-compose up -d

## Project Structure 

oddsmate-backend/  
├── src/  
│   ├── db/  
│   │   ├── models/          # SQLAlchemy ORM models  
│   │   ├── repository/      # Repository pattern implementations  
│   │   ├── base.py          # SQLAlchemy base class  
│   │   └── session.py       # Database connection management  
│   ├── judges_scraping/     # Judges and scoring data scrapers  
│   ├── stats_scraping/      # Fight statistics scrapers  
│   ├── odds_scraping/       # Betting odds scrapers  
│   └── main.py              # Entry point for scrapers  
├── tests/                   # Test suite  
├── initdb/                  # Database initialization scripts  
├── Dockerfiles/             # Docker build configurations  
├── compose.yml              # Docker Compose service definitions  
└── .env                     # Environment configuration  
  
## Data Collection Services

### UFC Stats Service
Collects fight statistics, fighter profiles, and event information from UFC's official stats provider.  

Run UFC stats scraper only:  
docker-compose up -d ufc_latest

### ESPN Service
Gathers fight data, live statistics, and event details from ESPN.  

Run ESPN scraper for historical data:  
docker-compose up -d espn_historical  

### Judges & Scoring Service
Collects official judges' scorecards and decision information  

Run judges sync for latest events:  
docker-compose up -d judges_sync_latest  

### Odds Service
Collects betting odds from theoddsapi connection  

## Database Model

The project uses an object-relational mapping (ORM) approach with SQLAlchemy, providing clean object-based interactions with the database instead of raw SQL.  

#### Core Entities

- Events: UFC/MMA events with location and date information
- Fighters: Athlete profiles and career statistics
- Fights: Individual bouts with results and method information
- Fight Stats: Detailed statistics for each fighter in a fight
- Round Stats: Round-by-round statistics
- Judges: Information about fight judges
- Scoring: Official scorecards from judges
- Odds: Betting odds from multiple bookmakers

#### Repository Pattern
The database layer follows the repository pattern, providing a clean abstraction over data access operations:  

Example: Retrieving a fighter with the repository pattern
from src.db.repository import FighterRepository:  

Get fighter by ID:  
fighter = FighterRepository.get_by_id("123")  

Get a fighter's recent fights:  
recent_fights = FighterRepository.get_fighter_history("123", limit=5)  

## Development

### Local Setup

#### 1. Create virtual environment
python -m venv venv  
source venv/bin/activate  

#### 2. Install dependencies
pip install -r requirements.txt  
playwright install  

#### 3. Set up environment variables (Edit .env with your credentials)
cp .env.example .env  

#### 4. Run a specific scraper locally, eg:
python src/main.py --scraper espn --mode sync --timeframe latest  