#!/usr/bin/env python3
# filepath: /Users/rohan/Desktop/oddsmate-backend/initdb/fix_results.py

import os
import json
import re
import glob

def traverse_and_extract_results():
    """
    Traverse through all JSON files in data/raw/stats/event_dumps/
    and extract fight results
    Returns a dictionary of {fight_id: {fighter1_id: result1, fighter2_id: result2}}
    """
    base_dir = "./data/raw/stats/event_dumps/"
    fight_results = {}
    
    # Find all JSON files in the directory and subdirectories
    json_files = glob.glob(f"{base_dir}**/*.json", recursive=True)
    print(f"Found {len(json_files)} JSON files")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle event JSON files with multiple fights
            if 'fights' in data:
                for fight in data['fights']:
                    fight_id = fight.get('fight_id')
                    if not fight_id:
                        continue
                        
                    fighter1 = fight.get('fighter1', {})
                    fighter2 = fight.get('fighter2', {})
                    
                    fighter1_id = fighter1.get('id')
                    fighter2_id = fighter2.get('id')
                    
                    # Look for results in stats entry
                    fighter1_result = ""
                    fighter2_result = ""
                    
                    # Check in stats for fighter1
                    fighter1_stats = fighter1.get('stats', {})
                    if isinstance(fighter1_stats, dict) and 'result' in fighter1_stats:
                        fighter1_result = fighter1_stats['result']
                    
                    # Check in stats for fighter2
                    fighter2_stats = fighter2.get('stats', {})
                    if isinstance(fighter2_stats, dict) and 'result' in fighter2_stats:
                        fighter2_result = fighter2_stats['result']
                    
                    # If still not found, check in different locations
                    if not fighter1_result:
                        if 'result' in fighter1:
                            fighter1_result = fighter1['result']
                    
                    if not fighter2_result:
                        if 'result' in fighter2:
                            fighter2_result = fighter2['result']
                    
                    # Print debug info for the first few fights
                    if len(fight_results) < 3:
                        print(f"DEBUG: Fight {fight_id}, Fighter1 {fighter1_id}: {fighter1_result}, Fighter2 {fighter2_id}: {fighter2_result}")
                        print(f"Fighter1 keys: {list(fighter1.keys())}")
                        if 'stats' in fighter1:
                            print(f"Fighter1 stats keys: {list(fighter1['stats'].keys()) if isinstance(fighter1['stats'], dict) else 'Not a dict'}")
                    
                    if fighter1_id and fighter2_id:
                        fight_results[fight_id] = {
                            fighter1_id: fighter1_result,
                            fighter2_id: fighter2_result
                        }
            
            # Handle individual fight JSON files
            elif 'fight_id' in data:
                fight_id = data.get('fight_id')
                fighter1 = data.get('fighter1', {})
                fighter2 = data.get('fighter2', {})
                
                fighter1_id = fighter1.get('id')
                fighter2_id = fighter2.get('id')
                
                # Look for results in stats entry
                fighter1_result = ""
                fighter2_result = ""
                
                # Check in stats for fighter1
                fighter1_stats = fighter1.get('stats', {})
                if isinstance(fighter1_stats, dict) and 'result' in fighter1_stats:
                    fighter1_result = fighter1_stats['result']
                
                # Check in stats for fighter2
                fighter2_stats = fighter2.get('stats', {})
                if isinstance(fighter2_stats, dict) and 'result' in fighter2_stats:
                    fighter2_result = fighter2_stats['result']
                
                # If still not found, check in different locations
                if not fighter1_result and 'result' in fighter1:
                    fighter1_result = fighter1['result']
                
                if not fighter2_result and 'result' in fighter2:
                    fighter2_result = fighter2['result']
                
                # Look more deeply in the structure - in case stats is an array of rounds
                if not fighter1_result and isinstance(fighter1_stats, list) and len(fighter1_stats) > 0:
                    for stat_entry in fighter1_stats:
                        if isinstance(stat_entry, dict) and 'result' in stat_entry:
                            fighter1_result = stat_entry['result']
                            break
                
                if not fighter2_result and isinstance(fighter2_stats, list) and len(fighter2_stats) > 0:
                    for stat_entry in fighter2_stats:
                        if isinstance(stat_entry, dict) and 'result' in stat_entry:
                            fighter2_result = stat_entry['result']
                            break
                
                if fighter1_id and fighter2_id:
                    fight_results[fight_id] = {
                        fighter1_id: fighter1_result,
                        fighter2_id: fighter2_result
                    }
                    
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            continue
    
    print(f"Extracted results for {len(fight_results)} fights")
    return fight_results

def process_sql_file(results_map, input_file="./initdb/04_fights_seed.sql", output_file="./initdb/12_results_fix.sql"):
    """
    Process the SQL file and update fighter results
    """
    # Parse the SQL file to extract existing fight information
    fight_data = {}
    missing_fights = []
    updated_fights = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Extract fight information from SQL
    fight_pattern = re.compile(r"INSERT INTO fights \(([^)]+)\) VALUES \(([^;]+)\);")
    
    # Create new SQL content with results
    new_sql_content = []
    new_sql_content.append("-- Fix for fight results")
    new_sql_content.append("-- Generated automatically")
    new_sql_content.append("")
    
    matches = fight_pattern.findall(sql_content)
    
    for columns_str, values_str in matches:
        columns = [col.strip() for col in columns_str.split(',')]
        values = [val.strip() for val in values_str.split(',')]
        
        # Extract fight_id, fighter IDs
        fight_id_idx = columns.index('fight_id') if 'fight_id' in columns else -1
        fighter1_id_idx = columns.index('fighter1_id') if 'fighter1_id' in columns else -1
        fighter2_id_idx = columns.index('fighter2_id') if 'fighter2_id' in columns else -1
        
        if fight_id_idx == -1 or fighter1_id_idx == -1 or fighter2_id_idx == -1:
            print("Column missing in SQL, skipping")
            continue
        
        # Extract IDs from values (removing quotes)
        fight_id = values[fight_id_idx].strip("'")
        fighter1_id = values[fighter1_id_idx].strip("'")
        fighter2_id = values[fighter2_id_idx].strip("'")
        
        # Look up results in our map
        fighter1_result = ""
        fighter2_result = ""
        if fight_id in results_map:
            if fighter1_id in results_map[fight_id]:
                fighter1_result = results_map[fight_id][fighter1_id]
            if fighter2_id in results_map[fight_id]:
                fighter2_result = results_map[fight_id][fighter2_id]
            
            if fighter1_result or fighter2_result:
                updated_fights.append(fight_id)
                # Generate UPDATE statement
                update_sql = f"UPDATE fights SET "
                updates = []
                
                if fighter1_result:
                    updates.append(f"fighter1_result = '{fighter1_result}'")
                if fighter2_result:
                    updates.append(f"fighter2_result = '{fighter2_result}'")
                
                update_sql += ", ".join(updates)
                update_sql += f" WHERE fight_id = '{fight_id}';"
                
                new_sql_content.append(update_sql)
        else:
            missing_fights.append(fight_id)
    
    # Write the new SQL file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_sql_content))
    
    print(f"Updated SQL file written to {output_file}")
    print(f"Missing results for {len(missing_fights)} fights")
    print(f"Updated results for {len(updated_fights)} fights")
    
    return missing_fights, updated_fights

if __name__ == "__main__":
    print("Extracting fight results from JSON files...")
    results_map = traverse_and_extract_results()
    
    print("Updating SQL file with results...")
    missing_fights, updated_fights = process_sql_file(results_map)
    
    # Output some statistics
    total_fights_in_sql = len(missing_fights) + len(updated_fights)
    if total_fights_in_sql > 0:
        print(f"Results coverage: {len(updated_fights)}/{total_fights_in_sql} ({len(updated_fights)/total_fights_in_sql*100:.1f}%)")
    
    # Sample of updated fights
    if updated_fights:
        print("Sample of updated fight IDs:")
        for fight_id in updated_fights[:5]:
            print(f"  {fight_id}")
    
    # Sample of missing fights
    if missing_fights:
        print("Sample of missing fight IDs:")
        for fight_id in missing_fights[:5]:
            print(f"  {fight_id}")