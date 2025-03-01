import os
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from dotenv import load_dotenv

def add_ufcstats_event_ids_to_judges_json(judges_json_file, output_file):
    """
    Scrapes UFCStats completed events, filters events after 2022-06-25, then for each event,
    finds the best fuzzy match (by date and location) in the judges JSON data.
    When a match is found, adds the UFCStats event id as "event_id" to that judges event.
    Finally, saves the updated judges events to a new JSON file.
    
    Parameters:
      judges_json_file (str): Path to the input judges JSON file.
      output_file (str): Path to save the updated JSON with event IDs added.
    """
    # --- Step 1. Scrape UFCStats events page ---
    url = "http://ufcstats.com/statistics/events/completed?page=all"
    print("Fetching UFCStats events...")
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"Error fetching UFCStats page: {resp.status_code}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.find_all("tr", class_="b-statistics__table-row")
    
    ufcstats_events = []
    cutoff_date = datetime.strptime("2022-06-25", "%Y-%m-%d")
    
    for row in rows:
        # Find the link containing the event details
        a_tag = row.find("a", class_="b-link")
        if not a_tag:
            continue
        
        event_link = a_tag.get("href", "").strip()  # e.g. "http://ufcstats.com/event-details/80dbeb1dd5b53e64"
        # Extract event id (the part after "/event-details/")
        if "/event-details/" in event_link:
            event_id = event_link.split("/event-details/")[1]
        else:
            continue
        
        event_name = a_tag.get_text(strip=True)
        
        # Extract the event date from the <span class="b-statistics__date">
        date_span = row.find("span", class_="b-statistics__date")
        if not date_span:
            continue
        event_date_str = date_span.get_text(strip=True)  # e.g. "February 01, 2025"
        try:
            event_date = datetime.strptime(event_date_str, "%B %d, %Y")
        except Exception as e:
            print(f"Error parsing date '{event_date_str}': {e}")
            continue
        
        # Only process events after 2022-06-25
        if event_date < cutoff_date:
            continue
        
        # Extract event location from the second <td> with the location info.
        location_td = row.find("td", class_="b-statistics__table-col b-statistics__table-col_style_big-top-padding")
        event_location = location_td.get_text(strip=True) if location_td else ""
        
        ufcstats_events.append({
            "event_id": event_id,
            "event_name": event_name,
            "event_date": event_date,
            "event_date_str": event_date_str,
            "event_location": event_location
        })
    
    print(f"Found {len(ufcstats_events)} UFCStats events after 2022-06-25.")
    
    # --- Step 2. Load the judges JSON file ---
    with open(judges_json_file, "r", encoding="utf-8") as f:
        judges_events = json.load(f)
    
    # --- Step 3. For each UFCStats event, find the best match in judges_events ---
    # We assume each judges event is a dict with an "event_details" block containing:
    #   "date" (format "dd/mm/yyyy") and "location"
    for u_event in ufcstats_events:
        best_match = None
        best_score = -1
        best_date_diff = None
        for j_event in judges_events:
            # Parse the judges event date (assumed to be in "dd/mm/yyyy" format)
            try:
                j_date = datetime.strptime(j_event["event_details"]["date"], "%d/%m/%Y")
            except Exception as e:
                continue
            # Check if the date is within 1 day difference
            date_diff = abs((u_event["event_date"] - j_date).days)
            if date_diff <= 1:
                # Compute fuzzy match score on the location strings
                j_location = j_event["event_details"].get("location", "")
                score = fuzz.token_set_ratio(u_event["event_location"], j_location)
                if score > best_score:
                    best_score = score
                    best_match = j_event
                    best_date_diff = date_diff
        
        if best_match is not None:
            # Add the UFCStats event_id to the judges event
            best_match["event_id"] = u_event["event_id"]
            print(f"Matched UFCStats event '{u_event['event_name']}' on {u_event['event_date_str']} "
                  f"with judges event '{best_match['event_details'].get('name', 'Unknown')}' "
                  f"(fuzzy score: {best_score}, date diff: {best_date_diff} day(s))")
        else:
            print(f"No close match found for UFCStats event '{u_event['event_name']}' on {u_event['event_date_str']}'.")
    
    # --- Step 4. Save the updated judges events JSON ---
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(judges_events, f, indent=2)
    print(f"Updated judges events with UFCStats event IDs saved to '{output_file}'.")


# Example usage:
if __name__ == "__main__":
    # Path to your existing judges JSON file (e.g., judges_2022_2025.json)
    input_judges_file = "judges_2022_2025.json"
    output_judges_file = "judges_2022_2025_with_ids.json"
    
    add_ufcstats_event_ids_to_judges_json(input_judges_file, output_judges_file)
