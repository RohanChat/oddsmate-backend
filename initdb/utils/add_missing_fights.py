#!/usr/bin/env python3
# filepath: /Users/rohan/Desktop/oddsmate-backend/initdb/utils/generate_fight_seeds.py

import os
import json
import glob
from datetime import datetime

def sanitize_sql_value(value):
    """Sanitize values for SQL insertion"""
    if value is None or value == "":
        return "NULL"
    if isinstance(value, str):
        # Replace single quotes with two single quotes to escape them in SQL
        return f"'{value.replace('\'', '\'\'')}'"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)

def parse_time_to_seconds(time_str):
    """Convert time string (MM:SS) to seconds"""
    if not time_str or time_str == "---":
        return 0
    
    parts = time_str.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return 0

def extract_fights_and_stats():
    """Extract fight data and statistics from JSONs"""
    base_dir = "./data/raw/stats/event_dumps/"
    fights_data = []
    fight_stats_data = []
    
    # Find all JSON files in the directory and subdirectories
    json_files = glob.glob(f"{base_dir}**/*.json", recursive=True)
    print(f"Found {len(json_files)} JSON files")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract event ID
            event_id = data.get('event_id')
            # Extract event ID
            event_id = data.get('event_id')
            
            # If no event_id, use parent folder name as fallback
            if not event_id:
                parent_folder = os.path.basename(os.path.dirname(json_file))
                print(f"No event_id found in {json_file}, using parent folder name '{parent_folder}' as event_id")
                event_id = parent_folder
                
            # Process fights in the event
            if 'fights' in data:
                for fight in data['fights']:
                    # Extract fight data
                    fight_data = extract_fight_data(fight, event_id)
                    if fight_data:
                        fights_data.append(fight_data)
                    
                    # Extract fight statistics
                    stats_data = extract_fight_stats(fight)
                    if stats_data:
                        fight_stats_data.extend(stats_data)
            
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            continue
    
    print(f"Extracted data for {len(fights_data)} fights")
    print(f"Extracted {len(fight_stats_data)} fighter statistics entries")
    return fights_data, fight_stats_data

def extract_fight_data(fight, event_id):
    """Extract data for the fights table"""
    fight_id = fight.get('fight_id')
    if not fight_id:
        return None
    
    # Extract fight details
    method = fight.get('method', '')
    round_num = fight.get('round', '')
    time = fight.get('time', '')
    referee = fight.get('referee', '')
    
    # Extract fighter details
    fighter1 = fight.get('fighter1', {})
    fighter2 = fight.get('fighter2', {})
    
    fighter1_id = fighter1.get('id', '')
    fighter2_id = fighter2.get('id', '')
    
    # Extract results
    fighter1_result = fighter1.get('result', '')
    fighter2_result = fighter2.get('result', '')
    
    # Create fight data object
    fight_data = {
        'fight_id': fight_id,
        'event_id': event_id,
        'fight_url': '',  # Not available in JSON
        'status': 'finished',  # All historical fights are finished
        'curr_round': '',
        'curr_time': '',
        'last_updated': None,
        'referee': referee,
        'fighter1_id': fighter1_id,
        'fighter2_id': fighter2_id,
        'fighter1_result': fighter1_result,
        'fighter2_result': fighter2_result,
        'final_method': method
    }
    
    return fight_data

def extract_fight_stats(fight):
    """Extract statistics for the fight_stats table"""
    fight_id = fight.get('fight_id')
    if not fight_id:
        return []
    
    stats_data = []
    
    # Process fighter1 stats
    fighter1 = fight.get('fighter1', {})
    fighter1_id = fighter1.get('id')
    if fighter1_id:
        fighter1_stats = create_fighter_stats(fight_id, fighter1_id, fighter1)
        if fighter1_stats:
            stats_data.append(fighter1_stats)
    
    # Process fighter2 stats
    fighter2 = fight.get('fighter2', {})
    fighter2_id = fighter2.get('id')
    if fighter2_id:
        fighter2_stats = create_fighter_stats(fight_id, fighter2_id, fighter2)
        if fighter2_stats:
            stats_data.append(fighter2_stats)
    
    return stats_data

def create_fighter_stats(fight_id, fighter_id, fighter_data):
    """Create a statistics entry for a fighter"""
    # Extract KD
    kd = fighter_data.get('KD', 0)
    
    # Extract significant strikes
    sig_str = fighter_data.get('Sig. str.', {})
    sig_strikes_landed = sig_str.get('landed', 0)
    sig_strikes_attempted = sig_str.get('attempted', 0)
    sig_strikes_accuracy = fighter_data.get('Sig. str. %', 0)
    
    # Extract strike breakdowns
    head = sig_str.get('Head', {})
    head_strikes_landed = head.get('landed', 0)
    head_strikes_attempted = head.get('attempted', 0)
    
    body = sig_str.get('Body', {})
    body_strikes_landed = body.get('landed', 0)
    body_strikes_attempted = body.get('attempted', 0)
    
    leg = sig_str.get('Leg', {})
    leg_strikes_landed = leg.get('landed', 0)
    leg_strikes_attempted = leg.get('attempted', 0)
    
    distance = sig_str.get('Distance', {})
    distance_strikes_landed = distance.get('landed', 0)
    distance_strikes_attempted = distance.get('attempted', 0)
    
    clinch = sig_str.get('Clinch', {})
    clinch_strikes_landed = clinch.get('landed', 0)
    clinch_strikes_attempted = clinch.get('attempted', 0)
    
    ground = sig_str.get('Ground', {})
    ground_strikes_landed = ground.get('landed', 0)
    ground_strikes_attempted = ground.get('attempted', 0)
    
    # Extract total strikes
    total_str = fighter_data.get('Total str.', {})
    total_strikes_landed = total_str.get('landed', 0)
    total_strikes_attempted = total_str.get('attempted', 0)
    
    # Extract takedowns
    td = fighter_data.get('Td', {})
    td_landed = td.get('landed', 0)
    td_attempted = td.get('attempted', 0)
    td_accuracy = fighter_data.get('Td %', 0)
    if td_accuracy == "---":
        td_accuracy = 0
    
    # Extract submission attempts and reversals
    sub_att = fighter_data.get('Sub. att', 0)
    if isinstance(sub_att, str):
        sub_att = int(sub_att) if sub_att.isdigit() else 0
        
    reversals = fighter_data.get('Rev.', 0)
    if isinstance(reversals, str):
        reversals = int(reversals) if reversals.isdigit() else 0
    
    # Extract control time
    ctrl = fighter_data.get('Ctrl', '0:00')
    ctrl_seconds = parse_time_to_seconds(ctrl)
    
    # Create stats object
    stats = {
        'fight_id': fight_id,
        'fighter_id': fighter_id,
        'kd': kd,
        'sig_strikes_landed': sig_strikes_landed,
        'sig_strikes_attempted': sig_strikes_attempted,
        'sig_strikes_accuracy': sig_strikes_accuracy,
        'head_strikes_landed': head_strikes_landed,
        'head_strikes_attempted': head_strikes_attempted,
        'body_strikes_landed': body_strikes_landed,
        'body_strikes_attempted': body_strikes_attempted,
        'leg_strikes_landed': leg_strikes_landed,
        'leg_strikes_attempted': leg_strikes_attempted,
        'distance_strikes_landed': distance_strikes_landed,
        'distance_strikes_attempted': distance_strikes_attempted,
        'clinch_strikes_landed': clinch_strikes_landed,
        'clinch_strikes_attempted': clinch_strikes_attempted,
        'ground_strikes_landed': ground_strikes_landed,
        'ground_strikes_attempted': ground_strikes_attempted,
        'total_strikes_landed': total_strikes_landed,
        'total_strikes_attempted': total_strikes_attempted,
        'total_strikes_accuracy': sig_strikes_accuracy, # Using same as sig strikes accuracy
        'td_landed': td_landed,
        'td_attempted': td_attempted,
        'td_accuracy': td_accuracy,
        'sub_att': sub_att,
        'reversals': reversals,
        'ctrl': ctrl_seconds
    }
    
    return stats

def generate_fights_seed(fights_data, output_dir="./initdb/"):
    """Generate SQL seed file for fights table"""
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/13_fights_from_json_seed.sql"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write("-- Seed data for fights table from JSON files\n")
        f.write(f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Add statement to disable triggers temporarily
        f.write("-- Temporarily disable triggers\n")
        f.write("ALTER TABLE fights DISABLE TRIGGER ALL;\n\n")
        
        # Write INSERT statements
        for fight in fights_data:
            f.write(f"""INSERT INTO fights (
  fight_id, event_id, fight_url, status, referee, 
  fighter1_id, fighter2_id, fighter1_result, fighter2_result, final_method
) VALUES (
  {sanitize_sql_value(fight['fight_id'])},
  {sanitize_sql_value(fight['event_id'])},
  {sanitize_sql_value(fight['fight_url'])},
  {sanitize_sql_value(fight['status'])},
  {sanitize_sql_value(fight['referee'])},
  {sanitize_sql_value(fight['fighter1_id'])},
  {sanitize_sql_value(fight['fighter2_id'])},
  {sanitize_sql_value(fight['fighter1_result'])},
  {sanitize_sql_value(fight['fighter2_result'])},
  {sanitize_sql_value(fight['final_method'])}
) ON CONFLICT (fight_id) DO UPDATE SET 
  referee = EXCLUDED.referee,
  fighter1_result = EXCLUDED.fighter1_result,
  fighter2_result = EXCLUDED.fighter2_result,
  final_method = EXCLUDED.final_method;

""")
        
        # Re-enable triggers
        f.write("-- Re-enable triggers\n")
        f.write("ALTER TABLE fights ENABLE TRIGGER ALL;\n")
    
    print(f"Fights SQL seed file generated: {output_file}")

def generate_fight_stats_seed(fight_stats_data, output_dir="./initdb/"):
    """Generate SQL seed file for fight_stats table"""
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/14_fight_stats_seed.sql"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write("-- Seed data for fight_stats table from JSON files\n")
        f.write(f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Add statement to disable triggers temporarily
        f.write("-- Temporarily disable triggers\n")
        f.write("ALTER TABLE fight_stats DISABLE TRIGGER ALL;\n\n")
        
        # Write INSERT statements
        for stats in fight_stats_data:
            f.write(f"""INSERT INTO fight_stats (
  fight_id, fighter_id, kd, 
  sig_strikes_landed, sig_strikes_attempted, sig_strikes_accuracy,
  head_strikes_landed, head_strikes_attempted,
  body_strikes_landed, body_strikes_attempted,
  leg_strikes_landed, leg_strikes_attempted,
  distance_strikes_landed, distance_strikes_attempted,
  clinch_strikes_landed, clinch_strikes_attempted,
  ground_strikes_landed, ground_strikes_attempted,
  total_strikes_landed, total_strikes_attempted, total_strikes_accuracy,
  td_landed, td_attempted, td_accuracy,
  sub_att, reversals, ctrl
) VALUES (
  {sanitize_sql_value(stats['fight_id'])},
  {sanitize_sql_value(stats['fighter_id'])},
  {sanitize_sql_value(stats['kd'])},
  {sanitize_sql_value(stats['sig_strikes_landed'])},
  {sanitize_sql_value(stats['sig_strikes_attempted'])},
  {sanitize_sql_value(stats['sig_strikes_accuracy'])},
  {sanitize_sql_value(stats['head_strikes_landed'])},
  {sanitize_sql_value(stats['head_strikes_attempted'])},
  {sanitize_sql_value(stats['body_strikes_landed'])},
  {sanitize_sql_value(stats['body_strikes_attempted'])},
  {sanitize_sql_value(stats['leg_strikes_landed'])},
  {sanitize_sql_value(stats['leg_strikes_attempted'])},
  {sanitize_sql_value(stats['distance_strikes_landed'])},
  {sanitize_sql_value(stats['distance_strikes_attempted'])},
  {sanitize_sql_value(stats['clinch_strikes_landed'])},
  {sanitize_sql_value(stats['clinch_strikes_attempted'])},
  {sanitize_sql_value(stats['ground_strikes_landed'])},
  {sanitize_sql_value(stats['ground_strikes_attempted'])},
  {sanitize_sql_value(stats['total_strikes_landed'])},
  {sanitize_sql_value(stats['total_strikes_attempted'])},
  {sanitize_sql_value(stats['total_strikes_accuracy'])},
  {sanitize_sql_value(stats['td_landed'])},
  {sanitize_sql_value(stats['td_attempted'])},
  {sanitize_sql_value(stats['td_accuracy'])},
  {sanitize_sql_value(stats['sub_att'])},
  {sanitize_sql_value(stats['reversals'])},
  {sanitize_sql_value(stats['ctrl'])}
) ON CONFLICT (fight_id, fighter_id) DO UPDATE SET 
  kd = EXCLUDED.kd,
  sig_strikes_landed = EXCLUDED.sig_strikes_landed,
  sig_strikes_attempted = EXCLUDED.sig_strikes_attempted,
  sig_strikes_accuracy = EXCLUDED.sig_strikes_accuracy,
  head_strikes_landed = EXCLUDED.head_strikes_landed,
  head_strikes_attempted = EXCLUDED.head_strikes_attempted,
  body_strikes_landed = EXCLUDED.body_strikes_landed,
  body_strikes_attempted = EXCLUDED.body_strikes_attempted,
  leg_strikes_landed = EXCLUDED.leg_strikes_landed,
  leg_strikes_attempted = EXCLUDED.leg_strikes_attempted,
  distance_strikes_landed = EXCLUDED.distance_strikes_landed,
  distance_strikes_attempted = EXCLUDED.distance_strikes_attempted,
  clinch_strikes_landed = EXCLUDED.clinch_strikes_landed,
  clinch_strikes_attempted = EXCLUDED.clinch_strikes_attempted,
  ground_strikes_landed = EXCLUDED.ground_strikes_landed,
  ground_strikes_attempted = EXCLUDED.ground_strikes_attempted,
  total_strikes_landed = EXCLUDED.total_strikes_landed,
  total_strikes_attempted = EXCLUDED.total_strikes_attempted,
  total_strikes_accuracy = EXCLUDED.total_strikes_accuracy,
  td_landed = EXCLUDED.td_landed,
  td_attempted = EXCLUDED.td_attempted,
  td_accuracy = EXCLUDED.td_accuracy,
  sub_att = EXCLUDED.sub_att,
  reversals = EXCLUDED.reversals,
  ctrl = EXCLUDED.ctrl;

""")
        
        # Re-enable triggers
        f.write("-- Re-enable triggers\n")
        f.write("ALTER TABLE fight_stats ENABLE TRIGGER ALL;\n")
    
    print(f"Fight stats SQL seed file generated: {output_file}")

def generate_round_stats_seed(fights_data, output_dir="./initdb/"):
    """Generate SQL seed file for round_stats table"""
    # This would require parsing the rounds data from the JSON
    # For brevity, we'll skip this implementation for now
    pass

if __name__ == "__main__":
    print("Extracting fight data and statistics from JSON files...")
    fights_data, fight_stats_data = extract_fights_and_stats()
    
    print("Generating SQL seed files...")
    output_dir = "./initdb/"
    os.makedirs(output_dir, exist_ok=True)
    
    generate_fights_seed(fights_data, output_dir)
    generate_fight_stats_seed(fight_stats_data, output_dir)
    
    print("Done!")