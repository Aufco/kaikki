# Kaikki Dictionary Sense Extractor

This project extracts dictionary entry senses from the Kaikki English dictionary JSONL file and stores them in an SQLite database for efficient querying.

## Overview

The extractor processes the `kaikki.org-dictionary-English.jsonl` file line by line and extracts:

- **Line number**: The line number where the entry was found in the file
- **Sense number**: The position of the sense within the entry (1-based)
- **Part of speech**: The grammatical category (noun, verb, etc.)
- **Definition**: The gloss text explaining the meaning
- **Examples**: Usage examples for each sense

All data is stored in an SQLite database (`dictionary_senses.db`) for fast searching and querying.

## Files

- `extract_dictionary_senses.py` - Full-featured extractor that stores data in SQLite database
- `simple_extract.py` - Database viewer for displaying and searching dictionary entries
- `utils.py` - Utility functions for database statistics and word lookups
- `dictionary_senses.db` - SQLite database file (created after running the extractor)
- `README.md` - This documentation file

## Installation

No special installation required. Uses Python 3 standard library only (including sqlite3).

## Usage

### Database Extractor

```bash
cd /home/benau/kaikki
python3 extract_dictionary_senses.py
```

This will:
- Process the entire JSONL file
- Create `dictionary_senses.db` SQLite database with all extracted data
- Show progress every 1000 lines
- Report total senses extracted and any errors

### Database Viewer

```bash
cd /home/benau/kaikki
python3 simple_extract.py              # View first 50 entries
python3 simple_extract.py 100          # View first 100 entries
python3 simple_extract.py search word  # Search for specific word
```

### Utility Functions

```bash
cd /home/benau/kaikki
python3 utils.py stats                 # Show database statistics
python3 utils.py word dictionary       # Extract all senses for "dictionary"
python3 utils.py lines 1 10            # Show entries from lines 1-10
```

## Database Schema

### Table: dictionary_senses

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing unique identifier |
| line_number | INTEGER | Line in the source file (1-based) |
| sense_number | INTEGER | Sense position within the entry (1-based) |
| word | TEXT | The dictionary headword |
| part_of_speech | TEXT | Grammatical category |
| definition | TEXT | The gloss/definition text |
| sense_id | TEXT | Internal sense identifier |
| examples | TEXT | All examples separated by \|\| |
| example_count | INTEGER | Number of examples |
| categories | TEXT | Associated categories |
| wikidata | TEXT | Wikidata identifiers |
| senseid | TEXT | Additional sense identifiers |
| links | TEXT | Related links |
| created_at | TIMESTAMP | When the record was created |

### Indexes
- `idx_word` - Fast searching by word
- `idx_line_number` - Fast line-based queries

### Example Output

```
Line  Sense  Word       POS   Definition                             Examples
1     1      dictionary noun  A reference work with a list of...    2 example(s)
1     2      dictionary noun  A synchronic dictionary of a...       2 example(s)
1     3      dictionary noun  Any work that has a list of...        0 example(s)
1     4      dictionary noun  An associative array, a data...       1 example(s)
```

## Data Structure

The JSONL file contains one JSON object per line with structure:

```json
{
  "word": "dictionary",
  "pos": "noun",
  "senses": [
    {
      "glosses": ["A reference work with a list of words..."],
      "examples": [
        {"text": "If you want to know the meaning..."}
      ],
      "id": "en-dictionary-en-noun-en:Q23622",
      "categories": [...],
      "wikidata": ["Q23622"]
    }
  ]
}
```

## Performance

- Processes approximately 1000 entries per second with batch inserts
- Memory efficient - reads line by line and uses batch processing
- Handles malformed JSON gracefully
- SQLite provides fast querying and indexing capabilities

## Error Handling

- Skips empty lines
- Reports JSON parsing errors with line numbers
- Continues processing after errors
- Summary of errors at completion
- Database transactions ensure data integrity

## Export Options

The extractor includes an option to export data to CSV format:

```python
# In extract_dictionary_senses.py
extractor = DictionaryExtractor(input_file, db_file)
extractor.extract_senses()
extractor.export_to_csv("exported_data.csv")  # Optional CSV export
```

## Customization

To modify the extractor:

1. Edit `extract_dictionary_senses.py`
2. Modify the database schema in the `create_database()` method
3. Adjust the extraction logic to include additional fields
4. Update the batch insert SQL in the `extract_senses()` method

## License

This extractor is provided as-is for processing the Kaikki dictionary data.
