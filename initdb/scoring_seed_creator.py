import os
import re
import json

# Global collections to gather SQL statements
judges_set = set()             # to deduplicate judge names
judges_sql_lines = []          # SQL lines for the judges table
fight_scores_sql_lines = []    # SQL lines for the fight_scores table
round_scores_sql_lines = []    # SQL lines for the round_scores table
fight_score_counter = 1        # global counter for fight_scores IDs

def sanitize(value):
    """Escape single quotes for SQL."""
    if isinstance(value, str):
        return value.replace("'", "''")
    return value

def process_event(event):
    """
    Process one event dictionary and generate SQL insert statements for:
      - judges (using a global set and ON CONFLICT clause)
      - fight_scores (one row per fight & judge combination)
      - round_scores (one row per round for each judge's score)
    """
    global fight_score_counter
    event_id = event.get("event_id", "")
    # event_details can be used for logging or further processing if needed.
    event_details = event.get("event_details", {})
    
    fights = event.get("fights", [])
    for fight in fights:
        # Use an empty string if no fight_id is provided
        fight_id = fight.get("fight_id", "")
        judges = fight.get("judges", {})
        for judge_key, judge_data in judges.items():
            judge_name = judge_data.get("judge_name", "")
            safe_judge_name = sanitize(judge_name)
            # If this judge hasn't been added yet, add an insert statement.
            if judge_name not in judges_set:
                judges_set.add(judge_name)
                judges_sql_lines.append(
                    f"INSERT INTO judges (name) VALUES ('{safe_judge_name}') ON CONFLICT (name) DO NOTHING;"
                )
            # Insert into fight_scores with the judge’s total scores.
            total = judge_data.get("total", {})
            total_fighter1 = total.get("fighter1", "NULL")
            total_fighter2 = total.get("fighter2", "NULL")
            fight_score_id = fight_score_counter
            fight_score_counter += 1
            
            fight_scores_sql_lines.append(
                "INSERT INTO fight_scores (id, fight_id, judge_id, Event_id, total_fighter1, total_fighter2) "
                f"VALUES ({fight_score_id}, '{sanitize(fight_id)}', "
                f"(SELECT judge_id FROM judges WHERE name = '{safe_judge_name}'), '{sanitize(event_id)}', "
                f"{total_fighter1}, {total_fighter2});"
            )
            
            # Insert round scores for each round for this judge.
            rounds = judge_data.get("rounds", [])
            for rnd in rounds:
                round_number = int(rnd.get("round", 0))
                fighter1_score = rnd.get("fighter1", "NULL")
                fighter2_score = rnd.get("fighter2", "NULL")
                round_scores_sql_lines.append(
                    "INSERT INTO round_scores (fight_id, Event_id, fight_judge_id, round_number, fighter1_score, fighter2_score) "
                    f"VALUES ('{sanitize(fight_id)}', '{sanitize(event_id)}', {fight_score_id}, {round_number}, {fighter1_score}, {fighter2_score});"
                )

def process_json_file(filepath):
    """
    Open and parse a JSON file (which can contain a single event or a list of events)
    and process each event.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
            return

    # JSON file may contain one event (dict) or a list of events.
    if isinstance(data, dict):
        events = [data]
    elif isinstance(data, list):
        events = data
    else:
        print(f"Unexpected JSON format in {filepath}")
        return

    for event in events:
        process_event(event)

def main():
    input_dir = "./data/raw/judging/"
    output_dir = "./initdb/seed/stats/"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process all JSON files recursively.
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".json"):
                filepath = os.path.join(root, file)
                print(f"Processing {filepath}...")
                process_json_file(filepath)
    
    # Write the collected SQL statements into one file per table.
    judges_file = os.path.join(output_dir, "judges_seed.sql")
    fight_scores_file = os.path.join(output_dir, "fight_scores_seed.sql")
    round_scores_file = os.path.join(output_dir, "round_scores_seed.sql")
    
    with open(judges_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(judges_sql_lines) + "\n")
    with open(fight_scores_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(fight_scores_sql_lines) + "\n")
    with open(round_scores_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(round_scores_sql_lines) + "\n")
    
    print("Seed files generated:")
    print(f"  Judges: {judges_file}")
    print(f"  Fight Scores: {fight_scores_file}")
    print(f"  Round Scores: {round_scores_file}")

if __name__ == "__main__":
    main()
