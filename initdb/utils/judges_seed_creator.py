#!/usr/bin/env python3
import os
import json
import glob
from datetime import datetime
import hashlib

def sanitize(value):
    """Sanitize a string for SQL insertion"""
    if value is None or value == "":
        return "NULL"
    if isinstance(value, str):
        # Replace single quotes with two single quotes to escape them in SQL
        return f"'{value.replace('\'', '\'\'')}'"
    return str(value)

def generate_temp_fight_id(event_id, index):
    """Generate a temporary fight ID that's deterministic based on input"""
    hash_input = f"{event_id}_{index}"
    temp_id = hashlib.md5(hash_input.encode()).hexdigest()[:16]
    return f"temp_{temp_id}"

def process_json_files():
    """Process all JSON files and generate SQL seed files"""
    # Initialize collections for SQL statements
    judges_set = set()  # Using a set for unique judge names
    judges_sql = []
    fight_scores_sql = []
    round_scores_sql = []
    
    # Create output directory if it doesn't exist
    output_dir = "./initdb/seed/scoring/"
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all JSON files in the judging directory and subdirectories
    json_files = glob.glob("./data/raw/judging/**/*.json", recursive=True)
    
    # Add the specific file mentioned if not already included
    all_until_2025_path = "./data/raw/judging/all_until_2025.json"
    if os.path.exists(all_until_2025_path) and all_until_2025_path not in json_files:
        json_files.append(all_until_2025_path)
    
    if not json_files:
        print("Error: No JSON files found in ./data/raw/judging/")
        return
    
    print(f"Found {len(json_files)} JSON files to process")
    
    # Counters for summary
    total_events = 0
    total_fights_with_scores = 0
    real_judges_count = 0
    
    # Try to find any real judge data in files
    real_judge_data_found = False
    test_data_being_used = False
    
    # Process each JSON file
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                
            # Handle both single event and array of events
            events = [data] if isinstance(data, dict) else data if isinstance(data, list) else []
            
            # Process each event
            for event in events:
                event_id = event.get("event_id")
                if not event_id:
                    # Skip events without IDs (like non-UFC events)
                    continue
                
                total_events += 1
                
                # Check if the event has any actual fights data
                fights = event.get("fights", [])
                
                # Create a dict to map fights to judges for this event
                event_fight_judges = {}
                
                # For each fight in the event
                for fight_idx, fight in enumerate(fights):
                    fight_id = fight.get("fight_id") 
                    if not fight_id:
                        # Generate a temporary fight ID if not present
                        fight_id = f"temp_{event_id}_{fight_idx + 1}"
                    
                    # Extract judge data from the fight
                    judges = fight.get("judges", {})
                    
                    # If this fight has judge data, process it
                    if judges and isinstance(judges, dict) and len(judges) > 0:
                        real_judge_data_found = True
                        for judge_name, judge_data in judges.items():
                            if not judge_name or judge_name == "null" or not judge_data:
                                continue
                                
                            # Add to our set of unique judges
                            judges_set.add(judge_name)
                            real_judges_count += 1
                            
                            # Add the SQL for this judge
                            judges_sql.append(
                                f"INSERT INTO judges (name) VALUES ({sanitize(judge_name)}) ON CONFLICT (name) DO NOTHING;"
                            )
                            
                            # Process total scores
                            total = judge_data.get("total", {})
                            fighter1_score = total.get("fighter1", "NULL")
                            fighter2_score = total.get("fighter2", "NULL")
                            
                            fight_scores_sql.append(
                                f"INSERT INTO fight_scores (fight_id, judge_id, event_id, total_fighter1, total_fighter2) "
                                f"VALUES ({sanitize(fight_id)}, "
                                f"(SELECT judge_id FROM judges WHERE name = {sanitize(judge_name)}), "
                                f"{sanitize(event_id)}, {fighter1_score}, {fighter2_score});"
                            )
                            
                            # Process round scores
                            rounds = judge_data.get("rounds", [])
                            for round_data in rounds:
                                round_number = round_data.get("round")
                                if not round_number:
                                    continue
                                    
                                fighter1_round_score = round_data.get("fighter1", "NULL")
                                fighter2_round_score = round_data.get("fighter2", "NULL")
                                
                                round_scores_sql.append(
                                    f"INSERT INTO round_scores (fight_id, event_id, judge_id, round_number, fighter1_score, fighter2_score) "
                                    f"VALUES ({sanitize(fight_id)}, {sanitize(event_id)}, "
                                    f"(SELECT judge_id FROM judges WHERE name = {sanitize(judge_name)}), "
                                    f"{round_number}, {fighter1_round_score}, {fighter2_round_score});"
                                )
                            
                            total_fights_with_scores += 1
                
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    # If we didn't find any real judge data, create sample data
    if not real_judge_data_found:
        print("No real judge data found in JSON files. Creating sample data.")
        test_data_being_used = True
        
        # Create a set of realistic judge names for our sample data
        real_judge_names = [
            "Derek Cleary", "Sal D'Amato", "Mike Bell", "Chris Lee", 
            "Eric Colon", "Dave Hagen", "Junichiro Kamijo", "Marcos Rosales",
            "Douglas Crosby", "Ron McCarthy", "Jeff Mullen", "Tony Weeks"
        ]
        
        # Add our sample judges
        for judge_name in real_judge_names[:5]:  # Just use the first 5 judges
            judges_set.add(judge_name)
            judges_sql.append(
                f"INSERT INTO judges (name) VALUES ({sanitize(judge_name)}) ON CONFLICT (name) DO NOTHING;"
            )
    
    # Write the SQL files
    
    # 1. Judges file
    judges_file = os.path.join(output_dir, "01_judges.sql")
    with open(judges_file, 'w') as f:
        f.write("-- Seed data for judges table\n")
        f.write(f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        if test_data_being_used:
            f.write("-- NOTE: Using realistic sample judge names because no real judge data was found\n\n")
        f.write("-- First clear any existing data\n")
        f.write("TRUNCATE judges CASCADE;\n\n")
        f.write("-- Insert judges data\n")
        f.write("\n".join(sorted(set(judges_sql))))
        f.write("\n")
    
    # 2. Fight scores file
    fight_scores_file = os.path.join(output_dir, "02_fight_scores.sql")
    with open(fight_scores_file, 'w') as f:
        f.write("-- Seed data for fight_scores table\n")
        f.write(f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        if test_data_being_used:
            f.write("-- NOTE: Using sample data because no real judge data was found\n\n")
        f.write("-- WARNING: This file contains temporary fight IDs (prefixed with 'temp_') that need to be updated\n")
        f.write("-- Note: judges table must be populated first\n\n")
        f.write("\n".join(fight_scores_sql))
        f.write("\n")
    
    # 3. Round scores file
    round_scores_file = os.path.join(output_dir, "03_round_scores.sql")
    with open(round_scores_file, 'w') as f:
        f.write("-- Seed data for round_scores table\n")
        f.write(f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        if test_data_being_used:
            f.write("-- NOTE: Using sample data because no real judge data was found\n\n")
        f.write("-- WARNING: This file contains temporary fight IDs (prefixed with 'temp_') that need to be updated\n")
        f.write("-- Note: judges table must be populated first\n\n")
        f.write("\n".join(round_scores_sql))
        f.write("\n")
    
    # Print summary
    print(f"Processing complete!")
    print(f"Found {total_events} events with IDs")
    
    if real_judge_data_found:
        print(f"Found {total_fights_with_scores} fights with judge scoring")
        print(f"Generated {len(judges_set)} unique judges from real data")
    else:
        print(f"No real judge data found - created {len(judges_set)} sample judges")
    
    print(f"Generated {len(fight_scores_sql)} fight score records")
    print(f"Generated {len(round_scores_sql)} round score records")
    print("\nSeed files created:")
    print(f"- {judges_file}")
    print(f"- {fight_scores_file}")
    print(f"- {round_scores_file}")

if __name__ == "__main__":
    process_json_files()