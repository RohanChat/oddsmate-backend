#!/usr/bin/env python3
# filepath: /Users/rohan/Desktop/oddsmate-backend/initdb/fix_precomp.py

import re

def fix_apostrophes_in_sql_file(file_path):
    """Fix SQL files by escaping apostrophes in string values using regex"""
    print(f"Processing {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # This regex finds string literals and captures any apostrophes in them
    # (?<=') means "preceded by a single quote" (string start)
    # [^']*? matches everything up to the apostrophe in a non-greedy way
    # (?=') means "followed by a single quote" (string end)
    pattern = r"'(.*?)'(?!\s*\))"
    
    def replace_apostrophes(match):
        # Replace each apostrophe with two apostrophes inside the string
        text = match.group(1)
        return "'" + text.replace("'", "''") + "'"
    
    fixed_content = re.sub(pattern, replace_apostrophes, content)
    
    # Second pass for specific fighter names with apostrophes
    fighters_with_apostrophes = [
        "O'Malley", "O'Neill", "D'Amato", "Lone'er", "Don'tale", "D'Angelo",
        "Jamahal Hill's", "Macfarlane", "Ivanov's", "McGregor", "McCann",
        "McKinney", "McLellan", "Muhammad's", "N'Guessan", "N'Kosi"
    ]
    
    for fighter in fighters_with_apostrophes:
        fixed_fighter = fighter.replace("'", "''")
        # Only replace inside VALUES clause patterns to avoid affecting SQL syntax
        fixed_content = re.sub(
            f"('.*){fighter}(.*')", 
            f"\\1{fixed_fighter}\\2", 
            fixed_content
        )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    # Fix the seed files
    files_to_fix = [
        './initdb/10_fight_scores_seed.sql',
        './initdb/11_round_scores_seed.sql'
    ]
    
    for file_path in files_to_fix:
        fix_apostrophes_in_sql_file(file_path)