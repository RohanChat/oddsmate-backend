import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from unidecode import unidecode
from fuzzywuzzy import fuzz

class SyncJudgeScraper:
    """
    A class-based scraper for MMA Decisions and UFCStats data.
    """

    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0'}

    def parse_fight(self, fight_url):
        """
        Given a fight URL, downloads the page and extracts the fighter names and judges' scorecards.
        Returns a dictionary containing:
         - "fight_url": the URL
         - "fighter1": first fighter’s name (after cleaning)
         - "fighter2": second fighter’s name (after cleaning)
         - "judges": a dictionary where each key (e.g. "Judge1") maps to a dict containing:
                - "judge_name": the judge’s name (cleaned),
                - "rounds": a list of per-round score dictionaries (with keys "round", "fighter1", "fighter2")
                - "total": a dict (if available) with total scores for fighter1 and fighter2.
        """
        response = requests.get(fight_url, headers=self.headers)
        if response.status_code != 200:
            print(f"Failed to retrieve fight page: {fight_url} (status code {response.status_code})")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # --- Extract fighter names ---
        fighter_cells = soup.find_all('td', class_=['decision-top', 'decision-bottom'])
        fighter_names = []
        for cell in fighter_cells:
            a_tag = cell.find('a')
            if a_tag:
                fighter_names.append(unidecode(a_tag.get_text(strip=True)))
        if len(fighter_names) >= 2:
            fighter1, fighter2 = fighter_names[:2]
        else:
            fighter1, fighter2 = "", ""
            print(f"Could not extract both fighter names from {fight_url}")

        # --- Extract judges' scorecards ---
        judges_tables = soup.find_all('table', {'style': 'border-spacing: 1px; width: 100%'})
        if len(judges_tables) < 3:
            print(f"Expected at least 3 judges tables but found {len(judges_tables)} in {fight_url}")
            return None

        judges_results = {}
        for idx, table in enumerate(judges_tables[:3], start=1):
            judge_cell = table.find('td', class_='judge')
            if not judge_cell:
                print(f"Judge cell not found in table {idx} on {fight_url}")
                continue
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
                # Skip a round if scores are missing
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

            # Overall total scores (if available)
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

    def get_ufcstats_events(self):
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
            event_date_str = date_span.get_text(strip=True)
            try:
                event_date = datetime.strptime(event_date_str, "%B %d, %Y")
            except Exception as e:
                print(f"Error parsing UFCStats event date '{event_date_str}': {e}")
                continue

            location_td = row.find(
                "td", 
                class_="b-statistics__table-col b-statistics__table-col_style_big-top-padding"
            )
            event_location = location_td.get_text(strip=True) if location_td else ""
            events.append({
                "event_id": event_id,
                "event_name": event_name,
                "event_date": event_date,
                "event_date_str": event_date_str,
                "event_location": event_location
            })
        return events

    def parse_event(self, event_url):
        """
        Given an MMA Decisions event URL, downloads the event page, extracts the event details
        (name, date, location) from the designated container, finds all fight URLs,
        and calls `parse_fight` on each one.
        
        Then, it also scrapes the UFCStats completed events page, finds the closest fuzzy match
        for this event (first by date within ±1 day, then by fuzzy matching the event location),
        and adds the matched UFCStats event's id into the returned JSON as "event_id" 
        (inserted before "fights").
        
        Returns a dictionary containing:
         - "event_url": the MMA Decisions event URL
         - "event_details": a dict with keys "name", "date", "location"
         - "event_id": (if found) the matched UFCStats event id
         - "fights": a list of fight data dictionaries (as returned by parse_fight)
        """
        response = requests.get(event_url, headers=self.headers)
        if response.status_code != 200:
            print(f"Failed to retrieve event page: {event_url} (status code {response.status_code})")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        event_info = {}
        # --- Extract event details ---
        top_row = soup.find('tr', class_='top-row')
        if top_row:
            td = top_row.find('td', class_='decision-top2')
            if td:
                parts = list(td.stripped_strings)
                if parts:
                    event_info['name'] = parts[0]
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

        bottom_row = soup.find('tr', class_='bottom-row')
        if bottom_row:
            td_date = bottom_row.find('td', class_='decision-bottom2')
            if td_date:
                date_str = td_date.get_text(strip=True)
                try:
                    parsed_date = datetime.strptime(date_str, "%B %d, %Y")
                    event_info['date'] = parsed_date.strftime("%d/%m/%Y")
                except Exception as e:
                    print(f"Date parsing error for '{date_str}': {e}")
                    event_info['date'] = date_str
            else:
                event_info['date'] = ""
        else:
            event_info['date'] = ""

        # --- Find all fight URLs ---
        fight_links = []
        fight_cells = soup.find_all('td', class_='list2')
        for cell in fight_cells:
            a_tag = cell.find('a', href=True)
            if a_tag and a_tag['href'].strip().startswith('decision/'):
                full_url = urljoin('https://mmadecisions.com/', a_tag['href'].strip())
                fight_links.append(full_url)
        fight_links = list(set(fight_links))

        fights_data = []
        for fight_url in fight_links:
            fight_data = self.parse_fight(fight_url)
            if fight_data:
                fights_data.append(fight_data)

        # --- Attempt to find matching UFCStats event ---
        matched_event_id = None
        try:
            event_date = datetime.strptime(event_info.get("date", ""), "%d/%m/%Y")
        except Exception as e:
            print(f"Error parsing MMA Decisions event date '{event_info.get('date', '')}': {e}")
            event_date = None

        event_name = event_info['name']
        if 'UFC' in event_name:
            if event_date:
                ufc_events = self.get_ufcstats_events()
                best_score = -1
                for u_event in ufc_events:
                    # Check if UFCStats event date is within ±1 day
                    date_diff = abs((u_event["event_date"] - event_date).days)
                    if date_diff <= 1:
                        # Fuzzy match on location
                        score = fuzz.token_set_ratio(
                            u_event["event_location"], 
                            event_info.get("location", "")
                        )
                        if score > best_score:
                            best_score = score
                            matched_event_id = u_event["event_id"]
                if matched_event_id:
                    print(
                        f"Matched UFCStats event id {matched_event_id} "
                        f"(fuzzy score: {best_score}) for MMA Decisions event '{event_info.get('name', '')}'"
                    )
                else:
                    print(f"No close UFCStats match found for MMA Decisions event '{event_info.get('name', '')}'")
            else:
                print("MMA Decisions event date unavailable; skipping UFCStats matching.")

        # --- Build final event data ---
        event_data = {
            "event_url": event_url,
            "event_details": event_info
        }
        if matched_event_id:
            event_data["event_id"] = matched_event_id
        event_data["fights"] = fights_data

        return event_data

    def parse_all_events(self, start_year=2025, end_year=2000):
        """
        Iterates through the "decisions-by-event" pages for each year (from start_year down to end_year)
        and processes every event found on each page.
        
        Returns a list of event data dictionaries (as returned by parse_event).
        """
        base_url = "https://mmadecisions.com/decisions-by-event/"
        all_events = []
        for year in range(start_year, end_year - 1, -1):
            year_url = f"{base_url}{year}/"
            print(f"\n--- Processing events for year: {year} ---")
            response = requests.get(year_url, headers=self.headers)
            if response.status_code != 200:
                print(f"Failed to retrieve events page for {year} (status code {response.status_code})")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
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
                    event_data = self.parse_event(full_event_url)
                    if event_data:
                        all_events.append(event_data)
        return all_events

    def parse_latest_event(self):
        """
        Fetches and parses just the first/latest event from mmadecisions.com
        Returns the parsed event data dictionary.
        """
        base_url = "https://mmadecisions.com/decisions-by-event/"
        response = requests.get(base_url, headers=self.headers)
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
                return self.parse_event(full_event_url)
        
        print("No events found")
        return None

    def main(self):
        """
        Example main method that parses the latest event
        and writes the result to a JSON file based on 'event_id'.
        """
        event_data = self.parse_latest_event()
        if event_data:
            # If there's no matched 'event_id', we'll fallback to a generic filename.
            filename = event_data.get("event_id", "latest_event") + ".json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(event_data, f, indent=2)
            print(f"Saved latest event data to '{filename}'.")
        else:
            print("No event data to save.")


if __name__ == "__main__":
    # Example usage:
    scraper = SyncJudgeScraper()

    # 1) Parse just the latest event and save JSON.
    scraper.main()

    # 2) Alternatively, parse all events in a given range of years:
    # all_events_data = scraper.parse_all_events(start_year=2021, end_year=1994)
    # with open("all_events.json", "w", encoding="utf-8") as f:
    #     json.dump(all_events_data, f, indent=4)
    # print(f"\nProcessed {len(all_events_data)} events from 2021 down to 1994.")
