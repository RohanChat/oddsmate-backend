import re
import json
import requests
from bs4 import BeautifulSoup

def process_stat_value(stat_value):
    """
    Convert a stat value string into an appropriate type.
    
    - If the value is in the form "X of Y", return a dict with keys 'landed' and 'attempted'
    - If the value is a time (e.g. "0:53"), convert to total seconds.
    - If the value is a percentage (e.g. "42%"), return a float.
    - Otherwise, try to convert to an integer.
    """
    # Convert dashes to zero
    if stat_value == '---':
        stat_value = '0'
    
    # Check for "X of Y" format
    if ' of ' in stat_value:
        parts = stat_value.split(' of ')
        try:
            landed = int(parts[0])
            attempted = int(parts[1])
        except ValueError:
            landed = parts[0]
            attempted = parts[1]
        return {"landed": landed, "attempted": attempted}
    # Check for time format (e.g. "0:53")
    elif ':' in stat_value:
        try:
            minutes, seconds = stat_value.split(':')
            return int(minutes) * 60 + int(seconds)
        except Exception:
            return stat_value
    # Check for percentage (e.g. "42%")
    elif '%' in stat_value:
        try:
            return float(stat_value.replace('%',''))
        except Exception:
            return stat_value
    else:
        try:
            return int(stat_value)
        except ValueError:
            return stat_value

def scrape_round_by_round_stats(fight_url, fighter_url):
    """
    Given a fight URL and a fighter URL, fetch the fight page and scrape the round-by-round
    statistics for the fighter whose profile URL matches the provided fighter_url.
    
    Two tables are processed:
      - The "totals" table (identified by a "KD" header) which contains overall stats such as:
            "KD", "Sig. str.", "Sig. str. %", "Total str.", "Td", "Td %", "Sub. att", "Rev.", "Ctrl"
      - The "significant strikes" table (identified by a "Head" header) which contains breakdowns:
            "Head", "Body", "Leg", "Distance", "Clinch", "Ground"
    
    The final output for each round is merged into a single dictionary with keys:
      "KD",
      "Sig. str."   -> a dictionary that merges overall ("landed"/"attempted") with the breakdown
      "Sig. str. %",
      "Total str.",
      "Td",
      "Td %",
      "Sub. att",
      "Rev.",
      "Ctrl"
    
    The rounds are keyed as "round1", "round2", etc.
    """
    # This intermediate dictionary will be keyed by round (e.g., "round1") and will store two parts:
    #  - "totals": stats from the totals table
    #  - "breakdown": keys from the significant strikes table (Head, Body, etc.)
    round_data = {}
    
    # This will hold the fighter index (0 or 1) determined by matching fighter URLs
    fighter_index = None

    # Fetch the fight page
    try:
        response = requests.get(fight_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching URL {fight_url}: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all sections that may contain per-round stats
    per_round_sections = soup.find_all('section', class_='b-fight-details__section js-fight-section')
    
    for section in per_round_sections:
        header = section.find('a', class_='b-fight-details__collapse-link_rnd js-fight-collapse-link')
        if header and 'Per round' in header.get_text():
            tables = section.find_all('table', class_='b-fight-details__table')
            for table in tables:
                # Determine table type by looking at header columns.
                header_cells = table.find('thead').find_all('th')
                headers = [th.get_text(strip=True) for th in header_cells]
                if 'KD' in headers:
                    table_type = 'totals'
                    totals_stat_names = [
                        'KD',
                        'Sig. str.',
                        'Sig. str. %',
                        'Total str.',
                        'Td',
                        'Td %',
                        'Sub. att',
                        'Rev.',
                        'Ctrl'
                    ]
                    stat_names = totals_stat_names
                elif 'Head' in headers:
                    table_type = 'significant_strikes'
                    ss_stat_names = [
                        'Sig. str.',
                        'Sig. str. %',
                        'Head',
                        'Body',
                        'Leg',
                        'Distance',
                        'Clinch',
                        'Ground'
                    ]
                    stat_names = ss_stat_names
                else:
                    continue  # Unknown table type, skip

                tbody = table.find('tbody', class_='b-fight-details__table-body')
                if not tbody:
                    continue

                rows = tbody.find_all(['tr', 'thead'])
                current_round = None
                for row in rows:
                    if row.name == 'thead':
                        # Extract the round number from the header (e.g., "Round 1")
                        round_header = row.get_text(strip=True)
                        m = re.search(r'Round\s*(\d+)', round_header, re.IGNORECASE)
                        if m:
                            current_round = m.group(1)
                            round_key = f"round{current_round}"
                            if round_key not in round_data:
                                round_data[round_key] = {"totals": {}, "breakdown": {}}
                        else:
                            continue
                    elif row.name == 'tr' and current_round is not None:
                        cols = row.find_all('td')
                        if len(cols) < 2:
                            continue  # Not enough columns
                        # The first column contains fighter info.
                        fighter_col = cols[0]
                        
                        # If we have not yet determined which fighter to use, try to extract fighter URLs.
                        if fighter_index is None:
                            # Look for <a> tags that link to fighter profiles.
                            fighter_links = fighter_col.find_all('a')
                            fighter_infos = []
                            if fighter_links:
                                for a in fighter_links:
                                    href = a.get('href', '')
                                    name = a.get_text(strip=True)
                                    fighter_infos.append({'name': name, 'url': href})
                            else:
                                # Fallback: if there are no links, grab text from <p> elements.
                                fighter_texts = [p.get_text(strip=True) for p in fighter_col.find_all('p', class_='b-fight-details__table-text')]
                                fighter_infos = [{'name': name, 'url': ''} for name in fighter_texts]
                            
                            # Compare each fighter’s URL with the provided fighter_url.
                            for idx, info in enumerate(fighter_infos):
                                # A simple check: if one URL is a substring of the other (after stripping any trailing slash).
                                if info['url'] and (fighter_url.rstrip('/') in info['url'] or info['url'].rstrip('/') in fighter_url):
                                    fighter_index = idx
                                    break
                            # If no match is found, default to the first fighter.
                            if fighter_index is None:
                                fighter_index = 0

                        # Process the stat columns (each corresponding to one stat in our list).
                        for i, stat_col in enumerate(cols[1:]):
                            # Each column should contain two values (one for each fighter).
                            stat_values = [p.get_text(strip=True) for p in stat_col.find_all('p', class_='b-fight-details__table-text')]
                            if len(stat_values) < fighter_index + 1:
                                continue
                            selected_value = process_stat_value(stat_values[fighter_index])
                            
                            if table_type == 'totals':
                                if i < len(stat_names):
                                    key = stat_names[i]
                                    round_data[round_key]["totals"][key] = selected_value
                            elif table_type == 'significant_strikes':
                                # For the significant strikes table, we only want the breakdown stats.
                                # (Skip the overall "Sig. str." and "Sig. str. %" as these come from the totals table.)
                                if i < len(stat_names):
                                    key = stat_names[i]
                                    if key in ['Head', 'Body', 'Leg', 'Distance', 'Clinch', 'Ground']:
                                        round_data[round_key]["breakdown"][key] = selected_value

    # Now merge the totals and breakdown parts for each round into the final output format.
    final_data = {}
    for round_key, data in round_data.items():
        totals = data.get("totals", {})
        breakdown = data.get("breakdown", {})
        round_final = {}

        # "KD" is taken directly from the totals table.
        round_final["KD"] = totals.get("KD", None)

        # For "Sig. str.", start with the overall (landed/attempted) numbers from totals.
        overall_sig = totals.get("Sig. str.", {})
        if not isinstance(overall_sig, dict):
            overall_sig = {}
        # Then add the breakdown stats.
        overall_sig.update(breakdown)
        round_final["Sig. str."] = overall_sig

        # Add the remaining keys from the totals table.
        for stat in ["Sig. str. %", "Total str.", "Td", "Td %", "Sub. att", "Rev.", "Ctrl"]:
            round_final[stat] = totals.get(stat, None)

        final_data[round_key] = round_final

    return final_data

def main():
    # Replace with the actual fight URL and fighter URL
    fight_url = "http://ufcstats.com/fight-details/f39941b3743bf18c"
    fighter_url = "http://ufcstats.com/fighter-details/c03520b5c88ed6b4"  # Replace with the actual fighter URL
    
    data = scrape_round_by_round_stats(fight_url, fighter_url)
    if data:
        print(json.dumps(data, indent=2))
    else:
        print("No round-by-round data extracted.")

if __name__ == "__main__":
    main()
