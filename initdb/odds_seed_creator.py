import os
import re
import json

##############################################
# Global Aggregation Structures & Counters
##############################################

# Accumulate odds_events keyed by odds_event_id.
global_odds_events = {}  # { odds_event_id: { ...fields... } }

# Deduplicate bookmakers globally by bookmaker_key.
global_bookmakers = {}   # { bookmaker_key: { ...fields..., bookmaker_id } }

# Deduplicate markets by (bookmaker_id, market_key)
global_markets = {}      # { (bookmaker_id, market_key): { ...fields..., market_id } }

# Deduplicate outcomes by (market_id, outcome_name)
global_outcomes = {}     # { (market_id, outcome_name): { ...fields..., outcome_id } }

# Counters for assigning new IDs (simulate SERIAL).
bookmaker_counter = 1
market_counter = 1
outcome_counter = 1

##############################################
# Helper Functions
##############################################

def sanitize(value):
    """Escape single quotes for SQL."""
    if isinstance(value, str):
        return value.replace("'", "''")
    return value

def sql_value(val, is_text=True):
    """Return SQL-safe representation: wrap strings in quotes, or return NULL if empty."""
    if val is None or val == "":
        return "NULL"
    if is_text:
        return f"'{sanitize(str(val))}'"
    return str(val)

def parse_json_objects(filepath):
    """
    Extract complete JSON objects from a file that may be in JSONL format.
    Accumulates lines until braces are balanced.
    """
    objects = []
    current_lines = []
    open_braces = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            current_lines.append(line)
            open_braces += line.count('{')
            open_braces -= line.count('}')
            if open_braces == 0 and current_lines:
                block = "".join(current_lines)
                try:
                    obj = json.loads(block)
                    objects.append(obj)
                except Exception as e:
                    print(f"Error parsing JSON block in {filepath}: {e}")
                current_lines = []
    return objects

##############################################
# Odds Data Processing
##############################################

def process_odds_event_record(odds_event, parent_meta):
    """
    Process one odds event record:
      - Synthesize odds_event_id if missing (using fight_id + "_" + event_id)
      - Add/update odds_events
      - Process bookmakers globally by bookmaker_key.
      - Process markets (assumed one type, e.g. "h2h") deduplicated per bookmaker.
      - Process outcomes deduplicated per market by outcome name.
    """
    global global_odds_events, global_bookmakers, global_markets, global_outcomes
    global bookmaker_counter, market_counter, outcome_counter

    # Determine odds_event_id. If missing, synthesize it as fight_id + "_" + event_id.
    odds_event_id = odds_event.get("id", "")
    if not odds_event_id:
        fight_id = odds_event.get("fight_id", "")
        event_id = parent_meta.get("event_id", "")
        odds_event_id = f"{fight_id}_{event_id}"
    
    # Insert odds_event (if not already recorded)
    if odds_event_id not in global_odds_events:
        # Get odds_timestamp from parent metadata if available.
        ts = ""
        if "timestamp" in parent_meta:
            ts = parent_meta["timestamp"]
        elif "response" in parent_meta and "timestamp" in parent_meta["response"]:
            ts = parent_meta["response"]["timestamp"]
        global_odds_events[odds_event_id] = {
            "odds_event_id": odds_event_id,
            "event_id": parent_meta.get("event_id", ""),
            "fight_id": odds_event.get("fight_id", ""),
            "odds_timestamp": ts,
            "sport_key": odds_event.get("sport_key", ""),
            "sport_title": odds_event.get("sport_title", ""),
            "commence_time": odds_event.get("commence_time", ""),
            "home_team": odds_event.get("home_team", ""),
            "away_team": odds_event.get("away_team", "")
        }
    
    # Process bookmakers for this odds event.
    bookmakers = odds_event.get("bookmakers", [])
    for bookmaker in bookmakers:
        bookmaker_key = bookmaker.get("key", "")
        # Global deduplication: use bookmaker_key only.
        if bookmaker_key not in global_bookmakers:
            # Use the odds_event_id from the first occurrence.
            global_bookmakers[bookmaker_key] = {
                "bookmaker_id": bookmaker_counter,
                "odds_event_id": odds_event_id,
                "bookmaker_key": bookmaker_key,
                "title": bookmaker.get("title", ""),
                "last_update": bookmaker.get("last_update", ""),
                "link": bookmaker.get("link", ""),
                "sid": bookmaker.get("sid", "")
            }
            assigned_bookmaker_id = bookmaker_counter
            bookmaker_counter += 1
        else:
            assigned_bookmaker_id = global_bookmakers[bookmaker_key]["bookmaker_id"]

        # Process markets for this bookmaker. (For now, assume only "h2h" exists.)
        markets = bookmaker.get("markets", [])
        for market in markets:
            market_key = market.get("key", "")
            mk_key = (assigned_bookmaker_id, market_key)
            if mk_key not in global_markets:
                global_markets[mk_key] = {
                    "market_id": market_counter,
                    "bookmaker_id": assigned_bookmaker_id,
                    "market_key": market_key,
                    "last_update": market.get("last_update", ""),
                    "link": market.get("link", ""),
                    "sid": market.get("sid", "")
                }
                assigned_market_id = market_counter
                market_counter += 1
            else:
                assigned_market_id = global_markets[mk_key]["market_id"]

            # Process outcomes for this market.
            outcomes = market.get("outcomes", [])
            for outcome in outcomes:
                outcome_name = outcome.get("name", "")
                out_key = (assigned_market_id, outcome_name)
                if out_key not in global_outcomes:
                    global_outcomes[out_key] = {
                        "outcome_id": outcome_counter,
                        "market_id": assigned_market_id,
                        "outcome_name": outcome_name,
                        "price": outcome.get("price", "NULL"),
                        "link": outcome.get("link", ""),
                        "sid": outcome.get("sid", ""),
                        "bet_limit": outcome.get("bet_limit", "")
                    }
                    outcome_counter += 1
                # If duplicate, skip.

##############################################
# File Processing Functions
##############################################

def process_pre_odds_file(filepath):
    """
    Process a JSON file (like pre_odds.json) containing an array of events.
    Each event has "event_id", "name", "date", and a "data" array with odds events.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            events = json.load(f)
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
            return
    for event in events:
        parent_event_id = event.get("event_id", "")
        parent_name = event.get("name", "unknown_event")
        parent_meta = {"event_id": parent_event_id, "name": parent_name}
        data = event.get("data", [])
        for odds_event in data:
            process_odds_event_record(odds_event, parent_meta)

def process_jsonl_file(filepath):
    """
    Process a JSONL file. Uses parse_json_objects to extract JSON objects.
    Handles two possible structures:
      - Odds references: top-level "response" with a "data" array.
      - Processed events: top-level "timestamp" and "data" keys.
    """
    objs = parse_json_objects(filepath)
    for obj in objs:
        if "response" in obj:
            parent_event_id = obj.get("event_id", "")
            parent_name = obj.get("name", "unknown_event")
            parent_meta = {"event_id": parent_event_id, "name": parent_name, "response": obj.get("response", {})}
            for odds_event in obj.get("response", {}).get("data", []):
                process_odds_event_record(odds_event, parent_meta)
        elif "timestamp" in obj and "data" in obj:
            parent_meta = {"timestamp": obj.get("timestamp", "")}
            for odds_event in obj.get("data", []):
                process_odds_event_record(odds_event, parent_meta)
        else:
            print(f"Unrecognized JSON structure in {filepath}: {obj}")

##############################################
# Write Output SQL Files (One per Table)
##############################################

def write_sql_files(output_dir):
    # odds_events.sql
    events_file = os.path.join(output_dir, "odds_events.sql")
    with open(events_file, 'w', encoding='utf-8') as f:
        f.write("-- Insert statements for odds_events\n")
        for oe in global_odds_events.values():
            f.write(
                "INSERT INTO odds_events (odds_event_id, event_id, fight_id, odds_timestamp, sport_key, sport_title, commence_time, home_team, away_team) VALUES ("
                f"{sql_value(oe['odds_event_id'])}, {sql_value(oe['event_id'])}, {sql_value(oe['fight_id'])}, {sql_value(oe['odds_timestamp'])}, {sql_value(oe['sport_key'])}, {sql_value(oe['sport_title'])}, {sql_value(oe['commence_time'])}, {sql_value(oe['home_team'])}, {sql_value(oe['away_team'])}"
                ");\n"
            )
    print(f"Wrote {events_file}")

    # bookmakers.sql
    bookmakers_file = os.path.join(output_dir, "bookmakers.sql")
    with open(bookmakers_file, 'w', encoding='utf-8') as f:
        f.write("-- Insert statements for bookmakers\n")
        for bm in global_bookmakers.values():
            f.write(
                "INSERT INTO bookmakers (bookmaker_id, odds_event_id, bookmaker_key, title, last_update, link, sid) VALUES ("
                f"{bm['bookmaker_id']}, {sql_value(bm['odds_event_id'])}, {sql_value(bm['bookmaker_key'])}, {sql_value(bm['title'])}, {sql_value(bm['last_update'])}, {sql_value(bm['link'])}, {sql_value(bm['sid'])}"
                ");\n"
            )
    print(f"Wrote {bookmakers_file}")

    # odds_markets.sql
    markets_file = os.path.join(output_dir, "odds_markets.sql")
    with open(markets_file, 'w', encoding='utf-8') as f:
        f.write("-- Insert statements for odds_markets\n")
        for mk in global_markets.values():
            f.write(
                "INSERT INTO odds_markets (market_id, bookmaker_id, market_key, last_update, link, sid) VALUES ("
                f"{mk['market_id']}, {mk['bookmaker_id']}, {sql_value(mk['market_key'])}, {sql_value(mk['last_update'])}, {sql_value(mk['link'])}, {sql_value(mk['sid'])}"
                ");\n"
            )
    print(f"Wrote {markets_file}")

    # odds_outcomes.sql
    outcomes_file = os.path.join(output_dir, "odds_outcomes.sql")
    with open(outcomes_file, 'w', encoding='utf-8') as f:
        f.write("-- Insert statements for odds_outcomes\n")
        for oc in global_outcomes.values():
            f.write(
                "INSERT INTO odds_outcomes (outcome_id, market_id, outcome_name, price, link, sid, bet_limit) VALUES ("
                f"{oc['outcome_id']}, {oc['market_id']}, {sql_value(oc['outcome_name'])}, {oc['price']}, {sql_value(oc['link'])}, {sql_value(oc['sid'])}, {sql_value(oc['bet_limit'])}"
                ");\n"
            )
    print(f"Wrote {outcomes_file}")

##############################################
# Main Function: Process Files and Write SQL
##############################################

def main():
    input_dir = "./data/raw/odds/"
    output_dir = "./initdb/seed/odds/"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for root, dirs, files in os.walk(input_dir):
        for file in files:
            filepath = os.path.join(root, file)
            if file.lower().endswith(".json"):
                print(f"Processing JSON file: {filepath}")
                process_pre_odds_file(filepath)
            elif file.lower().endswith(".jsonl"):
                print(f"Processing JSONL file: {filepath}")
                process_jsonl_file(filepath)
    
    write_sql_files(output_dir)

if __name__ == "__main__":
    main()
