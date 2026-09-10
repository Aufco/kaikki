#!/usr/bin/env python3
"""
Simple dictionary sense viewer for SQLite database.
Displays: line number, sense number, part of speech, definition, and examples.
"""

import sqlite3
import sys
from pathlib import Path


def display_dictionary_senses(db_file, limit=None):
    """
    Display dictionary senses from SQLite database.
    
    Args:
        db_file: Path to the SQLite database file
        limit: Maximum number of records to display (None for all)
    """
    
    db_path = Path(db_file)
    if not db_path.exists():
        print(f"Error: Database file not found - {db_file}")
        sys.exit(1)
    
    print(f"Reading from database: {db_file}")
    print("-" * 80)
    print(f"{'Line':<6} {'Sense':<6} {'POS':<10} {'Definition':<40} {'Examples'}")
    print("-" * 80)
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if table exists and has data
        cursor.execute("SELECT COUNT(*) FROM dictionary_senses")
        total_count = cursor.fetchone()[0]
        
        if total_count == 0:
            print("No data found in database. Run extract_dictionary_senses.py first.")
            conn.close()
            return
        
        # Query data with optional limit
        query = '''
            SELECT line_number, sense_number, word, part_of_speech, definition, 
                   examples, example_count
            FROM dictionary_senses 
            ORDER BY line_number, sense_number
        '''
        
        if limit:
            query += f" LIMIT {limit}"
            cursor.execute(query)
        else:
            cursor.execute(query)
        
        displayed_count = 0
        for row in cursor:
            line_number, sense_number, word, pos, definition, examples, example_count = row
            
            # Truncate for display
            def_display = definition[:37] + '...' if len(definition) > 40 else definition
            
            # Print extracted information
            print(f"{line_number:<6} {sense_number:<6} {pos:<10} {def_display:<40} {example_count} example(s)")
            
            # Optionally print first example
            if examples and examples.strip():
                first_example = examples.split(' || ')[0] if ' || ' in examples else examples
                ex_display = first_example[:60] + '...' if len(first_example) > 60 else first_example
                print(f"{'':>63} → {ex_display}")
            
            displayed_count += 1
        
        print("-" * 80)
        print(f"Displayed {displayed_count} of {total_count} total senses")
        
        conn.close()
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def search_word(db_file, word):
    """
    Search for a specific word in the database.
    
    Args:
        db_file: Path to the SQLite database file
        word: Word to search for
    """
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT line_number, sense_number, word, part_of_speech, definition, 
                   examples, example_count
            FROM dictionary_senses 
            WHERE word = ? COLLATE NOCASE
            ORDER BY line_number, sense_number
        ''', (word,))
        
        results = cursor.fetchall()
        
        if not results:
            print(f"No entries found for word: {word}")
            conn.close()
            return
        
        print(f"Found {len(results)} sense(s) for word: {word}")
        print("-" * 80)
        print(f"{'Line':<6} {'Sense':<6} {'POS':<10} {'Definition':<40} {'Examples'}")
        print("-" * 80)
        
        for row in results:
            line_number, sense_number, word, pos, definition, examples, example_count = row
            
            def_display = definition[:37] + '...' if len(definition) > 40 else definition
            print(f"{line_number:<6} {sense_number:<6} {pos:<10} {def_display:<40} {example_count} example(s)")
            
            if examples and examples.strip():
                first_example = examples.split(' || ')[0] if ' || ' in examples else examples
                ex_display = first_example[:60] + '...' if len(first_example) > 60 else first_example
                print(f"{'':>63} → {ex_display}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)


def main():
    """Main function."""
    db_file = "/home/benau/kaikki/dictionary_senses.db"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "search" and len(sys.argv) > 2:
            search_word(db_file, sys.argv[2])
        elif sys.argv[1].isdigit():
            display_dictionary_senses(db_file, int(sys.argv[1]))
        else:
            print("Usage:")
            print("  python simple_extract.py              - Display all entries")
            print("  python simple_extract.py <number>     - Display first N entries")
            print("  python simple_extract.py search <word> - Search for specific word")
    else:
        # Default: show first 50 entries
        display_dictionary_senses(db_file, 50)


if __name__ == "__main__":
    main()
