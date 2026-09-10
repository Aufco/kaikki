#!/usr/bin/env python3
"""
Utility functions for working with Kaikki dictionary SQLite database.
"""

import sqlite3
import sys
from collections import Counter
from pathlib import Path


def database_stats(db_file):
    """Show statistics from the SQLite database."""
    db_path = Path(db_file)
    if not db_path.exists():
        print(f"Error: Database file not found - {db_file}")
        return
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dictionary_senses'")
        if not cursor.fetchone():
            print("Error: dictionary_senses table not found in database")
            conn.close()
            return
        
        # Get total senses
        cursor.execute("SELECT COUNT(*) FROM dictionary_senses")
        total_senses = cursor.fetchone()[0]
        
        if total_senses == 0:
            print("No data found in database.")
            conn.close()
            return
        
        # Get unique words (entries)
        cursor.execute("SELECT COUNT(DISTINCT word) FROM dictionary_senses")
        unique_words = cursor.fetchone()[0]
        
        # Get part of speech distribution
        cursor.execute('''
            SELECT part_of_speech, COUNT(*) as count 
            FROM dictionary_senses 
            WHERE part_of_speech IS NOT NULL AND part_of_speech != ''
            GROUP BY part_of_speech 
            ORDER BY count DESC
        ''')
        pos_distribution = cursor.fetchall()
        
        # Get examples statistics
        cursor.execute("SELECT COUNT(*) FROM dictionary_senses WHERE example_count > 0")
        senses_with_examples = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(example_count) FROM dictionary_senses")
        avg_examples = cursor.fetchone()[0] or 0
        
        print(f"\nStatistics for {db_file}")
        print(f"{'='*50}")
        print(f"Total senses: {total_senses:,}")
        print(f"Unique words: {unique_words:,}")
        print(f"Average senses per word: {total_senses/unique_words:.2f}")
        print(f"Senses with examples: {senses_with_examples:,} ({senses_with_examples/total_senses*100:.1f}%)")
        print(f"Average examples per sense: {avg_examples:.2f}")
        
        print(f"\nPart of Speech Distribution:")
        for pos, count in pos_distribution:
            percentage = count/total_senses*100
            print(f"  {pos}: {count:,} ({percentage:.1f}%)")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")


def extract_word(db_file, target_word):
    """Extract all entries for a specific word from the database."""
    db_path = Path(db_file)
    if not db_path.exists():
        print(f"Error: Database file not found - {db_file}")
        return
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT line_number, sense_number, word, part_of_speech, definition,
                   examples, example_count, categories, wikidata, senseid
            FROM dictionary_senses 
            WHERE word = ? COLLATE NOCASE
            ORDER BY line_number, sense_number
        ''', (target_word,))
        
        results = cursor.fetchall()
        
        if not results:
            print(f"Word '{target_word}' not found in database.")
            conn.close()
            return
        
        # Group by line_number (original entry)
        entries = {}
        for row in results:
            line_num = row[0]
            if line_num not in entries:
                entries[line_num] = []
            entries[line_num].append(row)
        
        for line_num, senses in entries.items():
            first_sense = senses[0]
            word = first_sense[2]
            pos = first_sense[3]
            
            print(f"\n{'='*60}")
            print(f"Found '{word}' at line {line_num}")
            print(f"Part of speech: {pos}")
            print(f"Number of senses: {len(senses)}")
            
            for i, sense in enumerate(senses, 1):
                line_num, sense_num, word, pos, definition, examples, example_count, categories, wikidata, senseid = sense
                
                print(f"\nSense {i}:")
                if definition:
                    print(f"  Definition: {definition}")
                
                if examples and examples.strip():
                    example_list = examples.split(' || ')
                    print(f"  Examples ({len(example_list)}):")
                    for j, ex in enumerate(example_list[:3], 1):  # Show max 3 examples
                        print(f"    {j}. {ex}")
                
                if categories and categories.strip():
                    print(f"  Categories: {categories}")
                
                if wikidata and wikidata.strip():
                    print(f"  Wikidata: {wikidata}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")


def extract_line_range(db_file, start_line, end_line):
    """Extract entries from a specific line range from the database."""
    db_path = Path(db_file)
    if not db_path.exists():
        print(f"Error: Database file not found - {db_file}")
        return
    
    print(f"Extracting lines {start_line} to {end_line} from database...")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT line_number, word, part_of_speech, COUNT(*) as sense_count
            FROM dictionary_senses 
            WHERE line_number BETWEEN ? AND ?
            GROUP BY line_number, word, part_of_speech
            ORDER BY line_number
        ''', (start_line, end_line))
        
        entries = cursor.fetchall()
        
        if not entries:
            print(f"No entries found in line range {start_line}-{end_line}")
            conn.close()
            return
        
        for line_num, word, pos, sense_count in entries:
            print(f"\nLine {line_num}: {word} ({pos}) - {sense_count} sense(s)")
            
            # Get first sense definition as preview
            cursor.execute('''
                SELECT definition FROM dictionary_senses 
                WHERE line_number = ? AND word = ?
                ORDER BY sense_number LIMIT 1
            ''', (line_num, word))
            
            definition = cursor.fetchone()
            if definition and definition[0]:
                def_preview = definition[0][:80] + '...' if len(definition[0]) > 80 else definition[0]
                print(f"  First sense: {def_preview}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main function with command line interface."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python utils.py stats                    - Show database statistics")
        print("  python utils.py word <word>              - Extract specific word")
        print("  python utils.py lines <start> <end>      - Extract line range")
        sys.exit(1)
    
    db_file = "/home/benau/kaikki/dictionary_senses.db"
    command = sys.argv[1]
    
    if command == "stats":
        database_stats(db_file)
    
    elif command == "word" and len(sys.argv) >= 3:
        target_word = sys.argv[2]
        extract_word(db_file, target_word)
    
    elif command == "lines" and len(sys.argv) >= 4:
        try:
            start = int(sys.argv[2])
            end = int(sys.argv[3])
            extract_line_range(db_file, start, end)
        except ValueError:
            print("Error: Start and end must be integers")
    
    else:
        print("Invalid command or missing arguments")
        sys.exit(1)


if __name__ == "__main__":
    main()
