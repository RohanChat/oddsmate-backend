import os
import re
import json
import requests
from bs4 import BeautifulSoup

# Assume these functions are implemented in your modules.
from scrape_bio import scrape_fighter_stats       # should accept a fighter URL and return a dict
from scrape_round import scrape_round_by_round_stats   # should accept (fight_url, fighter_url) and return a dict
from scrape_pre_comp import scrape_precomp_stats   # should accept (fight_url, fighter_url) and return a dict

# --- Helper functions for extracting data from the fight page ---

def parse_x_of_y(text):
    """
    If text is of the form "X of Y", return a dict { "landed": X, "attempted": Y }.
    Otherwise, return the stripped text.
    """
    m = re.search(r'(\d+)\s*of\s*(\d+)', text)
    if m:
        return {"landed": int(m.group(1)), "attempted": int(m.group(2))}
    return text.strip()

def extract_fighter_info(soup):
    """
    Extract fighter names, URLs, win/loss results and nicknames.
    Returns a list of two dictionaries.
    """
    fighters = []
    persons_div = soup.find("div", class_="b-fight-details__persons")
    if persons_div:
        for fighter_div in persons_div.find_all("div", class_="b-fight-details__person"):
            status_elem = fighter_div.find("i", class_=re.compile("b-fight-details__person-status"))
            status = status_elem.get_text(strip=True) if status_elem else ""
            name_elem = fighter_div.find("h3", class_="b-fight-details__person-name")
            link = name_elem.find("a") if name_elem else None
            name = link.get_text(strip=True) if link else ""
            url = link.get("href") if link else ""
            nickname_elem = fighter_div.find("p", class_="b-fight-details__person-title")
            nickname = nickname_elem.get_text(strip=True) if nickname_elem else ""
            fighters.append({
                "name": name,
                "url": url,
                "result": status,
                "nickname": nickname
            })
    return fighters

def extract_fight_details(soup):
    """
    Extract overall fight details (method, round, time, time format, referee and judge details).
    """
    details = {}
    content_div = soup.find("div", class_="b-fight-details__content")
    if content_div:
        text_items = content_div.find_all("i", class_=re.compile("b-fight-details__text-item"))
        for item in text_items:
            label_elem = item.find("i", class_="b-fight-details__label")
            if label_elem:
                label = label_elem.get_text(strip=True).rstrip(":").lower()
                value_parts = []
                for sibling in label_elem.next_siblings:
                    if isinstance(sibling, str):
                        value_parts.append(sibling.strip())
                    else:
                        value_parts.append(sibling.get_text(strip=True))
                value = " ".join([v for v in value_parts if v]).strip()
                if label == "method":
                    details["method"] = value
                elif label == "round":
                    details["round"] = value
                elif label == "time":
                    details["time"] = value
                elif label == "time format":
                    details["time_format"] = value
                elif label == "referee":
                    details["referee"] = value
                elif label == "details":
                    judge_details = []
                    for sibling in item.find_next_siblings("i"):
                        judge_name = ""
                        span = sibling.find("span")
                        if span:
                            judge_name = span.get_text(strip=True)
                        detail_text = sibling.get_text(" ", strip=True)
                        if judge_name:
                            detail_text = detail_text.replace(judge_name, "").strip()
                        judge_details.append({"judge": judge_name, "score": detail_text})
                    details["details"] = judge_details
    return details

def parse_stat_cell(cell):
    """
    Given a table cell that might contain one or two <p> elements (one per fighter),
    return a list of values. If the text is of the form “X of Y”, it is converted to a dict.
    """
    results = []
    for p in cell.find_all("p"):
        txt = p.get_text(strip=True)
        results.append(parse_x_of_y(txt))
    return results

def extract_table_data(table):
    """
    Extract data from a table that has a single row with cells containing one or two values.
    Returns a list with two dictionaries (one per fighter).
    """
    header_cells = table.find("thead").find_all("th")
    headers = [h.get_text(strip=True) for h in header_cells]
    fighter_data = [{}, {}]
    tbody = table.find("tbody")
    if tbody:
        row = tbody.find("tr")
        if row:
            cells = row.find_all("td")
            for idx, cell in enumerate(cells):
                values = parse_stat_cell(cell)
                for fighter_index, value in enumerate(values):
                    header = headers[idx]
                    if isinstance(value, dict):
                        fighter_data[fighter_index][f"{header}_landed"] = value.get("landed")
                        fighter_data[fighter_index][f"{header}_attempted"] = value.get("attempted")
                    else:
                        fighter_data[fighter_index][header] = value
    return fighter_data

def extract_per_round_data(table):
    """
    Extract per-round stats from tables that include multiple round sections.
    Returns a list of rounds (each round is a dict with the round number and fighter data).
    """
    rounds = []
    tbody = table.find("tbody")
    if not tbody:
        return rounds
    current_round = None
    for child in tbody.children:
        if child.name == "thead":
            round_label = child.get_text(strip=True)
            m = re.search(r'Round\s*(\d+)', round_label, re.IGNORECASE)
            if m:
                current_round = m.group(1)
        elif child.name == "tr" and current_round:
            cells = child.find_all("td")
            fighter_stats = [{}, {}]
            for idx, cell in enumerate(cells):
                values = parse_stat_cell(cell)
                header = f"col_{idx}"
                for i, value in enumerate(values):
                    if isinstance(value, dict):
                        fighter_stats[i][f"{header}_landed"] = value.get("landed")
                        fighter_stats[i][f"{header}_attempted"] = value.get("attempted")
                    else:
                        fighter_stats[i][header] = value
            rounds.append({"round": current_round, "data": fighter_stats})
            current_round = None
    return rounds

def extract_all_tables(soup):
    """
    Look for sections containing the Totals and Significant Strikes tables (both overall and per round).
    Returns a dictionary with keys:
      - "totals" (overall totals data)
      - "significant_strikes" (overall significant strikes data)
      - (plus per round tables if needed)
    """
    results = {}
    sections = soup.find_all("section", class_="b-fight-details__section")
    for sec in sections:
        text = sec.get_text(" ", strip=True)
        # Overall Totals table
        if "Totals" in text and sec.find("p", class_=re.compile("b-fight-details__collapse-link_tot")):
            table = sec.find_next("table")
            if table:
                results["totals"] = extract_table_data(table)
        # Overall Significant Strikes table
        if "Significant Strikes" in text and sec.find("p", class_=re.compile("b-fight-details__collapse-link_tot")):
            table = sec.find_next("table")
            if table:
                results["significant_strikes"] = extract_table_data(table)
        # (Per-round tables can be extracted similarly if needed.)
    return results

# --- Main scraper function that builds the new JSON structure ---

def main(fight_url = "http://ufcstats.com/fight-details/358f816aff469270", output_dir =os.path.join(os.path.dirname(__file__), "../../data/raw/stats/event_dumps/")):
    # Replace with the actual fight URL you want to scrape.
    
    
    # Fetch the fight page.
    response = requests.get(fight_url)
    response.raise_for_status()
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Extract the fight id (the part after "fight-details/")
    fight_id = None
    m = re.search(r'fight-details/([a-zA-Z0-9]+)', fight_url)
    if m:
        fight_id = m.group(1)
    
    # 2. Extract fighter information and overall fight details.
    fighters = extract_fighter_info(soup)        # list of two fighter dictionaries
    fight_details = extract_fight_details(soup)    # overall fight details
    tables = extract_all_tables(soup)              # overall stats tables
    # Expect totals and significant strikes as lists (one per fighter)
    totals = tables.get("totals", [None, None])
    sig_strikes = tables.get("significant_strikes", [None, None])
    
    # 3. Build the top-level JSON object.
    final_output = {
        "fight_id": fight_id,
        "method": fight_details.get("method", ""),
        "round": fight_details.get("round", ""),
        "time": fight_details.get("time", ""),
        "time_format": fight_details.get("time_format", ""),
        "referee": fight_details.get("referee", ""),
        "details": fight_details.get("details", [])
    }
    
    # 4. Process each fighter (fighter1 and fighter2).
    for i in range(2):
        fighter_info = fighters[i] if i < len(fighters) else {}
        fighter_url = fighter_info.get("url", "")
        
        # Run the external bio and round scrapers.
        bio_data = scrape_fighter_stats(fighter_url)             # assumed to return a dict of fighter bio info
        round_data = scrape_round_by_round_stats(fight_url, fighter_url) # assumed to return round-by-round stats as a dict
        pre_comp_data = scrape_precomp_stats(fight_url, fighter_url) # assumed to return pre-comp stats as a dict

        # Get overall fight stats from the Totals and Significant Strikes tables.
        tot = totals[i] if totals and len(totals) > i and totals[i] is not None else {}
        sig = sig_strikes[i] if sig_strikes and len(sig_strikes) > i and sig_strikes[i] is not None else {}
        
        # Build a dictionary for the fighter.
        fighter_data = {}
        # Merge bio info.
        fighter_data.update(bio_data)
        # Add the win/loss result.
        fighter_data["result"] = fighter_info.get("result", "")
        
        # --- Overall fight stats ---
        # KD (attempt to convert to int if possible)
        kd_val = tot.get("KD", "0")
        try:
            fighter_data["KD"] = int(kd_val)
        except ValueError:
            fighter_data["KD"] = kd_val
        
        # Build the "Sig. str." object.
        overall_sig = {
            "landed": tot.get("Sig. str._landed", 0),
            "attempted": tot.get("Sig. str._attempted", 0),
            "Head": {
                "landed": sig.get("Head_landed", 0),
                "attempted": sig.get("Head_attempted", 0)
            },
            "Body": {
                "landed": sig.get("Body_landed", 0),
                "attempted": sig.get("Body_attempted", 0)
            },
            "Leg": {
                "landed": sig.get("Leg_landed", 0),
                "attempted": sig.get("Leg_attempted", 0)
            },
            "Distance": {
                "landed": sig.get("Distance_landed", 0),
                "attempted": sig.get("Distance_attempted", 0)
            },
            "Clinch": {
                "landed": sig.get("Clinch_landed", 0),
                "attempted": sig.get("Clinch_attempted", 0)
            },
            "Ground": {
                "landed": sig.get("Ground_landed", 0),
                "attempted": sig.get("Ground_attempted", 0)
            }
        }
        fighter_data["Sig. str."] = overall_sig
        
        # "Sig. str. %" (convert from a string like "56%" to a float)
        sig_str_pct = tot.get("Sig. str. %", "0%")
        if isinstance(sig_str_pct, str) and sig_str_pct.endswith("%"):
            try:
                sig_str_pct = float(sig_str_pct.strip("%"))
            except ValueError:
                sig_str_pct = 0.0
        fighter_data["Sig. str. %"] = sig_str_pct
        
        # "Total str." as a nested dict.
        fighter_data["Total str."] = {
            "landed": tot.get("Total str._landed", 0),
            "attempted": tot.get("Total str._attempted", 0)
        }
        
        # "Td" as a nested dict.
        fighter_data["Td"] = {
            "landed": tot.get("Td_landed", 0),
            "attempted": tot.get("Td_attempted", 0)
        }
        
        # "Td %" (convert if needed)
        td_pct = tot.get("Td %", "0%")
        if isinstance(td_pct, str) and td_pct.endswith("%"):
            try:
                td_pct = float(td_pct.strip("%"))
            except ValueError:
                td_pct = 0.0
        fighter_data["Td %"] = td_pct
        
        # "Sub. att" and "Rev."
        fighter_data["Sub. att"] = tot.get("Sub. att", 0)
        fighter_data["Rev."] = tot.get("Rev.", 0)
        
        # "Ctrl" – assumed to be already in a proper time format (e.g. "0:00")
        fighter_data["Ctrl"] = tot.get("Ctrl", "")
        
        # --- Add round-by-round stats ---
        fighter_data["rounds"] = round_data
        
        # --- Add pre-comp stats ---
        fighter_data["pre_comp"] = pre_comp_data
        
        # Save the fighter data as fighter1 or fighter2.
        key = "fighter1" if i == 0 else "fighter2"
        final_output[key] = fighter_data
    
    # 5. Write the final JSON to a file with proper formatting.
    output_file_path = os.path.join(output_dir, f"{fight_id}.json")

    # Create the directory if it does not exist.
    os.makedirs(output_dir, exist_ok=True)

    with open(output_file_path, "w") as f:
        json.dump(final_output, f, indent=2)
    
    # Optional: print to console.
    print(json.dumps(final_output, indent=2))
    
    # Return the dictionary (not a dumped string) to avoid double encoding.
    return final_output

if __name__ == "__main__":
    print(main())
