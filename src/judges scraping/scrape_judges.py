import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
from datetime import datetime
from unidecode import unidecode
from fuzzywuzzy import fuzz

# =============================================================================
# 1. Function to parse a fight page and output judges' scores (JSON‑ready)
# =============================================================================
def parse_fight(fight_url):
    """
    Given a fight URL, downloads the page and extracts the fighter names and judges' scorecards.
    Returns a dictionary containing:
      - "fight_url": the URL
      - "fighter1": first fighter’s name (after cleaning)
      - "fighter2": second fighter’s name (after cleaning)
      - "judges": a dictionary where each key (e.g. "Judge1") maps to a dict containing:
            - "judge_name": the judge’s name (cleaned),
            - "rounds": a list of per‑round score dictionaries (with keys "round", "fighter1", "fighter2")
            - "total": a dict (if available) with total scores for fighter1 and fighter2.
    """
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(fight_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve fight page: {fight_url} (status code {response.status_code})")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    # --- Extract fighter names ---
    # Fighter names are usually in cells with classes 'decision-top' and 'decision-bottom'
    fighter_cells = soup.find_all('td', class_=['decision-top', 'decision-bottom'])
    fighter_names = []
    for cell in fighter_cells:
        a_tag = cell.find('a')
        if a_tag:
            # Use unidecode to clean the name (this replaces non-breaking spaces, etc.)
            fighter_names.append(unidecode(a_tag.get_text(strip=True)))
    if len(fighter_names) >= 2:
        fighter1, fighter2 = fighter_names[:2]
    else:
        fighter1, fighter2 = "", ""
        print(f"Could not extract both fighter names from {fight_url}")

    # --- Extract judges' scorecards ---
    # Judge tables are identified by a specific style.
    judges_tables = soup.find_all('table', {'style': 'border-spacing: 1px; width: 100%'})
    if len(judges_tables) < 3:
        print(f"Expected at least 3 judges tables but found {len(judges_tables)} in {fight_url}")
        return None

    judges_results = {}
    # Process (up to) the first three tables as the three judges’ scorecards.
    for idx, table in enumerate(judges_tables[:3], start=1):
        judge_cell = table.find('td', class_='judge')
        if not judge_cell:
            print(f"Judge cell not found in table {idx} on {fight_url}")
            continue
        # Clean the judge's name using unidecode.
        judge_name = unidecode(judge_cell.get_text(strip=True).split('\n')[0])

        rounds_data = []
        round_rows = table.find_all('tr', class_='decision')
        for row in round_rows:
            cells = row.find_all('td')
            if len(cells) < 3:
                continue
            round_num = cells[0].get_text(strip=True)
            score_f1 = cells[1].get_text(strip=True)
            score_f2 = cells[2].get_text(strip=True)
            # Skip a round if scores are missing (e.g. shown as '-')
            if score_f1 == '-' or score_f2 == '-':
                continue
            try:
                score_f1 = int(score_f1)
                score_f2 = int(score_f2)
            except ValueError:
                continue

            rounds_data.append({
                "round": round_num,
                "fighter1": score_f1,
                "fighter2": score_f2
            })

        # Also try to get the overall total scores if available (from a row with class "bottom-row")
        totals = {}
        total_row = table.find('tr', class_='bottom-row')
        if total_row:
            total_cells = total_row.find_all('td')
            if len(total_cells) >= 3:
                total_f1 = total_cells[1].get_text(strip=True)
                total_f2 = total_cells[2].get_text(strip=True)
                try:
                    total_f1 = int(total_f1)
                    total_f2 = int(total_f2)
                    totals = {"fighter1": total_f1, "fighter2": total_f2}
                except ValueError:
                    totals = {}

        judges_results[f"Judge{idx}"] = {
            "judge_name": judge_name,
            "rounds": rounds_data,
            "total": totals
        }

    fight_data = {
        "fight_url": fight_url,
        "fighter1": fighter1,
        "fighter2": fighter2,
        "judges": judges_results
    }
    return fight_data


# -------------------------------
# Helper: Scrape UFCStats events
# -------------------------------
def get_ufcstats_events():
    """
    Scrapes the UFCStats completed events page and returns a list of event dictionaries.
    Each dictionary has:
      - event_id (extracted from the URL)
      - event_name
      - event_date (a datetime object)
      - event_date_str (original string, e.g. "February 01, 2025")
      - event_location
    """
    url = "http://ufcstats.com/statistics/events/completed?page=all"
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"Error fetching UFCStats events page: {resp.status_code}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.find_all("tr", class_="b-statistics__table-row")
    events = []
    for row in rows:
        a_tag = row.find("a", class_="b-link")
        if not a_tag:
            continue
        event_link = a_tag.get("href", "").strip()
        if "/event-details/" not in event_link:
            continue
        event_id = event_link.split("/event-details/")[1]
        event_name = a_tag.get_text(strip=True)
        date_span = row.find("span", class_="b-statistics__date")
        if not date_span:
            continue
        event_date_str = date_span.get_text(strip=True)  # e.g. "February 01, 2025"
        try:
            event_date = datetime.strptime(event_date_str, "%B %d, %Y")
        except Exception as e:
            print(f"Error parsing UFCStats event date '{event_date_str}': {e}")
            continue
        location_td = row.find("td", class_="b-statistics__table-col b-statistics__table-col_style_big-top-padding")
        event_location = location_td.get_text(strip=True) if location_td else ""
        events.append({
            "event_id": event_id,
            "event_name": event_name,
            "event_date": event_date,
            "event_date_str": event_date_str,
            "event_location": event_location
        })
    return events

# -------------------------------
# Main Function: parse_event
# -------------------------------
def parse_event(event_url):
    """
    Given an MMA Decisions event URL, downloads the event page, extracts the event details
    (name, date, location) from the designated container, finds all fight URLs,
    and calls `parse_fight` on each one.
    
    Then, it also scrapes the UFCStats completed events page, finds the closest fuzzy match
    for this event (first by date within ±1 day, then by fuzzy matching the event location),
    and adds the matched UFCStats event's id into the returned JSON as "event_id" (inserted before "fights").
    
    Returns a dictionary containing:
      - "event_url": the MMA Decisions event URL
      - "event_details": a dict with keys "name", "date", "location"
      - "event_id": (if found) the matched UFCStats event id
      - "fights": a list of fight data dictionaries (as returned by parse_fight)
    """
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(event_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve event page: {event_url} (status code {response.status_code})")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    event_info = {}
    # --- Extract event details from the container with class "decision-top2" ---
    top_row = soup.find('tr', class_='top-row')
    if top_row:
        td = top_row.find('td', class_='decision-top2')
        if td:
            # Use stripped_strings to get a list of text elements.
            parts = list(td.stripped_strings)
            if parts:
                # The first part is the event name.
                event_info['name'] = parts[0]
                # The remaining parts are the location.
                if len(parts) > 1:
                    event_info['location'] = ", ".join(parts[1:])
                else:
                    event_info['location'] = ""
            else:
                event_info['name'] = ""
                event_info['location'] = ""
    else:
        event_info['name'] = ""
        event_info['location'] = ""

    # --- Extract and reformat the event date ---
    bottom_row = soup.find('tr', class_='bottom-row')
    if bottom_row:
        td_date = bottom_row.find('td', class_='decision-bottom2')
        if td_date:
            date_str = td_date.get_text(strip=True)
            try:
                # Expecting a date like "February 01, 2025"
                parsed_date = datetime.strptime(date_str, "%B %d, %Y")
                # Format date as dd/mm/yyyy
                event_info['date'] = parsed_date.strftime("%d/%m/%Y")
            except Exception as e:
                print(f"Date parsing error for '{date_str}': {e}")
                event_info['date'] = date_str
        else:
            event_info['date'] = ""
    else:
        event_info['date'] = ""

    # --- Find all fight URLs in this event page ---
    fight_links = []
    fight_cells = soup.find_all('td', class_='list2')
    for cell in fight_cells:
        a_tag = cell.find('a', href=True)
        if a_tag and a_tag['href'].strip().startswith('decision/'):
            full_url = urljoin('https://mmadecisions.com/', a_tag['href'].strip())
            fight_links.append(full_url)
    # Remove duplicates (if any)
    fight_links = list(set(fight_links))

    fights_data = []
    for fight_url in fight_links:
        fight_data = parse_fight(fight_url)
        if fight_data:
            fights_data.append(fight_data)

    # --- New: Find closest matching UFCStats event ---
    matched_event_id = None
    try:
        # Convert event_info date ("dd/mm/yyyy") into a datetime object.
        event_date = datetime.strptime(event_info.get("date", ""), "%d/%m/%Y")
    except Exception as e:
        print(f"Error parsing MMA Decisions event date '{event_info.get('date', '')}': {e}")
        event_date = None

    event_name = event_info['name']
    if 'UFC' in event_name:

        if event_date:
            ufc_events = get_ufcstats_events()
            best_score = -1
            for u_event in ufc_events:
                # Check if UFCStats event date is within ±1 day of the MMA Decisions event date.
                date_diff = abs((u_event["event_date"] - event_date).days)
                if date_diff <= 1:
                    # Fuzzy match on the event location.
                    score = fuzz.token_set_ratio(u_event["event_location"], event_info.get("location", ""))
                    if score > best_score:
                        best_score = score
                        matched_event_id = u_event["event_id"]
            if matched_event_id:
                print(f"Matched UFCStats event id {matched_event_id} (fuzzy score: {best_score}) for MMA Decisions event '{event_info.get('name', '')}'")
            else:
                print(f"No close UFCStats match found for MMA Decisions event '{event_info.get('name', '')}'")
        else:
            print("MMA Decisions event date unavailable; skipping UFCStats matching.")

    # --- Build event_data with the new "event_id" inserted before "fights" ---
    event_data = {
        "event_url": event_url,
        "event_details": event_info
    }
    if matched_event_id:
        event_data["event_id"] = matched_event_id
    event_data["fights"] = fights_data

    return event_data


# =============================================================================
# 3. Function to loop through all event URLs (from a yearly listing) and process each event
# =============================================================================
def parse_all_events(start_year=2025, end_year=2000):
    """
    Iterates through the "decisions-by-event" pages for each year (from start_year down to end_year)
    and processes every event found on each page.
    
    Returns a list of event data dictionaries (as returned by parse_event).
    """
    base_url = "https://mmadecisions.com/decisions-by-event/"
    all_events = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for year in range(start_year, end_year - 1, -1):
        year_url = f"{base_url}{year}/"
        print(f"\n--- Processing events for year: {year} ---")
        response = requests.get(year_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve events page for {year} (status code {response.status_code})")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        # In the yearly page, event rows have class "decision".
        event_rows = soup.find_all('tr', class_='decision')
        for row in event_rows:
            event_cell = row.find('td', class_='list')
            if not event_cell:
                continue
            a_tag = event_cell.find('a', href=True)
            if a_tag:
                event_href = a_tag['href'].strip()
                full_event_url = urljoin('https://mmadecisions.com/', event_href)
                print(f"Found event URL: {full_event_url}")
                event_data = parse_event(full_event_url)
                if event_data:
                    all_events.append(event_data)
    return all_events

def parse_latest_event():
    """
    Fetches and parses just the first/latest event from mmadecisions.com
    Returns the parsed event data dictionary
    """
    base_url = "https://mmadecisions.com/decisions-by-event/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Get the main events listing page
    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve events page (status code {response.status_code})")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find first event row
    event_row = soup.find('tr', class_='decision')
    if event_row:
        event_cell = event_row.find('td', class_='list')
        if event_cell and event_cell.find('a', href=True):
            event_href = event_cell.find('a', href=True)['href'].strip()
            full_event_url = urljoin('https://mmadecisions.com/', event_href)
            print(f"Processing latest event: {full_event_url}")
            return parse_event(full_event_url)
    
    print("No events found")
    return None

def main():
    event_data = parse_latest_event()
    if event_data:
        with open(event_data["event_id"] + '.json', 'w') as f:
            json.dump(event_data, f, indent=2)

if __name__ == "__main__":
    main()

# # =============================================================================
# # Example usage:
# # You can test the functions individually.
# # -----------------------------------------------------------------------------
# if __name__ == "__main__":
#     # # Example 1: Parse a single fight page and output the results as JSON.
#     # test_fight_url = "https://mmadecisions.com/decision/9521/Jesus-Pinedo-vs-Devin-Powell"  # Replace with a valid fight URL
#     # fight_result = parse_fight(test_fight_url)
#     # if fight_result:
#     #     print("\n--- Fight Result ---")
#     #     print(json.dumps(fight_result, indent=4))

#     # # Example 2: Parse a single event page.
#     # test_event_url = "https://mmadecisions.com/event/5/UFC-5-The-Return-of-the-Beast"  # Replace with a valid event URL
#     # event_result = parse_event(test_event_url)
#     # if event_result:
#     #     print("\n--- Event Result ---")
#     #     print(json.dumps(event_result, indent=4))

    # Example 3: Process all events from 2025 down to 2023 (for a shorter test run).
    # (Adjust the years as desired.)
    all_events = parse_all_events(start_year=2021, end_year=1994)
    print(f"\nProcessed {len(all_events)} events from 2025 to 2023.")
    # Optionally, you could save all_events as JSON:
    with open("all_events.json", "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=4)
