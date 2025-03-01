import csv
import json
import os

def try_convert(value):
    """Attempt to convert a string value to an int or float; otherwise return the original."""
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value

def insert_overall_stat(overall, key, value):
    """
    Process an overall stat key (e.g. "avg_head_strikes_landed_differential")
    and insert it into the nested overall dictionary.
    """
    # We expect keys to start with "avg_"
    if not key.startswith("avg_"):
        return
    # Remove the "avg_" prefix
    stat = key[4:]
    suffix = None
    # Check for an optional suffix
    if stat.endswith("_differential"):
        suffix = "differential"
        stat = stat[:-len("_differential")]
    elif stat.endswith("_per_min"):
        suffix = "per_min"
        stat = stat[:-len("_per_min")]
    
    # These keys are “simple” and go at the top level (no category grouping)
    simple_keys = {"knockdowns", "sub_attempts", "reversals", "control"}
    # Also, if the key is one of the physicals we want to group together
    physicals_keys = {"reach", "height", "age"}
    
    # If the stat is one of the simple ones, add it directly (wrapped in a dict)
    if stat in simple_keys:
        if stat not in overall:
            overall[stat] = {}
        prop = "avg" if suffix is None else suffix
        overall[stat][prop] = value
        return

    # If it’s one of the physicals (e.g. "avg_reach_differential") then group under "physicals"
    if stat in physicals_keys and suffix == "differential":
        if "physicals" not in overall:
            overall["physicals"] = {}
        overall["physicals"][stat + "_differential"] = value
        return

    # For the remainder we expect a two-part key like "<category>_<substat>".
    # Define the known multi–value categories.
    known_categories = [
        "takedowns", "sig_strikes", "total_strikes", "head_strikes",
        "body_strikes", "leg_strikes", "distance_strikes", "clinch_strikes", "ground_strikes"
    ]
    # Look for one of the known category prefixes (note: we remap "sig_strikes" to "significant_strikes")
    for cat in known_categories:
        prefix = cat + "_"
        if stat.startswith(prefix):
            # Remap "sig_strikes" to "significant_strikes" for clarity.
            actual_cat = "significant_strikes" if cat == "sig_strikes" else cat
            sub = stat[len(prefix):]  # the remainder becomes the sub–key (e.g. "landed", "attempts", etc.)
            if actual_cat not in overall:
                overall[actual_cat] = {}
            if sub not in overall[actual_cat]:
                overall[actual_cat][sub] = {}
            prop = "avg" if suffix is None else suffix
            overall[actual_cat][sub][prop] = value
            return

    # If no mapping rule applies, fall back to using the stat as the key.
    overall[stat] = value

def insert_recent_stat(recent, key, value):
    """
    Process a recent stat key (coming from the "precomp_recent_" columns)
    and insert it into the nested recent dictionary.
    
    In the recent stats we choose to assign the “simple” keys directly (without wrapping them in an "avg" key)
    and we group per_min values under a separate "per_min" section.
    """
    if not key.startswith("avg_"):
        return
    stat = key[4:]
    suffix = None
    if stat.endswith("_differential"):
        suffix = "differential"
        stat = stat[:-len("_differential")]
    elif stat.endswith("_per_min"):
        suffix = "per_min"
        stat = stat[:-len("_per_min")]
    
    simple_keys = {"knockdowns", "sub_attempts", "reversals", "control"}
    physicals_keys = {"reach", "height", "age"}
    known_categories = [
        "takedowns", "sig_strikes", "total_strikes", "head_strikes",
        "body_strikes", "leg_strikes", "distance_strikes", "clinch_strikes", "ground_strikes"
    ]
    
    # For the simple keys, assign directly
    if stat in simple_keys:
        if suffix is None:
            recent[stat] = value
        elif suffix == "differential":
            if "physicals" not in recent:
                recent["physicals"] = {}
            recent["physicals"][stat + "_differential"] = value
        return

    # If the stat is a physical (reach, height, age) and has a differential suffix,
    # group it under "physicals".
    if stat in physicals_keys and suffix == "differential":
        if "physicals" not in recent:
            recent["physicals"] = {}
        recent["physicals"][stat + "_differential"] = value
        return

    # For per_min values, place them into a separate "per_min" group.
    if suffix == "per_min":
        if "per_min" not in recent:
            recent["per_min"] = {}
        # Look for a known category in the key
        for cat in known_categories:
            prefix = cat + "_"
            if stat.startswith(prefix):
                actual_cat = "significant_strikes" if cat == "sig_strikes" else cat
                sub = stat[len(prefix):]
                if actual_cat not in recent["per_min"]:
                    recent["per_min"][actual_cat] = {}
                recent["per_min"][actual_cat][sub] = value
                return
        # If not in a known category, put it directly.
        recent["per_min"][stat] = value
        return

    # Otherwise, assume the stat is of the form "<category>_<substat>".
    for cat in known_categories:
        prefix = cat + "_"
        if stat.startswith(prefix):
            actual_cat = "significant_strikes" if cat == "sig_strikes" else cat
            sub = stat[len(prefix):]
            if actual_cat not in recent:
                recent[actual_cat] = {}
            recent[actual_cat][sub] = value
            return

    # Fallback: assign the stat as a top-level key.
    recent[stat] = value

def scrape_precomp_stats(fight_url, fighter_url):
    """
    Reads the CSV at /Users/rohan/desktop/oddsmate-backend/data/raw/UNCLEANED.csv,
    finds a row with the matching fight_url and fighter_url,
    then transforms all columns that start with 'precomp' into a nested JSON structure.
    
    Overall stats come from columns beginning with 'precomp_' (with keys starting "avg_")
    and recent stats from columns starting with 'precomp_recent_'.
    
    The final structure nests keys by their domain (e.g. "takedowns", "head_strikes", etc.)
    and removes the redundant prefixes. If no matching row is found, returns None.
    
    Example final output:
    
    {
        "overall": {
            "knockdowns": { "avg": 1.22, ... },
            "takedowns": {
                "landed": { "avg": 0.0, "differential": 0.56 },
                "attempts": { "avg": 0.33, "per_min": 0.016 }
            },
            "significant_strikes": {
                "landed": { "avg": 62.0 },
                "attempts": { "avg": 124.0 }
            },
            "head_strikes": {
                "landed": { "avg": 33.11, "differential": 3.38 },
                "attempts": { "avg": 87.22, "differential": 1.60 }
            },
            "physicals": {
                "reach_differential": 1.07,
                "height_differential": 1.05,
                "age_differential": 0.95
            }
        },
        "recent": {
            "knockdowns": 1.0,
            "takedowns": {
                "landed": 0.0,
                "attempts": 0.0,
                "accuracy": 0.0
            },
            "per_min": {
                "takedowns": { "landed": 0.0, "attempts": 0.0 },
                "head_strikes": { "landed": 2.13, "attempts": 6.09 }
            },
            "physicals": {
                "reach_differential": 1.10,
                "height_differential": 1.05,
                "age_differential": 0.93
            }
        }
    }
    """
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    csv_path = os.path.join(base_dir, "data/raw/UNCLEANED_2.csv")
    
    with open(csv_path, mode="r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            if row.get("fight_url") == fight_url and row.get("fighter_url") == fighter_url:
                overall = {}
                recent = {}
                
                for col, val in row.items():
                    if not val:
                        continue  # Skip empty values
                    converted_val = try_convert(val)
                    
                    # Process recent columns (those with precomp_recent_)
                    if col.startswith("precomp_recent_"):
                        key = col[len("precomp_recent_"):]
                        insert_recent_stat(recent, key, converted_val)
                    # Process overall columns (those with precomp_ but not recent)
                    elif col.startswith("precomp_"):
                        key = col[len("precomp_"):]
                        insert_overall_stat(overall, key, converted_val)
                
                # Build final output structure. If no recent stats were found, you could return just overall.
                result = {"overall": overall}
                if recent:
                    result["recent"] = recent
                return result

    # If no matching row was found, return nothing.
    return None


if __name__ == "__main__":
    fight_url = "http://ufcstats.com/fight-details/7de9867b7cc2b1b1"
    fighter_url = "http://ufcstats.com/fighter-details/1338e2c7480bdf9e"
    stats = scrape_precomp_stats(fight_url, fighter_url)
    
    if stats:
        import json
        print(json.dumps(stats, indent=4))
    else:
        print("No matching data found.")
