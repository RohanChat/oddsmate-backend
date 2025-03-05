DROP TABLE IF EXISTS odds_outcomes;
DROP TABLE IF EXISTS odds_markets;
DROP TABLE IF EXISTS bookmakers;
DROP TABLE IF EXISTS odds_events;

CREATE TABLE odds_events (
  odds_event_id TEXT PRIMARY KEY,  -- Unique ID from the odds scraper
  event_id TEXT REFERENCES events(event_id), -- ufc stats event id for the event the odds are for
  fight_id TEXT REFERENCES fights(fight_id), -- ufc stats fight_id from the fights table
  odds_timestamp TIMESTAMPTZ,      -- When the odds snapshot was taken
  sport_key TEXT,
  sport_title TEXT,
  commence_time TIMESTAMPTZ,
  home_team TEXT,                   -- Fighter names in MMA context
  away_team TEXT
);

CREATE TABLE bookmakers (
  bookmaker_id SERIAL PRIMARY KEY,
  bookmaker_key TEXT,
  title TEXT,
  last_update TIMESTAMPTZ,
  link TEXT,
  sid TEXT
);

CREATE TABLE odds_markets (
  market_id SERIAL PRIMARY KEY,
  bookmaker_id INT REFERENCES bookmakers(bookmaker_id),
  market_key TEXT,                  
  last_update TIMESTAMPTZ,
  link TEXT,
  sid TEXT
);

CREATE TABLE odds_outcomes (
  outcome_id SERIAL PRIMARY KEY,
  market_id INT REFERENCES odds_markets(market_id),
  outcome_name TEXT,                
  price NUMERIC,
  link TEXT,
  sid TEXT,
  bet_limit TEXT
);
