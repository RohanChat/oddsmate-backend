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
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)

def convert_control_time(ctrl_str):
    """Convert control time string (like '1:08') to seconds"""
    if not ctrl_str or ctrl_str == "NULL":
        return 0
    
    try:
        parts = ctrl_str.split(':')
        if len(parts) == 2:
            minutes, seconds = parts
            return int(minutes) * 60 + int(seconds)
    except Exception:
        pass
    
    return 0

def parseRecordString(record_str):
    """Parse a record string like '31-13-0' into wins, losses, draws"""
    if not record_str:
        return None, None, None
    
    parts = record_str.split('-')
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    return None, None, None

def process_json_files():
    # Output directories
    output_dir = './initdb/seed/stats/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Initialize SQL files
    table_files = {
        'events': open(f"{output_dir}events_seed.sql", 'w'),
        'fights': open(f"{output_dir}fights_seed.sql", 'w'),
        'fighters': open(f"{output_dir}fighters_seed.sql", 'w'),
        'fighter_stats': open(f"{output_dir}fighter_stats_seed.sql", 'w'),
        'fight_stats': open(f"{output_dir}fight_stats_seed.sql", 'w'),
        'round_stats': open(f"{output_dir}round_stats_seed.sql", 'w'),
        'pre_comp_stats': open(f"{output_dir}pre_comp_stats_seed.sql", 'w')
    }
    
    # Write header to each file
    for name, file in table_files.items():
        file.write(f"-- Seed data for {name} table\n")
        file.write(f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # Keep track of unique fighter IDs to avoid duplicates
    unique_fighters = set()
    unique_fighter_stats = set()
    
    # Process each JSON file
    json_files = glob.glob('./data/raw/stats/event_dumps/*.json')
    total_files = len(json_files)
    
    for idx, json_file in enumerate(json_files, 1):
        print(f"Processing file {idx}/{total_files}: {os.path.basename(json_file)}")
        
        try:
            with open(json_file, 'r') as f:
                event_data = json.load(f)
                
            # Process event data
            event_id = event_data.get('event_id')
            event_date = event_data.get('date')
            location = event_data.get('location', {})
            location_name = location.get('name', '')
            coordinates = location.get('coordinates', {})
            lat, lng = coordinates.get('lat'), coordinates.get('lng')
            point = f"({lat},{lng})" if lat and lng else "NULL"
            elevation = location.get('elevation', 'NULL')
            
            # Write to events table
            table_files['events'].write(
                f"INSERT INTO events (event_id, date, name, location_name, location, elevation, event_url) VALUES (\n"
                f"  {sanitize(event_id)},\n"
                f"  {sanitize(event_date)},\n"
                f"  {sanitize(location_name.split(',')[0] if location_name else '')},\n"
                f"  {sanitize(location_name)},\n"
                f"  {point},\n"
                f"  {elevation},\n"
                f"  {sanitize(f'http://ufcstats.com/event-details/{event_id}')}\n"
                f");\n\n"
            )
            
            # Process fights
            fights = event_data.get('fights', [])
            for fight in fights:
                fight_id = fight.get('fight_id')
                method = fight.get('method')
                round_num = fight.get('round')
                time = fight.get('time')
                time_format = fight.get('time_format')
                referee = fight.get('referee')
                
                # Get fighter IDs
                fighter1 = fight.get('fighter1', {})
                fighter2 = fight.get('fighter2', {})
                fighter1_id = fighter1.get('id')
                fighter2_id = fighter2.get('id')
                
                # Write to fights table
                table_files['fights'].write(
                    f"INSERT INTO fights (fight_id, event_id, fight_url, status, referee, fighter1_id, fighter2_id, final_method) VALUES (\n"
                    f"  {sanitize(fight_id)},\n"
                    f"  {sanitize(event_id)},\n"
                    f"  {sanitize(f'http://ufcstats.com/fight-details/{fight_id}')},\n"
                    f"  'finished',\n"
                    f"  {sanitize(referee)},\n"
                    f"  {sanitize(fighter1_id)},\n"
                    f"  {sanitize(fighter2_id)},\n"
                    f"  {sanitize(method)}\n"
                    f");\n\n"
                )
                
                # Process both fighters
                for fighter_side, fighter_data in [('fighter1', fighter1), ('fighter2', fighter2)]:
                    fighter_id = fighter_data.get('id')
                    if not fighter_id:
                        continue
                    
                    # Only process each fighter once
                    if fighter_id not in unique_fighters:
                        unique_fighters.add(fighter_id)
                        
                        name = fighter_data.get('name')
                        nickname = fighter_data.get('nickname')
                        
                        # Convert DOB from DD/MM/YYYY to YYYY-MM-DD
                        dob = fighter_data.get('dob')
                        if dob and len(dob.split('/')) == 3:
                            day, month, year = dob.split('/')
                            dob = f"{year}-{month}-{day}"
                        
                        height = fighter_data.get('height')
                        weight = fighter_data.get('weight')
                        reach = fighter_data.get('reach')
                        stance = fighter_data.get('stance')
                        
                        # Write to fighters table
                        table_files['fighters'].write(
                            f"INSERT INTO fighters (fighter_id, name, nickname, dob, height, weight, reach, stance) VALUES (\n"
                            f"  {sanitize(fighter_id)},\n"
                            f"  {sanitize(name)},\n"
                            f"  {sanitize(nickname) if nickname else 'NULL'},\n"
                            f"  {sanitize(dob) if dob else 'NULL'},\n"
                            f"  {sanitize(height) if height else 'NULL'},\n"
                            f"  {sanitize(weight) if weight else 'NULL'},\n"
                            f"  {sanitize(reach) if reach else 'NULL'},\n"
                            f"  {sanitize(stance) if stance else 'NULL'}\n"
                            f");\n\n"
                        )
                    
                    # Process fighter stats
                    stats = fighter_data.get('stats', {})
                    timestamp = fighter_data.get('timestamp')
                    record = stats.get('record', {})
                    wins = record.get('wins')
                    losses = record.get('losses')
                    draws = record.get('draws')
                    
                    # Create a unique key for fighter_stats
                    fighter_stats_key = f"{fighter_id}_{timestamp}"
                    if fighter_stats_key not in unique_fighter_stats and timestamp:
                        unique_fighter_stats.add(fighter_stats_key)
                        
                        # Map the stats fields
                        slpm = stats.get('SLpM')
                        str_acc = stats.get('Str. Acc.:')
                        sapm = stats.get('SApM')
                        td_avg = stats.get('TD. Avg.')
                        td_acc = stats.get('TD. Acc.')
                        td_def = stats.get('TD, Def')
                        sub_avg = stats.get('Sub. Avg.')
                        
                        # Write to fighter_stats table
                        table_files['fighter_stats'].write(
                            f"INSERT INTO fighter_stats (fighter_id, timestamp, wins, losses, draws, "
                            f"sig_strikes_landed_per_min, sig_strikes_accuracy, sig_strikes_absorbed_permin, "
                            f"td_landed_avg, td_accuracy, td_def, sub_attempts_avg) VALUES (\n"
                            f"  {sanitize(fighter_id)},\n"
                            f"  {sanitize(timestamp)},\n"
                            f"  {sanitize(wins) if wins is not None else 'NULL'},\n"
                            f"  {sanitize(losses) if losses is not None else 'NULL'},\n"
                            f"  {sanitize(draws) if draws is not None else 'NULL'},\n"
                            f"  {sanitize(slpm) if slpm is not None else 'NULL'},\n"
                            f"  {sanitize(str_acc) if str_acc is not None else 'NULL'},\n"
                            f"  {sanitize(sapm) if sapm is not None else 'NULL'},\n"
                            f"  {sanitize(td_avg) if td_avg is not None else 'NULL'},\n"
                            f"  {sanitize(td_acc) if td_acc is not None else 'NULL'},\n"
                            f"  {sanitize(td_def) if td_def is not None else 'NULL'},\n"
                            f"  {sanitize(sub_avg) if sub_avg is not None else 'NULL'}\n"
                            f");\n\n"
                        )
                    
                    # Process fight stats
                    kd = fighter_data.get('KD', 0)
                    sig_str = fighter_data.get('Sig. str.', {})
                    sig_landed = sig_str.get('landed', 0)
                    sig_attempted = sig_str.get('attempted', 0)
                    sig_accuracy = fighter_data.get('Sig. str. %')
                    
                    # Extract strike breakdowns
                    head = sig_str.get('Head', {})
                    body = sig_str.get('Body', {})
                    leg = sig_str.get('Leg', {})
                    distance = sig_str.get('Distance', {})
                    clinch = sig_str.get('Clinch', {})
                    ground = sig_str.get('Ground', {})
                    
                    head_landed = head.get('landed', 0)
                    head_attempted = head.get('attempted', 0)
                    body_landed = body.get('landed', 0)
                    body_attempted = body.get('attempted', 0)
                    leg_landed = leg.get('landed', 0)
                    leg_attempted = leg.get('attempted', 0)
                    distance_landed = distance.get('landed', 0)
                    distance_attempted = distance.get('attempted', 0)
                    clinch_landed = clinch.get('landed', 0)
                    clinch_attempted = clinch.get('attempted', 0)
                    ground_landed = ground.get('landed', 0)
                    ground_attempted = ground.get('attempted', 0)
                    
                    # Total strikes
                    total_str = fighter_data.get('Total str.', {})
                    total_landed = total_str.get('landed', 0)
                    total_attempted = total_str.get('attempted', 0)
                    
                    # Takedowns
                    td = fighter_data.get('Td', {})
                    td_landed = td.get('landed', 0)
                    td_attempted = td.get('attempted', 0)
                    td_accuracy = fighter_data.get('Td %')
                    if td_accuracy == '---':
                        td_accuracy = None
                        
                    # Other stats
                    sub_att = fighter_data.get('Sub. att', 0)
                    if isinstance(sub_att, str):
                        try:
                            sub_att = int(sub_att)
                        except:
                            sub_att = 0
                            
                    rev = fighter_data.get('Rev.', 0)
                    if isinstance(rev, str):
                        try:
                            rev = int(rev)
                        except:
                            rev = 0
                            
                    ctrl_time = fighter_data.get('Ctrl', '0:00')
                    ctrl_seconds = convert_control_time(ctrl_time)
                    
                    # Write to fight_stats table
                    table_files['fight_stats'].write(
                        f"INSERT INTO fight_stats (fight_id, fighter_id, kd, sig_strikes_landed, sig_strikes_attempted, "
                        f"sig_strikes_accuracy, head_strikes_landed, head_strikes_attempted, body_strikes_landed, "
                        f"body_strikes_attempted, leg_strikes_landed, leg_strikes_attempted, distance_strikes_landed, "
                        f"distance_strikes_attempted, clinch_strikes_landed, clinch_strikes_attempted, ground_strikes_landed, "
                        f"ground_strikes_attempted, total_strikes_landed, total_strikes_attempted, td_landed, td_attempted, "
                        f"td_accuracy, sub_att, reversals, ctrl) VALUES (\n"
                        f"  {sanitize(fight_id)},\n"
                        f"  {sanitize(fighter_id)},\n"
                        f"  {sanitize(kd)},\n"
                        f"  {sanitize(sig_landed)},\n"
                        f"  {sanitize(sig_attempted)},\n"
                        f"  {sanitize(sig_accuracy)},\n"
                        f"  {sanitize(head_landed)},\n"
                        f"  {sanitize(head_attempted)},\n"
                        f"  {sanitize(body_landed)},\n"
                        f"  {sanitize(body_attempted)},\n"
                        f"  {sanitize(leg_landed)},\n"
                        f"  {sanitize(leg_attempted)},\n"
                        f"  {sanitize(distance_landed)},\n"
                        f"  {sanitize(distance_attempted)},\n"
                        f"  {sanitize(clinch_landed)},\n"
                        f"  {sanitize(clinch_attempted)},\n"
                        f"  {sanitize(ground_landed)},\n"
                        f"  {sanitize(ground_attempted)},\n"
                        f"  {sanitize(total_landed)},\n"
                        f"  {sanitize(total_attempted)},\n"
                        f"  {sanitize(td_landed)},\n"
                        f"  {sanitize(td_attempted)},\n"
                        f"  {sanitize(td_accuracy)},\n"
                        f"  {sanitize(sub_att)},\n"
                        f"  {sanitize(rev)},\n"
                        f"  {sanitize(ctrl_seconds)}\n"
                        f");\n\n"
                    )
                    
                    # Process round stats
                    rounds = fighter_data.get('rounds', {})
                    for round_name, round_data in rounds.items():
                        if not round_name.startswith('round'):
                            continue
                            
                        # Extract round number (e.g. 'round1' -> 1)
                        try:
                            round_number = int(round_name.replace('round', ''))
                        except:
                            continue
                            
                        # Extract stats for this round
                        r_kd = round_data.get('KD', 0)
                        r_sig_str = round_data.get('Sig. str.', {})
                        r_sig_landed = r_sig_str.get('landed', 0)
                        r_sig_attempted = r_sig_str.get('attempted', 0)
                        r_sig_accuracy = round_data.get('Sig. str. %')
                        
                        # Total strikes for round
                        r_total_str = round_data.get('Total str.', {})
                        r_total_landed = r_total_str.get('landed', 0)
                        r_total_attempted = r_total_str.get('attempted', 0)
                        
                        # Takedowns for round
                        r_td = round_data.get('Td', {})
                        r_td_landed = r_td.get('landed', 0)
                        r_td_attempted = r_td.get('attempted', 0)
                        r_td_accuracy = round_data.get('Td %')
                        if r_td_accuracy == '---':
                            r_td_accuracy = None
                            
                        # Other round stats
                        r_sub_att = round_data.get('Sub. att', 0)
                        r_rev = round_data.get('Rev.', 0)
                        r_ctrl_time = round_data.get('Ctrl', '0')
                        r_ctrl_seconds = r_ctrl_time if isinstance(r_ctrl_time, int) else convert_control_time(str(r_ctrl_time))
                        
                        # Write to round_stats table - use 0 for time since we don't have it per round
                        table_files['round_stats'].write(
                            f"INSERT INTO round_stats (fight_id, fighter_id, round_number, time, kd, sig_strikes_landed, "
                            f"sig_strikes_attempted, sig_strikes_accuracy, total_strikes_landed, total_strikes_attempted, "
                            f"td_landed, td_attempted, td_accuracy, sub_att, reversals, ctrl) VALUES (\n"
                            f"  {sanitize(fight_id)},\n"
                            f"  {sanitize(fighter_id)},\n"
                            f"  {sanitize(round_number)},\n"
                            f"  0,\n"  # Time set to 0
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
                    
                    # Process pre_comp_stats
                    pre_comp = fighter_data.get('pre_comp', {})
                    for stat_type, stats_data in pre_comp.items():
                        if not stats_data:  # Skip empty stats
                            continue
                            
                        # Process all the pre-comp stats fields
                        # First initialize with NULL defaults
                        pre_comp_values = {
                            'knockdowns_avg': 'NULL',
                            'knockdowns_diff': 'NULL',
                            'sub_attempts_avg': 'NULL',
                            'sub_attempts_diff': 'NULL',
                            'sub_attempts_per_min': 'NULL',
                            'reversals_avg': 'NULL',
                            'reversals_diff': 'NULL',
                            'ctrl_avg': 'NULL',
                            'ctrl_diff': 'NULL',
                            # ... add other fields with NULL defaults
                        }
                        
                        # Now extract the actual values
                        knockdowns = stats_data.get('knockdowns', {})
                        if isinstance(knockdowns, dict):
                            pre_comp_values['knockdowns_avg'] = sanitize(knockdowns.get('avg'))
                            pre_comp_values['knockdowns_diff'] = sanitize(knockdowns.get('differential'))
                        elif knockdowns is not None:
                            pre_comp_values['knockdowns_avg'] = sanitize(knockdowns)
                        
                        sub_attempts = stats_data.get('sub_attempts', {})
                        if isinstance(sub_attempts, dict):
                            pre_comp_values['sub_attempts_avg'] = sanitize(sub_attempts.get('avg'))
                            pre_comp_values['sub_attempts_diff'] = sanitize(sub_attempts.get('differential'))
                            pre_comp_values['sub_attempts_per_min'] = sanitize(sub_attempts.get('per_min'))
                        elif sub_attempts is not None:
                            pre_comp_values['sub_attempts_avg'] = sanitize(sub_attempts)
                        
                        reversals = stats_data.get('reversals', {})
                        if isinstance(reversals, dict):
                            pre_comp_values['reversals_avg'] = sanitize(reversals.get('avg'))
                            pre_comp_values['reversals_diff'] = sanitize(reversals.get('differential'))
                        elif reversals is not None:
                            pre_comp_values['reversals_avg'] = sanitize(reversals)
                        
                        control = stats_data.get('control', {})
                        if isinstance(control, dict):
                            pre_comp_values['ctrl_avg'] = sanitize(control.get('avg'))
                            pre_comp_values['ctrl_diff'] = sanitize(control.get('differential'))
                        elif control is not None:
                            pre_comp_values['ctrl_avg'] = sanitize(control)
                        
                        # Write to pre_comp_stats table (simplified for example)
                        table_files['pre_comp_stats'].write(
                            f"INSERT INTO pre_comp_stats (fight_id, fighter_id, stat_type, "
                            f"knockdowns_avg, knockdowns_diff, "
                            f"sub_attempts_avg, sub_attempts_diff, sub_attempts_per_min, "
                            f"reversals_avg, reversals_diff, "
                            f"ctrl_avg, ctrl_diff) VALUES (\n"
                            f"  {sanitize(fight_id)},\n"
                            f"  {sanitize(fighter_id)},\n"
                            f"  {sanitize(stat_type)},\n"
                            f"  {pre_comp_values['knockdowns_avg']},\n"
                            f"  {pre_comp_values['knockdowns_diff']},\n"
                            f"  {pre_comp_values['sub_attempts_avg']},\n"
                            f"  {pre_comp_values['sub_attempts_diff']},\n"
                            f"  {pre_comp_values['sub_attempts_per_min']},\n"
                            f"  {pre_comp_values['reversals_avg']},\n"
                            f"  {pre_comp_values['reversals_diff']},\n"
                            f"  {pre_comp_values['ctrl_avg']},\n"
                            f"  {pre_comp_values['ctrl_diff']}\n"
                            f");\n\n"
                        )
                    
        except Exception as e:
            print(f"Error processing file {json_file}: {e}")
    
    # Close all files
    for file in table_files.values():
        file.close()
    
    print("Processing complete. Seed files generated in initdb/seed/.")

if __name__ == "__main__":
    process_json_files()