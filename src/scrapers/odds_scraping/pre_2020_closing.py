import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
import json

"""
This script is designed to obtain the closing odds lines for all fights that occurred before 2020.
It aggregates data by scraping UFC event pages and pulling from existing CSV datasets—compiled fight odds,
outcomes odds, and additional uncleaned data—which have been collated from various sources. The script
parses event and fight details, extracts and converts odds from multiple bookmakers, merges them into a
unified structure, and finally writes the results to a JSON file for further processing or analysis.
"""

# ==============================
# Utility Functions
# ==============================

def test_csv_parsing(compiled_csv_path, outcomes_csv_path):
    # Read the CSV files
    compiled_df = pd.read_csv(compiled_csv_path)
    outcomes_df = pd.read_csv(outcomes_csv_path)
    
    # Print the first few rows for inspection
    print("=== Compiled Fight Odds CSV (head) ===")
    print(compiled_df.head(5))
    print("\nUnique dates in 'Date' column (compiled):")
    print(compiled_df['Date'].unique())
    
    print("\n=== Odds With Outcomes CSV (head) ===")
    print(outcomes_df.head(5))
    print("\nUnique dates in 'Card_Date' column (outcomes):")
    print(outcomes_df['Card_Date'].unique())

def extract_event_id(event_url):
    """
    Given an event URL like "http://ufcstats.com/event-details/39f68882def7a507",
    return the substring after "event-details/".
    """
    m = re.search(r"/event-details/([a-zA-Z0-9]+)", event_url)
    if m:
        return m.group(1)
    return ""

def american_to_decimal(odds):
    """
    Convert American odds (as a number or string) to decimal odds.
    For positive odds: decimal = (odds/100) + 1.
    For negative odds: decimal = (100/abs(odds)) + 1.
    """
    try:
        odds = float(odds)
    except Exception as e:
        print(f"[DEBUG] american_to_decimal: Cannot convert odds {odds} -> {e}")
        return None
    if odds > 0:
        return (odds / 100) + 1
    elif odds < 0:
        return (100 / abs(odds)) + 1
    else:
        return 1.0

# ==============================
# Parsing Functions for an Event Page
# ==============================

def parse_event_page(event_url):
    """
    Fetch the event page, extract the event date (from the info box)
    and return the date (as an ISO string "YYYY-MM-DD") and the list
    of fight container tags.
    """
    response = requests.get(event_url)
    if response.status_code != 200:
        print(f"[DEBUG] Error fetching event page: {event_url} (status {response.status_code})")
        return None, None

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract event date from the info box
    event_date = None
    info_box = soup.find("div", class_="b-list__info-box b-list__info-box_style_large-width")
    if info_box:
        for li in info_box.find_all("li", class_="b-list__box-list-item"):
            i_tag = li.find("i", class_="b-list__box-item-title")
            if i_tag and "Date:" in i_tag.get_text():
                date_text = li.get_text(strip=True).replace("Date:", "").strip()
                try:
                    parsed_date = datetime.strptime(date_text, "%B %d, %Y")
                    event_date = parsed_date.strftime("%Y-%m-%d")
                    print(f"[DEBUG] Parsed event date: {date_text} -> {event_date}")
                except Exception as e:
                    print(f"[DEBUG] Error parsing event date '{date_text}': {e}")
                break
    else:
        print("[DEBUG] No info box found on event page.")

    # Find all fight containers (rows with a click handler)
    fight_containers = soup.find_all("tr", class_="js-fight-details-click")
    # print(f"[DEBUG] Found {len(fight_containers)} fight containers on the event page.")
    return event_date, fight_containers

def extract_fight_details(fight_tag):
    """
    Given a fight container (<tr>), extract:
      - fight_id: parsed from the URL in the onclick attribute
      - fighter1: first fighter’s name
      - fighter2: second fighter’s name
      - fighter1_url: URL from the first fighter's <a> tag
      - fighter2_url: URL from the second fighter's <a> tag
    """
    fight_id = None
    onclick_attr = fight_tag.get("onclick", "")
    m = re.search(r"doNav\('([^']+)'\)", onclick_attr)
    if m:
        fight_url = m.group(1)
        m2 = re.search(r"fight-details/([a-zA-Z0-9]+)", fight_url)
        if m2:
            fight_id = m2.group(1)
    else:
        print("[DEBUG] Could not parse fight URL from onclick.")

    fighter_names = []
    fighter_urls = []
    fighter_td = fight_tag.find("td", class_="b-fight-details__table-col l-page_align_left")
    if fighter_td:
        fighter_links = fighter_td.find_all("a", class_="b-link b-link_style_black")
        for a in fighter_links:
            name = a.get_text(strip=True)
            url = a.get("href", "").strip()
            if name:
                fighter_names.append(name)
                fighter_urls.append(url)
    if len(fighter_names) < 2:
        print(f"[DEBUG] Could not extract two fighter names from fight container: {fight_tag}")
        return None

    # print(f"[DEBUG] Extracted fight details: fight_id={fight_id}, fighter1='{fighter_names[0]}', fighter2='{fighter_names[1]}'")
    return {
        "fight_id": fight_id,
        "fighter1": fighter_names[0],
        "fighter2": fighter_names[1],
        "fighter1_url": fighter_urls[0] if len(fighter_urls) > 0 else "",
        "fighter2_url": fighter_urls[1] if len(fighter_urls) > 1 else ""
    }

def get_odds_for_fighter(fighter_name, event_date, compiled_df, outcomes_df, fuzzy_threshold=80, tolerance_days=1):
    """
    Given a fighter's name and an event date (as "YYYY-MM-DD"), search for rows in
    compiled_df (with columns "Date" and "Fighter") and outcomes_df (with columns "Card_Date" and "Bet")
    that are within tolerance_days of the event_date and fuzzy match the fighter name.
    
    For rows in compiled_df, convert the odds (assumed to be in American format) to decimal using american_to_decimal().
    For rows in outcomes_df, assume the odds are already in decimal.
    
    Returns a dictionary mapping bookmaker names to the odds value.
    """
    try:
        event_date_dt = datetime.strptime(event_date, "%Y-%m-%d")
    except Exception as e:
        print(f"[DEBUG] Error parsing event date {event_date}: {e}")
        return {}

    # print(f"[DEBUG] Using a date tolerance of {tolerance_days} day(s) for fighter '{fighter_name}'")
    
    def is_date_within(row_date_str, date_format):
        try:
            row_date = datetime.strptime(row_date_str, date_format)
            within = abs((row_date - event_date_dt).days) <= tolerance_days
            return within
        except Exception as e:
            print(f"[DEBUG] Date parsing error for '{row_date_str}': {e}")
            return False

    odds_dict = {}

    # Adjust the list to match your CSV columns:
    bookmakers_columns = ["DraftKings", "BetMGM", "Caesars", "FanDuel", "BetWay", "Book1", "Book2", "Book3"]

    # --- Process compiled_fight_odds.csv ---
    compiled_filtered = compiled_df[compiled_df['Date'].fillna('').apply(lambda x: is_date_within(x, "%Y-%m-%d"))]
    # print(f"[DEBUG] Compiled odds: {len(compiled_filtered)} rows after date filter for fighter '{fighter_name}'")
    for idx, row in compiled_filtered.iterrows():
        fighter_in_row = str(row.get("Fighter", ""))
        score = fuzz.token_set_ratio(fighter_name.lower(), fighter_in_row.lower())
        # print(f"[DEBUG] Compiled row {idx}: Fighter in row: '{fighter_in_row}', match score: {score}")
        if score >= fuzzy_threshold:
            # print(f"[DEBUG] Compiled row {idx} accepted (score {score} >= {fuzzy_threshold}).")
            # print(f"[DEBUG] Available columns in compiled row {idx}: {list(row.index)}")
            for col in bookmakers_columns:
                val = row.get(col, "")
                if pd.notnull(val) and str(val).strip() != "":
                    dec_odds = american_to_decimal(val)
                    # print(f"[DEBUG] Compiled row {idx}, column '{col}': raw value: '{val}', converted: {dec_odds}")
                    if dec_odds is not None:
                        odds_dict[col] = dec_odds
                

    # A separate set of bookmaker columns for outcomes CSV (if needed)
    bookmakers_columns_owo = ["5Dimes", "Bet365", "BetDSI", "BetOnline", "BookMaker", "Bovada", "Intertops", "SportBet", "Pinnacle", "SportsInt", "Sportsbook", "William_H", "meanodds", "meanodds_novig"]

    # --- Process odds_w_outcomes.csv ---
    outcomes_filtered = outcomes_df[outcomes_df['Card_Date'].fillna('').apply(lambda x: is_date_within(x, "%Y-%m-%d"))]
    # print(f"[DEBUG] Outcomes odds: {len(outcomes_filtered)} rows after date filter for fighter '{fighter_name}'")
    for idx, row in outcomes_filtered.iterrows():
        fighter_in_row = str(row.get("Bet", ""))
        score = fuzz.token_set_ratio(fighter_name.lower(), fighter_in_row.lower())
        # print(f"[DEBUG] Outcomes row {idx}: Fighter in row: '{fighter_in_row}', match score: {score}")
        if score >= fuzzy_threshold:
            # print(f"[DEBUG] Outcomes row {idx} accepted (score {score} >= {fuzzy_threshold}).")
            # print(f"[DEBUG] Available columns in outcomes row {idx}: {list(row.index)}")
            for col in bookmakers_columns_owo:
                val = row.get(col, "")
                if pd.notnull(val) and str(val).strip() != "":
                    try:
                        dec_odds = float(val)
                        # print(f"[DEBUG] Outcomes row {idx}, column '{col}': raw value: '{val}', float: {dec_odds}")
                    except ValueError as e:
                        # print(f"[DEBUG] Outcomes row {idx}, column '{col}': ValueError converting '{val}': {e}")
                        continue
                    # Only add if not already present (compiled odds take precedence)
                    if col not in odds_dict:
                        odds_dict[col] = dec_odds
                

    # print(f"[DEBUG] Final odds for fighter '{fighter_name}': {odds_dict}")
    return odds_dict

def merge_fighter_odds(fighter1_name, fighter2_name, fighter1_odds, fighter2_odds):
    """
    Given the odds dictionaries for fighter1 and fighter2,
    merge them into a list of bookmakers (one per bookmaker).
    """
    all_bookmakers = set(list(fighter1_odds.keys()) + list(fighter2_odds.keys()))
    bookmakers_list = []
    for bookmaker in all_bookmakers:
        outcome1 = fighter1_odds.get(bookmaker)
        outcome2 = fighter2_odds.get(bookmaker)
        if outcome1 is None and outcome2 is None:
            continue
        bookmakers_list.append({
            "key": bookmaker.lower(),
            "title": bookmaker,
            "markets": [
                {
                    "key": "h2h",
                    "outcomes": [
                        {"name": fighter1_name, "price": outcome1} if outcome1 is not None else None,
                        {"name": fighter2_name, "price": outcome2} if outcome2 is not None else None
                    ]
                }
            ]
        })
    # Remove any None outcomes from the markets.
    for bookmaker in bookmakers_list:
        for market in bookmaker["markets"]:
            market["outcomes"] = [o for o in market["outcomes"] if o is not None]
    # print(f"[DEBUG] Merged bookmakers: {json.dumps(bookmakers_list, indent=2)}")
    return bookmakers_list

def get_uncleaned_meanodds(fight_id, fighter_url, uncleaned_df):
    """
    Given a fight_id and a fighter_url, look in the uncleaned_df (loaded from UNCLEANED_2.csv)
    for the row where the fight_id is contained in the CSV's "fight_url" column and the
    CSV's "fighter_url" exactly matches the provided fighter_url.
    If found, return the value in the "meanodds_novig" column.
    """
    filtered = uncleaned_df[uncleaned_df["fight_url"].astype(str).str.contains(fight_id)]
    if filtered.empty:
        return None
    filtered = filtered[filtered["fighter_url"] == fighter_url]
    if filtered.empty:
        return None
    return filtered.iloc[0]["meanodds_novig"]

def process_event(event_url, compiled_csv_path, outcomes_csv_path):
    """
    Given an event URL and CSV file paths, process the event page:
      - Extract event date and fight containers.
      - For each fight container, extract fight details (including fighter URLs).
      - Look up odds for each fighter using the CSVs.
      - Additionally, load UNCLEANED_2.csv (from a fixed path) and for each fight,
        find the row where the fight_id is contained in the CSV's "fight_url" column and
        the fighter_url matches the fighter's URL from the event page. If found, retrieve
        the "meanodds_novig" value.
      - Merge all odds into a bookmakers list. For the uncleaned CSV values, add a new bookmaker
        entry with key and title "meanodds_novig".
      - Return a nested JSON object with keys: event_id, name, date, and data (the fights list).
    """
    # Load CSV files (adjust paths as needed)
    compiled_df = pd.read_csv(compiled_csv_path)
    outcomes_df = pd.read_csv(outcomes_csv_path)
    # Load the additional CSV from UNCLEANED_2.csv (fixed path)
    uncleaned_csv_path = "/Users/rohan/Desktop/oddsmate-backend/data/raw/UNCLEANED_2.csv"
    uncleaned_df = pd.read_csv(uncleaned_csv_path)

    event_date, fight_containers = parse_event_page(event_url)
    if event_date is None:
        print("[DEBUG] Event date not found. Exiting process_event.")
        return None

    fights_json = []
    for fight_tag in fight_containers:
        details = extract_fight_details(fight_tag)
        if not details:
            continue
        fighter1_name = details["fighter1"]
        fighter2_name = details["fighter2"]
        fight_id = details["fight_id"]
        fighter1_url = details.get("fighter1_url", "")
        fighter2_url = details.get("fighter2_url", "")

        # Get odds for each fighter from the compiled/outcomes CSVs
        fighter1_odds = get_odds_for_fighter(fighter1_name, event_date, compiled_df, outcomes_df)
        fighter2_odds = get_odds_for_fighter(fighter2_name, event_date, compiled_df, outcomes_df)

        # Merge the odds into bookmakers JSON structure.
        bookmakers = merge_fighter_odds(fighter1_name, fighter2_name, fighter1_odds, fighter2_odds)

        # Now check UNCLEANED_2.csv for additional "meanodds_novig" data
        uncleaned_value1 = get_uncleaned_meanodds(fight_id, fighter1_url, uncleaned_df)
        # print(fighter1_url)
        uncleaned_value2 = get_uncleaned_meanodds(fight_id, fighter2_url, uncleaned_df)
        if uncleaned_value1 is not None or uncleaned_value2 is not None:
            uncleaned_outcomes = []
            if uncleaned_value1 is not None:
                uncleaned_outcomes.append({"name": fighter1_name, "price": float(uncleaned_value1)})
            if uncleaned_value2 is not None:
                uncleaned_outcomes.append({"name": fighter2_name, "price": float(uncleaned_value2)})
            if uncleaned_outcomes:
                # Append a new bookmaker entry for meanodds_novig.
                bookmakers.append({
                    "key": "meanodds_novig",
                    "title": "meanodds_novig",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": uncleaned_outcomes
                        }
                    ]
                })

        fight_json = {
            "fight_id": fight_id,
            "sport_key": "mma_mixed_martial_arts",
            "sport_title": "MMA",
            "commence_time": event_date,  # ISO formatted date (YYYY-MM-DD)
            "bookmakers": bookmakers
        }
        fights_json.append(fight_json)

    # Re-fetch the event page (to extract event name and re-confirm event date)
    response = requests.get(event_url)
    soup = BeautifulSoup(response.text, "html.parser")

    # --- Extract event date from the info box (again) ---
    event_date = None
    info_box = soup.find("div", class_="b-list__info-box b-list__info-box_style_large-width")
    if info_box:
        for li in info_box.find_all("li", class_="b-list__box-list-item"):
            i_tag = li.find("i", class_="b-list__box-item-title")
            if i_tag and "Date:" in i_tag.get_text():
                date_text = li.get_text(strip=True).replace("Date:", "").strip()
                try:
                    parsed_date = datetime.strptime(date_text, "%B %d, %Y")
                    event_date = parsed_date.strftime("%Y-%m-%d")
                    # print(f"[DEBUG] Re-parsed event date: {date_text} -> {event_date}")
                except Exception as e:
                    print(f"[DEBUG] Error parsing event date '{date_text}': {e}")
                break
    else:
        print("[DEBUG] No info box found on event page.")

    # --- Extract event name from the <span class="b-content__title-highlight"> ---
    event_name = ""
    span_title = soup.find("span", class_="b-content__title-highlight")
    if span_title:
        event_name = span_title.get_text(strip=True)
        # print(f"[DEBUG] Extracted event name: {event_name}")
    else:
        print("[DEBUG] Event name not found.")

    event_id = extract_event_id(event_url)

    # Filter out fights with empty bookmakers
    filtered_fights = [fight for fight in fights_json if fight.get("bookmakers") and len(fight.get("bookmakers")) > 0]
    if not filtered_fights:
        print(f"[DEBUG] Event {event_id} - {event_name} on {event_date} has no fights with valid bookmakers.")
        return None

    final_json = {
        "event_id": event_id,
        "name": event_name,
        "date": event_date,
        "data": filtered_fights
    }
    # with open(f"{event_id}.json", "w", encoding="utf-8") as f:
    #     json.dump(final_json, f, indent=2)
    return final_json

def get_all_event_links():
    """
    Scrape http://ufcstats.com/statistics/events/completed?page=all to extract all event URLs,
    their names, and dates. Returns a list of dicts with keys:
      "url", "name", "date_str", and "date_dt" (a datetime object for sorting).
    """
    events_url = "http://ufcstats.com/statistics/events/completed?page=all"
    response = requests.get(events_url)
    if response.status_code != 200:
        print(f"[DEBUG] Error fetching events listing page: {events_url}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.find_all("tr", class_="b-statistics__table-row")
    event_list = []
    for row in rows:
        a_tag = row.find("a", class_="b-link b-link_style_black")
        if not a_tag:
            continue
        event_url = a_tag.get("href", "").strip()
        event_name = a_tag.get_text(strip=True)
        date_span = row.find("span", class_="b-statistics__date")
        event_date_str = date_span.get_text(strip=True) if date_span else ""
        try:
            event_date_dt = datetime.strptime(event_date_str, "%B %d, %Y")
        except Exception as e:
            print(f"[DEBUG] Error parsing event date for event '{event_name}': {e}")
            event_date_dt = None
        event_list.append({
            "url": event_url,
            "name": event_name,
            "date_str": event_date_str,
            "date_dt": event_date_dt
        })
    return event_list

def main():
    # Set your CSV file paths (adjust as needed)
    compiled_csv_path = "/Users/rohan/Desktop/oddsmate-backend/old/data/odds scraping/compiled_fight_odds.csv"
    outcomes_csv_path = "/Users/rohan/Desktop/oddsmate-backend/old/data/odds scraping/odds_w_outcomes.csv"
    # process_event("http://ufcstats.com/event-details/073eee4e62f0d988", compiled_csv_path, outcomes_csv_path)
    # Get all event links from the completed events page.
    events = get_all_event_links()
    # Filter out events with no valid date and sort descending (latest to earliest)
    events_valid = [e for e in events if e["date_dt"] is not None]
    events_sorted = sorted(events_valid, key=lambda x: x["date_dt"], reverse=True)
    # print(f"[DEBUG] Found {len(events_sorted)} events with valid dates.")

    final_events = []  # List of event JSON objects to be written to pre_odds.json

    # Process each event in sorted order.
    for event in events_sorted:
        print(f"[DEBUG] Processing event: {event['name']} on {event['date_str']}")
        event_data = process_event(event["url"], compiled_csv_path, outcomes_csv_path)
        # If event_data is None (i.e. no fights with valid bookmakers), log an exception.
        if event_data is None or not event_data.get("data"):
            with open("exceptions.txt", "a", encoding="utf-8") as ef:
                ef.write(f"Event {event['url']} - {event['name']} on {event['date_str']} has empty or invalid odds.\n")
            print(f"[DEBUG] Skipping event {event['name']} due to empty odds.")
        else:
            final_events.append(event_data)
        # Continuously update the JSON file after processing each event.
        with open("pre_odds.json", "w", encoding="utf-8") as f:
            json.dump(final_events, f, indent=2)
        print(f"[DEBUG] Updated pre_odds.json with {len(final_events)} events.")

if __name__ == "__main__":
    main()
