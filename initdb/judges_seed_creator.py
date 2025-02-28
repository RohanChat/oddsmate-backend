#!/usr/bin/env python3
import os
import json
import glob
import hashlib
from datetime import datetime

def sanitize(value):
    """Sanitize a string for SQL insertion"""
    if value is None or value == "":
        return "NULL"
    if isinstance(value, str):
        # Replace single quotes with two single quotes to escape them in SQL
        return f"'{value.replace('\'', '\'\'')}'"
    return str(value)

def generate_temp_fight_id(event_id, judge_name, index):
    """Generate a temporary fight ID that's deterministic based on input"""
    # Create a hash of the inputs to ensure consistency
    hash_input = f"{event_id}_{judge_name}_{index}"
    # Use first 16 chars of hash as the ID
    temp_id = hashlib.md5(hash_input.encode()).hexdigest()[:16]
    return f"temp_{temp_id}"

def process_json_files():
    # Initialize collections for SQL statements
    judges_set = set()
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
                if not fights:
                    # This is where we need to generate a synthetic fight entry
                    # We'll create a single empty placeholder fight
                    temp_fight_id = f"temp_{event_id}_1"
                    
                    # Generate a synthetic judge entry
                    judge_name = "Unknown Judge"
                    if judge_name not in judges_set:
                        judges_set.add(judge_name)
                        judges_sql.append(
                            f"INSERT INTO judges (name) VALUES ({sanitize(judge_name)}) ON CONFLICT (name) DO NOTHING;"
                        )
                    
                    # Generate a synthetic fight score with NULL scores
                    fight_scores_sql.append(
                        f"-- TEMPORARY FIGHT ID: This is a placeholder fight for event {event_id}\n"
                        f"INSERT INTO fight_scores (fight_id, judge_id, event_id, total_fighter1, total_fighter2) "
                        f"VALUES ({sanitize(temp_fight_id)}, "
                        f"(SELECT judge_id FROM judges WHERE name = {sanitize(judge_name)}), "
                        f"{sanitize(event_id)}, NULL, NULL);"
                    )
                    
                    # Generate synthetic round scores with NULL scores
                    for round_number in range(1, 4):  # Assuming 3 rounds
                        round_scores_sql.append(
                            f"-- TEMPORARY FIGHT ID: This is a placeholder round for event {event_id}\n"
                            f"INSERT INTO round_scores (fight_id, event_id, judge_id, round_number, fighter1_score, fighter2_score) "
                            f"VALUES ({sanitize(temp_fight_id)}, {sanitize(event_id)}, "
                            f"(SELECT judge_id FROM judges WHERE name = {sanitize(judge_name)}), "
                            f"{round_number}, NULL, NULL);"
                        )
                    
                    continue
                
                # Process real fights data if available
                for fight_idx, fight in enumerate(fights):
                    fight_id = fight.get("fight_id")
                    
                    # If no fight_id, generate a temporary one
                    if not fight_id:
                        fight_id = f"temp_{event_id}_{fight_idx + 1}"
                        print(f"Generated temporary fight ID: {fight_id} for event {event_id}")
                    
                    # Process judges data
                    judges = fight.get("judges", {})
                    if not judges:
                        # No judges data, create one synthetic judge entry
                        judge_name = f"Unknown Judge"
                        if judge_name not in judges_set:
                            judges_set.add(judge_name)
                            judges_sql.append(
                                f"INSERT INTO judges (name) VALUES ({sanitize(judge_name)}) ON CONFLICT (name) DO NOTHING;"
                            )
                        
                        # Generate a synthetic fight score
                        fight_scores_sql.append(
                            f"-- TEMPORARY JUDGE DATA: This is a placeholder for fight {fight_id}\n"
                            f"INSERT INTO fight_scores (fight_id, judge_id, event_id, total_fighter1, total_fighter2) "
                            f"VALUES ({sanitize(fight_id)}, "
                            f"(SELECT judge_id FROM judges WHERE name = {sanitize(judge_name)}), "
                            f"{sanitize(event_id)}, NULL, NULL);"
                        )
                        continue
                        
                    total_fights_with_scores += 1
                    
                    # Process each judge's scores
                    for idx, (judge_name, judge_data) in enumerate(judges.items()):
                        if not judge_name or judge_name == "null" or not judge_data:
                            # Skip invalid judge entries
                            continue
                            
                        # Add judge to set if new
                        if judge_name not in judges_set:
                            judges_set.add(judge_name)
                            judges_sql.append(
                                f"INSERT INTO judges (name) VALUES ({sanitize(judge_name)}) ON CONFLICT (name) DO NOTHING;"
                            )
                        
                        # Process total scores
                        total = judge_data.get("total", {})
                        fighter1_score = total.get("fighter1", "NULL")
                        fighter2_score = total.get("fighter2", "NULL")
                        
                        # Add fight score record
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
                
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            import traceback
            traceback.print_exc()
    
    # Write the SQL files
    
    # 1. Judges file
    judges_file = os.path.join(output_dir, "01_judges.sql")
    with open(judges_file, 'w') as f:
        f.write("-- Seed data for judges table\n")
        f.write(f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
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
        f.write("-- WARNING: This file contains temporary fight IDs (prefixed with 'temp_') that need to be updated\n")
        f.write("-- Note: judges table must be populated first\n\n")
        f.write("\n".join(fight_scores_sql))
        f.write("\n")
    
    # 3. Round scores file
    round_scores_file = os.path.join(output_dir, "03_round_scores.sql")
    with open(round_scores_file, 'w') as f:
        f.write("-- Seed data for round_scores table\n")
        f.write(f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("-- WARNING: This file contains temporary fight IDs (prefixed with 'temp_') that need to be updated\n")
        f.write("-- Note: judges table must be populated first\n\n")
        f.write("\n".join(round_scores_sql))
        f.write("\n")
    
    # Print summary
    temp_count = sum(1 for line in fight_scores_sql if "TEMPORARY" in line)
    print(f"Processing complete!")
    print(f"Found {total_events} events with IDs")
    print(f"Generated {len(judges_set)} unique judges")
    print(f"Generated {len(fight_scores_sql)} fight score records ({temp_count} temporary)")
    print(f"Generated {len(round_scores_sql)} round score records")
    print(f"Generated temporary fight IDs for {temp_count} fights")
    print("\nSeed files created:")
    print(f"- {judges_file}")
    print(f"- {fight_scores_file}")
    print(f"- {round_scores_file}")
    
    # Note in the console about schema issues
    print("\nNOTE: Please fix any schema issues in your create_scoring_tables.sql file.")

if __name__ == "__main__":
    process_json_files()