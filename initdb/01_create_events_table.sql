-- Drop tables if they exist (for development purposes)
DROP TABLE IF EXISTS events;

-- Create events table
CREATE TABLE events (
  event_id TEXT PRIMARY KEY,
  date DATE NOT NULL,
  name TEXT NOT NULL,
  location_name TEXT,
  location POINT NOT NULL,
  elevation NUMERIC,
  event_url TEXT
);