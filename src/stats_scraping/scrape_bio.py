import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re

def clean_record_part(part):
    """
    Remove any parenthetical text from the record part and return just the integer.
    For example:
       "0 (1 NC)"  --> "0"
       "10"        --> "10"
    """
    # Remove anything starting with a space and an open parenthesis.
    cleaned = re.sub(r'\s*\(.*\)', '', part)
    return cleaned.strip()

def convert_height_to_inches(height_str):
    """
    Convert a height string like "5' 6\"" or "5'6\"" to an integer of total inches, e.g. 66.
    If parsing fails, returns None.
    """
    # This regex will match either 5' 6" or 5'6"
    match = re.match(r"(\d+)'\s*(\d+)", height_str)
    if match:
        feet = int(match.group(1))
        inches = int(match.group(2))
        return feet * 12 + inches
    return None

def convert_reach_to_int(reach_str):
    """
    Convert a reach string like "68\"" or "70 in." to an integer (e.g. 68 or 70).
    If parsing fails, returns None.
    """
    digits = re.findall(r"\d+", reach_str)
    if digits:
        return int(digits[0])
    return None

def convert_weight_to_int(weight_str):
    """
    Convert a weight string like "135 lbs." or "155 lbs" to an integer (e.g., 135 or 155).
    If parsing fails, returns None.
    """
    digits = re.findall(r"\d+", weight_str)
    if digits:
        return int(digits[0])
    return None

def convert_dob_to_ddmmyyyy(dob_str):
    """
    Convert a DOB string like "Oct 1, 1991" to "01/10/1991" (DD/MM/YYYY format).
    If parsing fails or empty, returns the original string or None.
    """
    if not dob_str:
        return None
    
    try:
        dob_obj = datetime.strptime(dob_str, "%b %d, %Y")
        return dob_obj.strftime("%d/%m/%Y")
    except ValueError:
        # If it doesn't match the expected format, just return as-is or None
        return dob_str

def scrape_fighter_stats(fighter_url):
    # Parse id from URL (everything after the last slash)
    id = fighter_url.strip('/').split('/')[-1]
    
    response = requests.get(fighter_url)
    if response.status_code != 200:
        print("Failed to retrieve page")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract Fighter Name
    name_tag = soup.find('span', class_='b-content__title-highlight')
    name = name_tag.text.strip() if name_tag else ""

    nickname_tag = soup.find('p', class_='b-content__Nickname')
    nickname = nickname_tag.text.strip() if nickname_tag else ""

    # Extract Record (e.g., "Record: 19-4-0")
    record_tag = soup.find('span', class_='b-content__title-record')
    wins, losses, draws = 0, 0, 0
    if record_tag:
        record_text = record_tag.text.strip()  # e.g. "Record: 19-4-0"
        record_text = record_text.replace("Record:", "").strip()  # "19-4-0"
        parts = record_text.split('-')
        # Assume `parts` is a list of strings obtained by splitting the record string.
        cleaned_parts = [clean_record_part(part) for part in parts]
        if len(parts) == 3:
            try:
                wins, losses, draws = map(int, cleaned_parts)
            except ValueError as e:
                # Optionally, log the error or set defaults if conversion fails.
                wins, losses, draws = 0, 0, 0
    
    # Prepare dictionary for raw stats
    raw_stats = {}
    
    # We can look for these labels in <li> blocks with class 'b-list__box-list-item'
    # The site typically uses keys like: "Height:", "Weight:", "Reach:", "Stance:", "DOB:", "Nickname:"
    for item in soup.find_all('li', class_='b-list__box-list-item'):
        title = item.find('i', class_='b-list__box-item-title')
        if title:
            key = title.text.strip().replace(':', '')   # e.g. "Height", "Weight", etc.
            value = item.text.replace(title.text, '').strip()  
            # e.g. if item is "<li> <i>Height:</i> 5'6" </li>", then value ~ "5'6\""
            raw_stats[key] = value
    
    # Now gather the career (pre-fight) statistics
    # Typically listed in another set of <li> blocks as well
    # We want to map them to the final keys you provided (with punctuation, etc.)
    # e.g. site might use "SLpM" => your final JSON wants "SLpM"
    # site might use "Str. Def." => final JSON wants "Str. Def:"

    # Mapping from site text to final JSON key you specified
    # Adjust as needed so your final output EXACTLY matches the requested format
    stat_key_map = {
        "SLpM": "SLpM",
        "Str. Acc.": "Str. Acc.:",
        "SApM": "SApM",
        "Str. Def.": "Str. Def:",    # site typically has a period
        "TD Avg.": "TD. Avg.",
        "TD Acc.": "TD. Acc.",
        "TD Def.": "TD, Def",        # note the comma instead of period, as per your example
        "Sub. Avg.": "Sub. Avg."
    }

    # Initialize your stats dictionary
    stats = {
        # We'll add stats as we parse them
    }

    # Some sites might show "Str. Acc." or "Str. Acc.:". We'll check each <li> for relevant stats
    for item in soup.find_all('li', class_='b-list__box-list-item'):
        title = item.find('i', class_='b-list__box-item-title')
        if title:
            # Clean up the label
            key_site = title.text.strip().replace(':', '')  # site label w/o trailing colon
            if key_site in stat_key_map:
                final_key = stat_key_map[key_site]
                value = item.text.replace(title.text, '').strip()
                
                # Try to remove % if present
                numeric_val = value.replace('%', '').strip()
                # Convert to float if possible
                try:
                    numeric_val = float(numeric_val)
                    stats[final_key] = numeric_val
                except ValueError:
                    stats[final_key] = numeric_val
    
    # Build the final top-level dictionary

    # # Nickname (title-casing, if desired)
    # nickname = raw_stats.get("Nickname", "").strip()
    
    # DOB
    dob_str = raw_stats.get("DOB", "")
    dob_formatted = convert_dob_to_ddmmyyyy(dob_str)
    
    # Height in inches
    height_str = raw_stats.get("Height", "")
    height_in_inches = convert_height_to_inches(height_str)
    
    # Weight in lbs (integer)
    weight_str = raw_stats.get("Weight", "")
    weight_int = convert_weight_to_int(weight_str)

    # Reach as integer
    reach_str = raw_stats.get("Reach", "")
    reach_int = convert_reach_to_int(reach_str)
    
    # Stance (lowercase)
    stance_str = raw_stats.get("STANCE", "").lower()
    
    # Insert record into stats
    stats["record"] = {
        "wins": wins,
        "losses": losses,
        "draws": draws
    }
    
    # Build your final JSON structure
    output = {
        "id": id,
        "name": name,
        "nickname": nickname,
        "dob": dob_formatted,
        "height": height_in_inches if height_in_inches else None,
        "weight": weight_int if weight_int else None,
        "reach": reach_int if reach_int else None,
        "stance": stance_str,
        "stats": stats,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Add timestamp here

    }
    
    return output

# Example usage
if __name__ == "__main__":
    fighter_url = "http://ufcstats.com/fighter-details/1338e2c7480bdf9e"  # Example fighter URL
    fighter_stats = scrape_fighter_stats(fighter_url)
    print(json.dumps(fighter_stats, indent=4))
