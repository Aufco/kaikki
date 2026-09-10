#!/usr/bin/env python3
"""
Extract dictionary entry senses from Kaikki English dictionary JSONL file.
Extracts: senses, part of speech, definition glosses, and examples.
Assigns line numbers and sense numbers to each entry.
Stores data in SQLite database.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class DictionaryExtractor:
    def __init__(self, input_file: str, db_file: str = None):
        """
        Initialize the dictionary extractor.
        
        Args:
            input_file: Path to the JSONL file
            db_file: Path to the SQLite database file (optional)
        """
        self.input_file = Path(input_file)
        if db_file:
            self.db_file = Path(db_file)
        else:
            self.db_file = self.input_file.parent / "dictionary_senses.db"
        
        self.extracted_count = 0
        self.error_count = 0
        
        self.create_database()
    
    def create_database(self):
        """Create the SQLite database and table for storing dictionary senses."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dictionary_senses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                line_number INTEGER NOT NULL,
                sense_number INTEGER NOT NULL,
                word TEXT NOT NULL,
                part_of_speech TEXT,
                definition TEXT,
                sense_id TEXT,
                examples TEXT,
                example_count INTEGER DEFAULT 0,
                categories TEXT,
                wikidata TEXT,
                senseid TEXT,
                links TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_word ON dictionary_senses(word)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_line_number ON dictionary_senses(line_number)
        ''')
        
        conn.commit()
        conn.close()
        
    def extract_senses(self):
        """
        Extract senses from the JSONL file line by line and store in SQLite database.
        """
        print(f"Starting extraction from: {self.input_file}")
        print(f"Storing in database: {self.db_file}")
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM dictionary_senses")
        conn.commit()
        
        batch_data = []
        batch_size = 1000
        
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                for line_number, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        entry = json.loads(line)
                        
                        # Extract basic entry information
                        word = entry.get('word', '')
                        pos = entry.get('pos', '')
                        
                        # Extract senses
                        senses = entry.get('senses', [])
                        
                        for sense_number, sense in enumerate(senses, 1):
                            # Extract glosses (definitions)
                            glosses = sense.get('glosses', [])
                            gloss_text = ' | '.join(glosses) if glosses else ''
                            
                            # Extract examples
                            examples = sense.get('examples', [])
                            example_texts = []
                            
                            for example in examples:
                                if isinstance(example, dict):
                                    example_text = example.get('text', '')
                                    if example_text:
                                        example_texts.append(example_text)
                            
                            # Create extracted entry tuple for database
                            extracted_entry = (
                                line_number,
                                sense_number,
                                word,
                                pos,
                                gloss_text,
                                sense.get('id', ''),
                                ' || '.join(example_texts),
                                len(example_texts),
                                ', '.join([cat.get('name', '') for cat in sense.get('categories', [])]),
                                ', '.join(sense.get('wikidata', [])),
                                ', '.join(sense.get('senseid', [])),
                                ', '.join([str(link) for link in sense.get('links', [])])
                            )
                            
                            batch_data.append(extracted_entry)
                            self.extracted_count += 1
                            
                            # Insert batch when it reaches batch_size
                            if len(batch_data) >= batch_size:
                                cursor.executemany('''
                                    INSERT INTO dictionary_senses 
                                    (line_number, sense_number, word, part_of_speech, definition, 
                                     sense_id, examples, example_count, categories, wikidata, senseid, links)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', batch_data)
                                conn.commit()
                                batch_data = []
                            
                            # Progress indicator every 1000 lines
                            if line_number % 1000 == 0:
                                print(f"Processed {line_number} lines, extracted {self.extracted_count} senses...")
                    
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON on line {line_number}: {e}")
                        self.error_count += 1
                    except Exception as e:
                        print(f"Error processing line {line_number}: {e}")
                        self.error_count += 1
                
                # Insert remaining batch data
                if batch_data:
                    cursor.executemany('''
                        INSERT INTO dictionary_senses 
                        (line_number, sense_number, word, part_of_speech, definition, 
                         sense_id, examples, example_count, categories, wikidata, senseid, links)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', batch_data)
                    conn.commit()
        
        except FileNotFoundError:
            print(f"Error: File not found - {self.input_file}")
            conn.close()
            return
        except Exception as e:
            print(f"Error reading file: {e}")
            conn.close()
            return
        
        conn.close()
        
        print(f"\nExtraction complete!")
        print(f"Total senses extracted: {self.extracted_count}")
        print(f"Errors encountered: {self.error_count}")
        print(f"Data stored in: {self.db_file}")
    
    def get_sample_data(self, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get sample data from the database.
        
        Args:
            limit: Number of records to return
            
        Returns:
            List of dictionary records
        """
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM dictionary_senses 
            ORDER BY line_number, sense_number 
            LIMIT ?
        ''', (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def export_to_csv(self, csv_file: str = None) -> None:
        """
        Export database contents to CSV file.
        
        Args:
            csv_file: Path to output CSV file
        """
        if not csv_file:
            csv_file = self.db_file.with_suffix('.csv')
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM dictionary_senses')
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("No data in database to export.")
            conn.close()
            return
        
        print(f"Exporting {count} records to CSV...")
        
        try:
            import csv
            cursor.execute('''
                SELECT line_number, sense_number, word, part_of_speech, definition,
                       sense_id, examples, example_count, categories, wikidata, senseid, links
                FROM dictionary_senses 
                ORDER BY line_number, sense_number
            ''')
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'line_number', 'sense_number', 'word', 'part_of_speech', 'definition',
                    'sense_id', 'examples', 'example_count', 'categories', 'wikidata', 'senseid', 'links'
                ])
                writer.writerows(cursor.fetchall())
            
            print(f"Data exported to: {csv_file}")
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
        
        conn.close()


def main():
    """Main function to run the extraction."""
    
    # Configuration
    input_file = "/home/benau/kaikki/kaikki.org-dictionary-English.jsonl"
    db_file = "/home/benau/kaikki/dictionary_senses.db"
    
    # Create extractor instance
    extractor = DictionaryExtractor(input_file, db_file)
    
    # Extract senses and store in database
    extractor.extract_senses()
    
    # Show sample of extracted data from database
    sample_data = extractor.get_sample_data(3)
    if sample_data:
        print("\nSample of extracted data (first 3 entries):")
        for i, entry in enumerate(sample_data):
            print(f"\nEntry {i+1}:")
            print(f"  Line: {entry['line_number']}, Sense: {entry['sense_number']}")
            print(f"  Word: {entry['word']} ({entry['part_of_speech']})")
            definition = entry['definition']
            print(f"  Definition: {definition[:100]}..." if len(definition) > 100 else f"  Definition: {definition}")
            if entry['examples']:
                print(f"  Examples: {entry['example_count']} found")


if __name__ == "__main__":
    main()
