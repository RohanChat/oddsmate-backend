#!/usr/bin/env python3
# filepath: /Users/rohan/Desktop/oddsmate-backend/initdb/round_stats_seed_creator.py

import json
import os
import glob
from datetime import datetime
from typing import List, Dict, Any, Optional

def convert_ctrl_to_seconds(ctrl_str) -> int:
    """Convert control time string to seconds."""
    if not ctrl_str or ctrl_str == "0" or ctrl_str == 0:
        return 0
    
    if isinstance(ctrl_str, int):
        return ctrl_str
    elif ':' in ctrl_str:
        minutes, seconds = ctrl_str.split(':')
        return int(minutes) * 60 + int(seconds)
    else:
        try:
            return int(ctrl_str)
        except (ValueError, TypeError):
            return 0

def extract_round_stats(fight_id: str, fighter_id: str, round_number: int, round_stats: Dict) -> Optional[str]:
    """Extract round statistics and create SQL INSERT statement."""
    try:
        # Knockdowns
        kd = round_stats.get('KD', 0)
        
        # Significant strikes
        sig_strikes = round_stats.get('Sig. str.', {})
        sig_strikes_landed = sig_strikes.get('landed', 0)
        sig_strikes_attempted = sig_strikes.get('attempted', 0)
        sig_strikes_accuracy = round_stats.get('Sig. str. %', 0)
        
        # Strikes by target
        head_strikes = sig_strikes.get('Head', {})
        head_strikes_landed = head_strikes.get('landed', 0)
        head_strikes_attempted = head_strikes.get('attempted', 0)
        
        body_strikes = sig_strikes.get('Body', {})
        body_strikes_landed = body_strikes.get('landed', 0)
        body_strikes_attempted = body_strikes.get('attempted', 0)
        
        leg_strikes = sig_strikes.get('Leg', {})
        leg_strikes_landed = leg_strikes.get('landed', 0)
        leg_strikes_attempted = leg_strikes.get('attempted', 0)
        
        # Strikes by position
        distance_strikes = sig_strikes.get('Distance', {})
        distance_strikes_landed = distance_strikes.get('landed', 0)
        distance_strikes_attempted = distance_strikes.get('attempted', 0)
        
        clinch_strikes = sig_strikes.get('Clinch', {})
        clinch_strikes_landed = clinch_strikes.get('landed', 0)
        clinch_strikes_attempted = clinch_strikes.get('attempted', 0)
        
        ground_strikes = sig_strikes.get('Ground', {})
        ground_strikes_landed = ground_strikes.get('landed', 0)
        ground_strikes_attempted = ground_strikes.get('attempted', 0)
        
        # Total strikes
        total_strikes = round_stats.get('Total str.', {})
        total_strikes_landed = total_strikes.get('landed', 0)
        total_strikes_attempted = total_strikes.get('attempted', 0)
        
        # Takedowns
        td = round_stats.get('Td', {})
        td_landed = td.get('landed', 0)
        td_attempted = td.get('attempted', 0)
        td_accuracy = round_stats.get('Td %', 0)
        
        # Submissions and reversals
        sub_att = round_stats.get('Sub. att', 0)
        if isinstance(sub_att, str):
            sub_att = int(sub_att) if sub_att.isdigit() else 0
            
        reversals = round_stats.get('Rev.', 0)
        if isinstance(reversals, str):
            reversals = int(reversals) if reversals.isdigit() else 0
        
        # Control time
        ctrl = convert_ctrl_to_seconds(round_stats.get('Ctrl', 0))
        
        # Create SQL insert statement
        return f"""INSERT INTO round_stats (fight_id, fighter_id, round_number, kd, 
            sig_strikes_landed, sig_strikes_attempted, sig_strikes_accuracy,
            head_strikes_landed, head_strikes_attempted, 
            body_strikes_landed, body_strikes_attempted,
            leg_strikes_landed, leg_strikes_attempted,
            distance_strikes_landed, distance_strikes_attempted,
            clinch_strikes_landed, clinch_strikes_attempted,
            ground_strikes_landed, ground_strikes_attempted,
            total_strikes_landed, total_strikes_attempted,
            td_landed, td_attempted, td_accuracy,
            sub_att, reversals, ctrl) VALUES (
            '{fight_id}',
            '{fighter_id}',
            {round_number},
            {kd},
            {sig_strikes_landed},
            {sig_strikes_attempted},
            {sig_strikes_accuracy},
            {head_strikes_landed},
            {head_strikes_attempted},
            {body_strikes_landed},
            {body_strikes_attempted},
            {leg_strikes_landed},
            {leg_strikes_attempted},
            {distance_strikes_landed},
            {distance_strikes_attempted},
            {clinch_strikes_landed},
            {clinch_strikes_attempted},
            {ground_strikes_landed},
            {ground_strikes_attempted},
            {total_strikes_landed},
            {total_strikes_attempted},
            {td_landed},
            {td_attempted},
            {td_accuracy},
            {sub_att},
            {reversals},
            {ctrl}
        );"""
    except Exception as e:
        print(f"Error extracting stats for fighter {fighter_id} in round {round_number}: {str(e)}")
        return None

def process_fighter_rounds(fight_id: str, fighter: Dict, fighter_key: str) -> List[str]:
    """Process rounds data for a fighter."""
    sql_inserts = []
    fighter_id = fighter.get('id')
    if not fighter_id:
        print(f"Warning: Missing ID for {fighter_key} in fight {fight_id}")
        return []
        
    fighter_rounds = fighter.get('rounds', {})
    
    for round_name, round_stats in fighter_rounds.items():
        if not round_name.startswith('round'):
            continue
            
        try:
            round_number = int(round_name.replace('round', ''))
            sql_insert = extract_round_stats(fight_id, fighter_id, round_number, round_stats)
            if sql_insert:
                sql_inserts.append(sql_insert)
        except Exception as e:
            print(f"Error processing {round_name} for {fighter_key} in fight {fight_id}: {str(e)}")
    
    return sql_inserts

def process_event_json(data: Dict) -> List[str]:
    """Process event-style JSON containing multiple fights."""
    sql_inserts = []
    
    for fight in data.get('fights', []):
        fight_id = fight.get('fight_id')
        if not fight_id:
            continue
        
        # Process fighter1's rounds
        fighter1 = fight.get('fighter1', {})
        sql_inserts.extend(process_fighter_rounds(fight_id, fighter1, 'fighter1'))
        
        # Process fighter2's rounds
        fighter2 = fight.get('fighter2', {})
        sql_inserts.extend(process_fighter_rounds(fight_id, fighter2, 'fighter2'))
    
    return sql_inserts

def process_fight_json(data: Dict, file_path: str) -> List[str]:
    """Process single fight JSON file."""
    sql_inserts = []
    
    # Use filename as fight_id if not specified
    fight_id = data.get('fight_id', os.path.basename(file_path).split('.')[0])
    
    # Process fighter1's rounds if present
    if 'fighter1' in data:
        sql_inserts.extend(process_fighter_rounds(fight_id, data['fighter1'], 'fighter1'))
    
    # Process fighter2's rounds if present
    if 'fighter2' in data:
        sql_inserts.extend(process_fighter_rounds(fight_id, data['fighter2'], 'fighter2'))
    
    return sql_inserts

def process_json_file(file_path: str) -> List[str]:
    """Process a JSON file and determine its structure."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON from {file_path}")
        return []
    
    # Determine file structure and process accordingly
    if 'event_id' in data and 'fights' in data:
        print(f"Processing as event file: {file_path}")
        return process_event_json(data)
    elif 'fighter1' in data or 'fighter2' in data:
        print(f"Processing as single fight file: {file_path}")
        return process_fight_json(data, file_path)
    elif 'fights' in data:
        print(f"Processing as event file without event_id: {file_path}")
        return process_event_json(data)
    else:
        print(f"Skipping file with unknown structure: {file_path}")
        return []

def find_json_files() -> List[str]:
    """Find all JSON files in the data directory."""
    json_files = []
    
    # Base directory
    base_dir = './data/raw/stats/event_dumps'
    
    # Check main directory
    for json_file in glob.glob(f"{base_dir}/*.json"):
        json_files.append(json_file)
    
    # Check subdirectories
    for subdir in glob.glob(f"{base_dir}/**/"):
        for json_file in glob.glob(f"{subdir}/*.json"):
            json_files.append(json_file)
    
    print(f"Found {len(json_files)} JSON files")
    return json_files

def write_sql_file(sql_inserts: List[str], output_file: str):
    """Write SQL statements to output file."""
    with open(output_file, 'w') as f:
        f.write("-- Seed data for round_stats table\n")
        f.write(f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("-- Disable triggers for faster bulk loading\n")
        f.write("ALTER TABLE round_stats DISABLE TRIGGER ALL;\n\n")
        
        for sql in sql_inserts:
            f.write(sql + "\n\n")
        
        f.write("-- Re-enable triggers\n")
        f.write("ALTER TABLE round_stats ENABLE TRIGGER ALL;\n")
    
    print(f"Generated {len(sql_inserts)} SQL INSERT statements")
    print(f"Output written to {output_file}")

def main():
    """Main function to orchestrate the seed data generation process."""
    # Find all JSON files
    json_files = find_json_files()
    
    # Process each file and collect SQL statements
    all_sql_inserts = []
    for json_file in json_files:
        sql_inserts = process_json_file(json_file)
        all_sql_inserts.extend(sql_inserts)
    
    # Write SQL statements to output file
    output_file = "./initdb/05_round_stats_seed.sql"
    write_sql_file(all_sql_inserts, output_file)

if __name__ == "__main__":
    main()