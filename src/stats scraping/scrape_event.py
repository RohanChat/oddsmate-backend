from dotenv import load_dotenv
import os

load_dotenv()

import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import scrape_totals

# --- Configuration: Replace these with your own API keys ---
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_KEY")
GOOGLE_ELEVATION_API_KEY = os.getenv("GOOGLE_KEY")

# --- Helper Functions ---

def get_coordinates(location_name):
    """
    Use the Google Places API to retrieve coordinates for a given location name.
    """
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": location_name,
        "inputtype": "textquery",
        "fields": "geometry",
        "key": GOOGLE_PLACES_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data.get("status") == "OK" and data.get("candidates"):
        geometry = data["candidates"][0]["geometry"]["location"]
        return geometry  # Example: {"lat": 24.7136, "lng": 46.6753}
    return None

def get_elevation(lat, lng):
    """
    Use the Google Maps Elevation API to get the elevation (in meters) for the given coordinates.
    """
    url = "https://maps.googleapis.com/maps/api/elevation/json"
    params = {
        "locations": f"{lat},{lng}",
        "key": GOOGLE_ELEVATION_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data.get("status") == "OK" and data.get("results"):
        return data["results"][0].get("elevation")
    return None

def extract_event_info(soup):
    """
    Extract the event date and location from the event page.
    The date and location are found in <li class="b-list__box-list-item"> elements.
    """
    event_date = None
    event_location = None
    list_items = soup.find_all("li", class_="b-list__box-list-item")
    for li in list_items:
        title_elem = li.find("i", class_="b-list__box-item-title")
        if title_elem:
            title = title_elem.get_text(strip=True).rstrip(":").lower()
            full_text = li.get_text(" ", strip=True)
            if title == "date":
                # Remove the "Date:" label from the full text.
                event_date = full_text.replace("Date:", "").strip()
            elif title == "location":
                event_location = full_text.replace("Location:", "").strip()
    return event_date, event_location

def format_date(date_str):
    """
    Convert a date string (e.g. "February 01, 2025") into ISO format ("YYYY-MM-DD").
    """
    try:
        dt = datetime.strptime(date_str, "%B %d, %Y")
        return dt.strftime("%Y-%m-%d")
    except Exception as e:
        return date_str

def extract_fight_ids(soup):
    """
    Look for all fight rows in the event page and extract the fight ids.
    Each fight row is in a <tr> tag with class:
      "b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click"
    and the fight URL is stored in the onclick attribute as:
      doNav('http://ufcstats.com/fight-details/85e79748b75eb30e')
    """
    fight_ids = []
    rows = soup.find_all("tr", class_="b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click")
    for row in rows:
        onclick = row.get("onclick", "")
        # Extract the URL from the onclick attribute.
        m = re.search(r"doNav\('([^']+)'\)", onclick)
        if m:
            fight_url = m.group(1)
            # Extract the fight id (the part after "fight-details/").
            m_id = re.search(r"fight-details/([a-zA-Z0-9]+)", fight_url)
            if m_id:
                fight_ids.append(m_id.group(1))
    return fight_ids

# --- Main Script ---

def main(event_url="http://ufcstats.com/event-details/9fd1f08dd4aec14a"):
    
    # Extract event id from the URL (the part after "event-details/")
    m = re.search(r"event-details/([a-zA-Z0-9]+)", event_url)
    event_id = m.group(1) if m else ""
    
    # Fetch the event page
    response = requests.get(event_url)
    response.raise_for_status()
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    
    # Extract event date and location from the page
    raw_date, location_name = extract_event_info(soup)
    formatted_date = format_date(raw_date) if raw_date else ""
    
    # Get coordinates for the location (using Google Places API)
    coordinates = get_coordinates(location_name) if location_name else None
    lat = coordinates.get("lat") if coordinates else None
    lng = coordinates.get("lng") if coordinates else None
    
    # Get elevation using the coordinates (using Google Maps Elevation API)
    elevation = get_elevation(lat, lng) if (lat is not None and lng is not None) else None
    
    # Extract all fight ids from the event page.
    fight_ids = extract_fight_ids(soup)
    
    # Build the final JSON object.
    output = {
        "event_id": event_id,
        "date": formatted_date,
        "location": {
            "name": location_name,
            "coordinates": coordinates,   # Will be None if not found; otherwise a dict with "lat" and "lng"
            "elevation": elevation
        },
        "fights": [
            scrape_totals.main(f"http://ufcstats.com/fight-details/{fight_id}")
            for fight_id in fight_ids
        ]
        # "fights_ids": fight_ids  # A list of fight ids (the parts after "fight-details/")
    }
    
    # Output the JSON
    print(json.dumps(output, indent=2))
    with open(f"{event_id}.json", "w") as json_file:
        json.dump(output, json_file, indent=2)
    return json.dumps(output, indent=2)


if __name__ == "__main__":
    print(main())

