#!/usr/bin/env python3
import os
import json
import glob
from datetime import datetime

def sanitize(value):
    """Sanitize values for SQL insertion"""
    if value is None:
        return "NULL"
    if isinstance(value, str):
        # Replace single quotes with two single quotes to escape them in SQL
        return f"'{value.replace('\'', '\'\'')}'"
    return str(value)

def convert_date_to_timestamptz(date_str):
    """Convert YYYY-MM-DD to timestamptz format"""
    if not date_str or date_str == "NULL":
        return "NULL"
    return f"'{date_str}T00:00:00Z'::TIMESTAMPTZ"

def process_json_files():
    """Process JSON files and generate SQL seed files"""
    # Output directories
    output_dir = './initdb/seed/stats/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Initialize SQL files
    fighter_stats_sql = open(f"{output_dir}fighter_stats_seed.sql", 'w')
    round_stats_sql = open(f"{output_dir}round_stats_seed.sql", 'w')
    
    # Write headers
    fighter_stats_sql.write("-- Seed data for fighter_stats table (merged from pre_comp_stats)\n")
    fighter_stats_sql.write(f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    round_stats_sql.write("-- Seed data for round_stats table (updated schema without time field)\n")
    round_stats_sql.write(f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # Process each JSON file
    json_files = glob.glob('./data/raw/stats/event_dumps/*.json')
    total_files = len(json_files)
    
    print(f"Found {total_files} JSON files to process")
    
    # Keep track of unique entries to avoid duplicates
    processed_fighter_stats = set()
    processed_round_stats = set()
    
    for idx, json_file in enumerate(json_files, 1):
        print(f"Processing file {idx}/{total_files}: {os.path.basename(json_file)}")
        
        try:
            with open(json_file, 'r') as f:
                event_data = json.load(f)
                
            # Get event info
            event_id = event_data.get('event_id')
            event_date = event_data.get('date')
            
            if not event_id or not event_date:
                print(f"  Skipping file {json_file} - missing event_id or date")
                continue
            
            # Process fights
            fights = event_data.get('fights', [])
            for fight in fights:
                fight_id = fight.get('fight_id')
                if not fight_id:
                    continue
                
                # Process fighters
                for fighter_key in ['fighter1', 'fighter2']:
                    fighter_data = fight.get(fighter_key, {})
                    fighter_id = fighter_data.get('id')
                    if not fighter_id:
                        continue
                    
                    # Process pre_comp_stats into fighter_stats
                    pre_comp = fighter_data.get('pre_comp', {})
                    for stat_type, stats in pre_comp.items():
                        if not stats:
                            continue
                        
                        # Create a unique key to avoid duplicates
                        unique_key = f"{fighter_id}_{fight_id}_{stat_type}"
                        if unique_key in processed_fighter_stats:
                            continue
                            
                        processed_fighter_stats.add(unique_key)
                        
                        # Start building the values for the SQL statement
                        columns = ["fighter_id", "timestamp", "fight_id"]
                        values = [
                            sanitize(fighter_id),
                            convert_date_to_timestamptz(event_date),
                            sanitize(fight_id)
                        ]
                        
                        # Add all available stat fields from the pre_comp data
                        # Knockdowns
                        if isinstance(stats.get('knockdowns'), dict):
                            knockdowns = stats.get('knockdowns', {})
                            if knockdowns.get('avg') is not None:
                                columns.append('knockdowns_avg')
                                values.append(sanitize(knockdowns.get('avg')))
                            if knockdowns.get('differential') is not None:
                                columns.append('knockdowns_diff')
                                values.append(sanitize(knockdowns.get('differential')))
                        
                        # Submission attempts
                        if isinstance(stats.get('sub_attempts'), dict):
                            sub_attempts = stats.get('sub_attempts', {})
                            if sub_attempts.get('avg') is not None:
                                columns.append('sub_attempts_avg')
                                values.append(sanitize(sub_attempts.get('avg')))
                            if sub_attempts.get('differential') is not None:
                                columns.append('sub_attempts_diff')
                                values.append(sanitize(sub_attempts.get('differential')))
                            if sub_attempts.get('per_min') is not None:
                                columns.append('sub_attempts_per_min')
                                values.append(sanitize(sub_attempts.get('per_min')))
                        
                        # Reversals
                        if isinstance(stats.get('reversals'), dict):
                            reversals = stats.get('reversals', {})
                            if reversals.get('avg') is not None:
                                columns.append('reversals_avg')
                                values.append(sanitize(reversals.get('avg')))
                            if reversals.get('differential') is not None:
                                columns.append('reversals_diff')
                                values.append(sanitize(reversals.get('differential')))
                        
                        # Control time
                        if isinstance(stats.get('control'), dict):
                            control = stats.get('control', {})
                            if control.get('avg') is not None:
                                columns.append('ctrl_avg')
                                values.append(sanitize(control.get('avg')))
                            if control.get('differential') is not None:
                                columns.append('ctrl_diff')
                                values.append(sanitize(control.get('differential')))
                        
                        # Takedowns
                        if isinstance(stats.get('takedowns'), dict):
                            takedowns = stats.get('takedowns', {})
                            # Landed
                            td_landed = takedowns.get('landed', {})
                            if isinstance(td_landed, dict):
                                if td_landed.get('avg') is not None:
                                    columns.append('td_landed_avg')
                                    values.append(sanitize(td_landed.get('avg')))
                                if td_landed.get('differential') is not None:
                                    columns.append('td_landed_diff')
                                    values.append(sanitize(td_landed.get('differential')))
                                if td_landed.get('per_min') is not None:
                                    columns.append('td_landed_per_min')
                                    values.append(sanitize(td_landed.get('per_min')))
                            
                            # Attempted
                            td_attempts = takedowns.get('attempts', {})
                            if isinstance(td_attempts, dict):
                                if td_attempts.get('avg') is not None:
                                    columns.append('td_attempts_avg')
                                    values.append(sanitize(td_attempts.get('avg')))
                                if td_attempts.get('differential') is not None:
                                    columns.append('td_attempts_diff')
                                    values.append(sanitize(td_attempts.get('differential')))
                                if td_attempts.get('per_min') is not None:
                                    columns.append('td_attempts_per_min')
                                    values.append(sanitize(td_attempts.get('per_min')))
                            
                            # Accuracy
                            td_accuracy = takedowns.get('accuracy', {})
                            if isinstance(td_accuracy, dict):
                                if td_accuracy.get('avg') is not None:
                                    columns.append('td_accuracy')
                                    values.append(sanitize(td_accuracy.get('avg')))
                                if td_accuracy.get('differential') is not None:
                                    columns.append('td_accuracy_diff')
                                    values.append(sanitize(td_accuracy.get('differential')))
                            
                            # Defense
                            td_def = takedowns.get('defense', {})
                            if isinstance(td_def, dict):
                                if td_def.get('avg') is not None:
                                    columns.append('td_def')
                                    values.append(sanitize(td_def.get('avg')))
                                if td_def.get('differential') is not None:
                                    columns.append('td_def_diff')
                                    values.append(sanitize(td_def.get('differential')))
                        
                        # Significant Strikes
                        if isinstance(stats.get('sig_strikes'), dict):
                            sig_strikes = stats.get('sig_strikes', {})
                            # Landed
                            sig_landed = sig_strikes.get('landed', {})
                            if isinstance(sig_landed, dict):
                                if sig_landed.get('avg') is not None:
                                    columns.append('sig_strikes_landed_avg')
                                    values.append(sanitize(sig_landed.get('avg')))
                                if sig_landed.get('differential') is not None:
                                    columns.append('sig_strikes_landed_diff')
                                    values.append(sanitize(sig_landed.get('differential')))
                                if sig_landed.get('per_min') is not None:
                                    columns.append('sig_strikes_landed_per_min')
                                    values.append(sanitize(sig_landed.get('per_min')))
                            
                            # Attempts
                            sig_attempts = sig_strikes.get('attempts', {})
                            if isinstance(sig_attempts, dict):
                                if sig_attempts.get('avg') is not None:
                                    columns.append('sig_strikes_attempts_avg')
                                    values.append(sanitize(sig_attempts.get('avg')))
                                if sig_attempts.get('differential') is not None:
                                    columns.append('sig_strikes_attempts_diff')
                                    values.append(sanitize(sig_attempts.get('differential')))
                                if sig_attempts.get('per_min') is not None:
                                    columns.append('sig_strikes_attempts_per_min')
                                    values.append(sanitize(sig_attempts.get('per_min')))
                            
                            # Accuracy
                            sig_accuracy = sig_strikes.get('accuracy', {})
                            if isinstance(sig_accuracy, dict):
                                if sig_accuracy.get('avg') is not None:
                                    columns.append('sig_strikes_accuracy')
                                    values.append(sanitize(sig_accuracy.get('avg')))
                                if sig_accuracy.get('differential') is not None:
                                    columns.append('sig_strikes_accuracy_diff')
                                    values.append(sanitize(sig_accuracy.get('differential')))
                            
                            # Defense
                            sig_def = sig_strikes.get('defense', {})
                            if isinstance(sig_def, dict):
                                if sig_def.get('avg') is not None:
                                    columns.append('sig_strikes_def_avg')
                                    values.append(sanitize(sig_def.get('avg')))
                                if sig_def.get('differential') is not None:
                                    columns.append('sig_strikes_def_diff')
                                    values.append(sanitize(sig_def.get('differential')))
                        
                        # Add more mappings for additional stats as needed
                        
                        # Write the SQL insert statement
                        if len(columns) > 3:  # Only if we have actual stats beyond the IDs
                            fighter_stats_sql.write(
                                f"INSERT INTO fighter_stats ({', '.join(columns)}) VALUES (\n"
                                f"  {', '.join(values)}\n"
                                f");\n\n"
                            )
                    
                    # Process round_stats (without time field)
                    rounds = fighter_data.get('rounds', {})
                    for round_name, round_data in rounds.items():
                        if not round_name.startswith('round'):
                            continue
                            
                        try:
                            round_number = int(round_name.replace('round', ''))
                        except:
                            continue
                        
                        # Create a unique key to avoid duplicates
                        unique_key = f"{fight_id}_{fighter_id}_{round_number}"
                        if unique_key in processed_round_stats:
                            continue
                            
                        processed_round_stats.add(unique_key)
                        
                        # Extract stats for this round
                        r_kd = round_data.get('KD', 0)
                        r_sig_str = round_data.get('Sig. str.', {})
                        r_sig_landed = r_sig_str.get('landed', 0)
                        r_sig_attempted = r_sig_str.get('attempted', 0)
                        r_sig_accuracy = round_data.get('Sig. str. %')
                        
                        # Total strikes
                        r_total_str = round_data.get('Total str.', {})
                        r_total_landed = r_total_str.get('landed', 0)
                        r_total_attempted = r_total_str.get('attempted', 0)
                        
                        # Takedowns
                        r_td = round_data.get('Td', {})
                        r_td_landed = r_td.get('landed', 0)
                        r_td_attempted = r_td.get('attempted', 0)
                        r_td_accuracy = round_data.get('Td %')
                        if r_td_accuracy == '---':
                            r_td_accuracy = None
                            
                        # Other stats
                        r_sub_att = round_data.get('Sub. att', 0)
                        r_rev = round_data.get('Rev.', 0)
                        r_ctrl_time = round_data.get('Ctrl', '0')
                        r_ctrl_seconds = r_ctrl_time if isinstance(r_ctrl_time, int) else 0
                        
                        # Write to round_stats table - REMOVED time parameter
                        round_stats_sql.write(
                            f"INSERT INTO round_stats (fight_id, fighter_id, round_number, kd, sig_strikes_landed, "
                            f"sig_strikes_attempted, sig_strikes_accuracy, total_strikes_landed, total_strikes_attempted, "
                            f"td_landed, td_attempted, td_accuracy, sub_att, reversals, ctrl) VALUES (\n"
                            f"  {sanitize(fight_id)},\n"
                            f"  {sanitize(fighter_id)},\n"
                            f"  {sanitize(round_number)},\n"
                            f"  {sanitize(r_kd)},\n"
                            f"  {sanitize(r_sig_landed)},\n"
                            f"  {sanitize(r_sig_attempted)},\n"
                            f"  {sanitize(r_sig_accuracy)},\n"
                            f"  {sanitize(r_total_landed)},\n"
                            f"  {sanitize(r_total_attempted)},\n"
                            f"  {sanitize(r_td_landed)},\n"
                            f"  {sanitize(r_td_attempted)},\n"
                            f"  {sanitize(r_td_accuracy)},\n"
                            f"  {sanitize(r_sub_att)},\n"
                            f"  {sanitize(r_rev)},\n"
                            f"  {sanitize(r_ctrl_seconds)}\n"
                            f");\n\n"
                        )
                    
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            import traceback
            traceback.print_exc()
    
    # Close SQL files
    fighter_stats_sql.close()
    round_stats_sql.close()
    
    print(f"\nProcessing complete!")
    print(f"Generated {len(processed_fighter_stats)} fighter_stats entries from pre_comp data")
    print(f"Generated {len(processed_round_stats)} updated round_stats entries")

if __name__ == "__main__":
    process_json_files()