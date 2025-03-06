#!/usr/bin/env python3
# filepath: /Users/rohan/Desktop/oddsmate-backend/fix_round_stats_seed.py

import re
import os

def main():
    input_file = './initdb/05_round_stats_seed.sql'
    output_file = './initdb/05_round_stats_seed_fixed.sql'
    
    # Pattern to extract fight_id, fighter_id, and round_number from complete INSERT statements
    pattern = r"VALUES\s*\(\s*'([^']+)',\s*'([^']+)',\s*(\d+),"
    
    seen_keys = set()  # Store unique (fight_id, fighter_id, round_number) combinations
    valid_statements = []
    current_statement = []
    reading_statement = False
    
    # Read the file
    with open(input_file, 'r') as f:
        for line in f:
            # Start of a new INSERT statement
            if line.strip().startswith("INSERT INTO round_stats"):
                if reading_statement and current_statement:
                    full_statement = ''.join(current_statement)
                    if ");".encode().decode() in full_statement:  # Complete statement check
                        valid_statements.append((full_statement, current_statement))
                current_statement = [line]
                reading_statement = True
            # Comment, blank line or other non-statement line
            elif line.strip().startswith("--") or not line.strip():
                if not reading_statement:
                    valid_statements.append((line, [line]))
                else:
                    current_statement.append(line)
            # Part of current statement
            elif reading_statement:
                current_statement.append(line)
                if ");".encode().decode() in line:  # End of statement
                    full_statement = ''.join(current_statement)
                    valid_statements.append((full_statement, current_statement))
                    reading_statement = False
                    current_statement = []
            # Other lines (like ALTER TABLE statements)
            else:
                valid_statements.append((line, [line]))
                
    # Finish last statement if any
    if reading_statement and current_statement:
        full_statement = ''.join(current_statement)
        valid_statements.append((full_statement, current_statement))

    # Write unique statements to the output file
    with open(output_file, 'w') as f:
        f.write("-- Seed data for round_stats table\n")
        f.write("-- Generated on 2025-03-04 (cleaned duplicate entries)\n\n")
        f.write("-- Disable triggers for faster bulk loading\n")
        f.write("ALTER TABLE round_stats DISABLE TRIGGER ALL;\n\n")
        
        for full_stmt, stmt_lines in valid_statements:
            # Skip incomplete INSERT statements
            if "INSERT INTO round_stats" in full_stmt and "VALUES" not in full_stmt:
                continue
                
            match = re.search(pattern, full_stmt)
            if match:
                fight_id = match.group(1)
                fighter_id = match.group(2)
                round_number = match.group(3)
                key = (fight_id, fighter_id, round_number)
                
                if key not in seen_keys:
                    seen_keys.add(key)
                    f.writelines(stmt_lines)
            else:
                # Write non-INSERT statements or comments
                if not full_stmt.strip().startswith("INSERT INTO round_stats"):
                    f.writelines(stmt_lines)
        
        f.write("\n-- Re-enable triggers\n")
        f.write("ALTER TABLE round_stats ENABLE TRIGGER ALL;\n")
    
    print(f"Processing complete. Found {len(seen_keys)} unique round stat entries.")
    print(f"Output written to {output_file}")
    
    # Optionally replace the original file
    os.rename(output_file, input_file)
    print(f"Replaced original file {input_file}")

if __name__ == "__main__":
    main()