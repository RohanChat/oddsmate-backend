build:
	docker-compose build --no-cache

build-espn:
	docker-compose build --no-cache espn_historical espn_latest

build-judges:
	docker-compose build --no-cache judges_async_latest judges_sync_latest judges_async_historical judges_async_historical

odds-scraping:
	docker-compose build --no-cache odds_scraping

ufc-historical:
	docker-compose build --no-cache ufc_historical

ufc-latest:
	docker-compose build --no-cache ufc_latest