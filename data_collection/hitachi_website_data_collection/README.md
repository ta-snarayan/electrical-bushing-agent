# Hitachi Energy Bushing Data Collector

A web scraping system to collect electrical bushing cross-reference information from the Hitachi Energy website.

> **Note**: This is part of a multi-website data collection system. Additional website collectors (PCORE, etc.) will be organized in parallel directories.

## Overview

This tool scrapes bushing data from the Hitachi Energy Bushing Cross Reference website and saves the information to a CSV file. It extracts key information including original bushing manufacturer, catalog numbers, and ABB replacement style numbers.

## Features

- ✅ Scrapes bushing cross-reference data from Hitachi Energy website
- ✅ Parses pseudo-table HTML structures to extract structured data
- ✅ Saves data to CSV format with standardized column names
- ✅ **Saves raw HTML only for valid data (storage optimization)**
- ✅ **Detects and skips invalid bushings** ("No bushing found by that style number")
- ✅ **Comprehensive error handling with timestamped CSV error logging**
- ✅ **Smart error log checking** - automatically skips known error indices
- ✅ Handles large-scale automation (tested 1-200, supports up to 50,000+ indices)
- ✅ **Multiple write modes: append (skip existing), overwrite (update existing), scratch (fresh start)**
- ✅ Intelligent duplicate detection - checks CSV, HTML files, and error log
- ✅ Batch processing support for multiple indices
- ✅ Detailed logging and progress tracking
- ✅ **Selective HTML cleanup** - deletes error index files during processing
- ✅ **Performance optimized** - no redundant network requests for known errors

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Anaconda environment (recommended)

### Setup

1. Navigate to the hitachi_website_data_collection directory:
```powershell
cd C:\Users\snarayan\Desktop\electrical-bushing-agent\data_collection\hitachi_website_data_collection
```

2. Install required dependencies (if not already installed):
```powershell
pip install -r ../requirements.txt
```

Or install individually:
```powershell
pip install requests==2.31.0 beautifulsoup4==4.12.3 lxml==5.1.0 pandas==2.2.0
```

## Usage

### Basic Usage

Run the scraper with a bushing index number:

```powershell
python hitachi_website_data_scraper.py <index>
```

### Examples

Scrape data for index 42131:
```powershell
python hitachi_website_data_scraper.py 42131
```

Scrape data for index 42246:
```powershell
python hitachi_website_data_scraper.py 42246
```

### Batch Scraping

For scraping multiple indices, use the batch scraper:

#### Write Modes

The batch scraper supports three write modes (default is `append`):

- **`--mode append`** (default): Skips indices that already exist in both the CSV file and raw HTML folder. Perfect for incremental data collection without re-scraping existing data.
- **`--mode overwrite`**: Overwrites existing data file-by-file. Use this to update specific indices while preserving other data.
- **`--mode scratch`**: Deletes ALL existing data (CSV, error log, raw HTML files) and starts fresh. Use with caution!

#### Basic Examples

**Scrape a range of indices (append mode - skips existing):**
```powershell
python hitachi_website_data_batch_scraper.py --start 1 --end 100 --delay 0.5
```

**Scrape specific indices:**
```powershell
python hitachi_website_data_batch_scraper.py --indices 42131,42246,50000 --delay 0.5
```

**Scrape from a file (one index per line):**
```powershell
python hitachi_website_data_batch_scraper.py --file indices.txt --delay 0.5
```

**Large-scale automation (tested with 1-200, supports up to 50,000+):**
```powershell
python hitachi_website_data_batch_scraper.py --start 1 --end 50000 --delay 0.5
```

#### Write Mode Examples

**Append mode - Skip existing data (default):**
```powershell
python hitachi_website_data_batch_scraper.py --start 1 --end 200 --delay 0.5 --mode append
```

**Overwrite mode - Update existing entries:**
```powershell
python hitachi_website_data_batch_scraper.py --start 1 --end 100 --delay 0.5 --mode overwrite
```

**Scratch mode - Fresh start (deletes all existing data):**
```powershell
python hitachi_website_data_batch_scraper.py --start 1 --end 100 --delay 0.5 --mode scratch
```

#### Creating an Index File

Create a text file `indices.txt` with one index per line:
```
42131
42246
50000
# This is a comment - lines starting with # are ignored
65432
```

Then run:
```powershell
python hitachi_website_data_batch_scraper.py --file indices.txt
```

## Catalog Data Collection (Phase 2)

After collecting cross-reference data, you can enrich the ABB style numbers with detailed catalog specifications.

### Overview

**Phase 1 (Cross-Reference)** collects Original → ABB replacement mappings  
**Phase 2 (Catalog)** enriches ABB style numbers with 53 detailed specification fields

This two-phase approach:
1. First identifies the 1,364 unique ABB bushings
2. Then collects comprehensive technical specifications for each

### Quick Start - Catalog Scraping

**Step 1: Initialize catalog master list**
```powershell
python hitachi_website_catalog_batch_scraper.py --initialize
```

This extracts 1,364 unique ABB style numbers from the cross-reference master list and creates `hitachi_website_bushing_catalog_master_list.csv`.

**Step 2: Scrape catalog data**
```powershell
# Scrape all 1,364 style numbers
python hitachi_website_catalog_batch_scraper.py --all --delay 0.5

# Or test with a single bushing first
python hitachi_website_catalog_scraper.py 138W0800XA

# Or scrape specific style numbers
python hitachi_website_catalog_batch_scraper.py --styles 138W0800XA,196W1620UW --delay 0.5
```

### Catalog Data Features

- **53 Specification Fields**: Complete technical data including:
  - Basic info (catalog #, delivery, price)
  - Insulator type and color
  - Electrical ratings (voltage, BIL, current, capacitance)
  - Physical dimensions (lengths, diameters, weight)
  - Terminal specifications (top and bottom)
  - Flange mounting details
  - Special features
- **Smart Initialization**: Automatically extracts unique ABB styles from Phase 1 results
- **Same Write Modes**: append/overwrite/scratch modes for flexible workflow
- **Independent Storage**: Separate CSV, error log, and HTML archive from Phase 1

### Documentation

For complete catalog scraping documentation, see:
- **[Catalog Data Collection README](CATALOG_DATA_COLLECTION_README.md)** - Full usage guide
- **[Catalog Scraper Architecture](CATALOG_SCRAPER_ARCHITECTURE.md)** - Technical details

### Output

Phase 1 (Cross-Reference) Output:

The scraper will:
1. Fetch data from: `https://bushing.hitachienergy.com/Scripts/BushingCrossReferenceBU.asp?INDEX=<index>`
2. **Save raw HTML response** to: `hitachi_website_data_raw/cross_reference_data/Hitachi_website_bushing_<index>.html`
3. Extract the following fields:
   - Website Index
   - Original Bushing Manufacturer
   - Original Catalog Number
   - Replacement Bushing Manufacturer (defaults to "ABB")
   - ABB Style Number
4. Save/append the data to: `hitachi_website_bushing_master_list.csv`
5. **Log any errors to**: `hitachi_website_scraping_error_log.csv`

### Output Files

**CSV Data File:**
- Location: `hitachi_website_bushing_master_list.csv`
- Format: Comma-separated values with headers
- Purpose: Structured data extraction for analysis

**Raw HTML Files:**
- Location: `hitachi_website_data_raw/cross_reference_data/Hitachi_website_bushing_<index>.html`
- Format: Original HTML from website
- Purpose: 
  - Archive original source data
  - Enable re-parsing if scraper logic needs updates
  - Debug data extraction issues
  - Verify scraped data accuracy
  - Maintain data provenance

**Error Log File:**
- Location: `hitachi_website_scraping_error_log.csv`
- Format: CSV with timestamp, index, and detailed error message
- Columns:
  - `Timestamp`: When the error occurred (YYYY-MM-DD HH:MM:SS)
  - `Index`: Which bushing index failed
  - `Error_Message`: Detailed error description
- Purpose:
  - Track failures during large-scale automation
  - Skip known error indices in future runs (performance optimization)
  - Identify problematic index numbers
  - Debug scraping issues with descriptive messages
  - Analyze error patterns
- Behavior:
  - **Appends data** - never cleared between runs (preserves history)
  - **Automatic skip** - indices in error log are skipped during processing
  - **HTML cleanup** - deletes associated HTML files when encountered
  - **No duplicates** - prevents adding same index twice

### Output Format

The CSV file contains the following columns:

| Column | Description | Source |
|--------|-------------|--------|
| Website Index | The index number from the URL | Input parameter |
| Original Bushing Information - Original Bushing Manufacturer | Manufacturer of the original bushing | Scraped from website |
| Original Bushing Information - Catalog Number | Original catalog number | Scraped from website |
| Replacement Information - Replacement Bushing Manufacturer | Replacement manufacturer | Default: "ABB" |
| Replacement Information - ABB Style Number | ABB replacement style number | Scraped from website |

### Example Output

**hitachi_website_bushing_master_list.csv:**
```csv
Website Index,Original Bushing Information - Original Bushing Manufacturer,Original Bushing Information - Catalog Number,Replacement Information - Replacement Bushing Manufacturer,Replacement Information - ABB Style Number
1,PCORE,B-89311-70,ABB,034W1200UH
2,LAPP,B-88843-8-70,ABB,034Z3900AB
3,WEST,225,ABB,196X1216UP
```

**hitachi_website_scraping_error_log.csv:**
```csv
Timestamp,Index,Error_Message
2026-02-11 21:51:17,24,All fields empty - no bushing data extracted
2026-02-11 21:51:17,47,No bushing found by that style number
2026-02-11 21:51:17,99999,No bushing found by that style number
```

## Logging

The scraper provides detailed logging information:
- **INFO**: Successful operations and progress updates
- **WARNING**: Missing fields or data quality issues
- **ERROR**: Failed requests or parsing errors (also logged to CSV)

Logs are displayed in the console during execution.

## Error Handling

The scraper handles various error conditions with comprehensive error logging:

### Error Messages

Descriptive error messages are logged for easy debugging:

1. **"No bushing found by that style number"**: Website explicitly states bushing doesn't exist
2. **"All fields empty - no bushing data extracted"**: Page loaded but no valid data found
3. **"Page not found (HTTP 404)"**: Invalid index number
4. **"Access forbidden (HTTP 403)"**: Server blocked request (rare with browser headers)
5. **"Empty or too short response from server"**: Server returned insufficient data
6. **"Request timeout after 30 seconds"**: Network timeout
7. **"Network connection error: [details]"**: Connection issues with details
8. **"HTTP error [code]: [details]"**: Other HTTP errors with specifics
9. **"HTML parser returned None - could not parse page"**: Parsing failure
10. **"Request exception: [details]"**: Request library errors
11. **"Unexpected error: [details]"**: Unhandled exceptions with details

### Error Recovery & Optimization

- All errors are logged to `hitachi_website_scraping_error_log.csv` with timestamp and index
- **Error log is preserved** - never cleared between runs (except scratch mode)
- **Automatic skip** - indices in error log are automatically skipped in future runs
- **HTML cleanup during processing** - when error index is encountered, any existing HTML file is deleted
- **No redundant scraping** - known error indices are never re-scraped
- **Performance benefit** - skipping errors saves time and network bandwidth
- Scraper continues to next index after logging errors
- Successful indices are saved even when others fail

## Technical Details

### Dependencies

- **requests 2.31.0**: HTTP requests to fetch webpage content
- **beautifulsoup4 4.12.3**: HTML parsing and data extraction
- **lxml 5.1.0**: Fast XML and HTML parser
- **pandas 2.2.0**: CSV file operations and data management

### Architecture

The scraper consists of several key components:

#### Core Scraper (hitachi_website_data_scraper.py)

**Functions:**
1. `scrape_bushing_data(index)`: Main orchestration with error handling and validation
   - Detects "No bushing found" messages
   - Only saves HTML for valid/partial data
   - Deletes HTML files for error cases
2. `log_error_to_csv(index, error_message)`: Logs errors with timestamp and descriptive message
3. `save_raw_html(html_content, index, directory)`: Save raw HTML (only for valid data)
4. `delete_raw_html(index, directory)`: Delete HTML file for error indices
5. `get_error_log_indices()`: Load all error log indices into memory for fast lookup
6. `parse_bushing_info(soup, index)`: Extracts structured data from HTML
7. `extract_field_value(text, label)`: Generic field extraction
8. `extract_catalog_number(soup, text)`: Specialized catalog number extraction
9. `extract_abb_style_number(soup, text)`: Specialized ABB style number extraction
10. `save_to_csv(data, filepath, mode)`: CSV file operations with mode support

#### Batch Scraper (hitachi_website_data_batch_scraper.py)

**Functions:**
1. `check_index_exists(index)`: Check if index exists in CSV or HTML (not error log)
2. `scrape_range(start, end, delay, mode)`: Scrape consecutive index range
   - Loads error log indices at startup
   - Skips error indices and deletes their HTML files
   - Checks append/overwrite mode for existing data
3. `scrape_list(indices, delay, mode)`: Scrape specific list of indices
   - Same error log checking as scrape_range
4. `scrape_from_file(filepath, delay, mode)`: Read indices from file and scrape
5. `clean_scratch_mode()`: Delete all data for fresh start

**Features:**
- **Error log awareness** - automatically skips indices in error log
- **Selective HTML cleanup** - deletes error index HTML files during processing
- Progress tracking with success/failure/skipped counts
- Configurable delay between requests
- Support for multiple input methods (range, list, file)
- Three write modes: append (default), overwrite, scratch
- Detailed logging and summary statistics
- Error log file notifications

### Data Extraction Strategy

The website uses a pseudo-table layout with:
- Label-value pairs separated by visual dividers
- Section-based organization (Original vs. Replacement info)
- Clickable links for certain fields

The parser:
1. Checks for "No bushing found by that style number" message (logs error if found)
2. Extracts all text content from the webpage
3. Identifies sections by text markers
4. Uses label-based searching within sections
5. Falls back to link extraction for style numbers
6. Validates extracted data (requires at least one field with data)
7. **Saves HTML only if valid/partial data exists**
8. **Deletes HTML file if no valid data or error detected**
9. Logs all failures to error CSV with descriptive messages
10. **Error log indices are skipped in future runs** (performance optimization)

## Testing & Validation

The scraper has been thoroughly tested and validated against the Hitachi Energy website.

### Test Summary

- ✅ **Test Range:** Indices 1-100
- ✅ **Success Rate:** 89% (89/100 valid, 11 empty pages)
- ✅ **Accuracy:** Perfect match across all fields
- ✅ **Date Validated:** February 10, 2026
- ✅ **Error Logging:** All 11 failures properly logged with NO_DATA type

The scraper correctly handles:
- Multiple manufacturer formats (PCORE, LAPP, WEST, G.E., ABB)
- Various catalog number formats
- Different ABB style number patterns
- Empty or missing field values
- Non-existent index numbers
- Large-scale automation (100 indices tested, supports 50,000+)

### Failed Indices (1-100 range)

The following indices had NO_DATA (empty pages):
24, 47, 63, 67, 71, 73, 74, 76, 81, 93, 95

All failures were properly logged to `hitachi_website_scraping_error_log.csv`.

### Quick Validation

To verify the scraper is working correctly:

1. Test with known index (1):
```powershell
python hitachi_website_data_scraper.py 1
```

2. Check the output CSV file exists:
```powershell
ls hitachi_website_bushing_master_list.csv
```

3. Verify the data matches expected values:
   - Manufacturer: PCORE
   - Catalog Number: B-89311-70
   - ABB Style Number: 034W1200UH

### Batch Testing

To test with indices 1-10:
```powershell
python hitachi_website_data_batch_scraper.py --start 1 --end 10 --delay 0.5
```

## Troubleshooting

### Common Issues

**Issue**: "Can't open file" or "No such file or directory"
- **Solution**: Always navigate to the correct directory first:
  ```powershell
  cd C:\Users\snarayan\Desktop\electrical-bushing-agent\data_collection\hitachi_website_data_collection
  ```

**Issue**: "ModuleNotFoundError: No module named 'pandas'"
- **Solution**: 
  1. Make sure you're using the Anaconda base environment (you should see `(base)` in your prompt)
  2. Install dependencies: `pip install pandas requests beautifulsoup4 lxml`

**Issue**: "Failed to fetch data"
- **Solution**: Check internet connection and verify the website is accessible

**Issue**: "Missing Original Bushing Manufacturer"
- **Solution**: This is normal for some indices where the manufacturer field is empty on the website; the field will be blank in the CSV and logged in error log

**Issue**: "No valid data found"
- **Solution**: The index may not exist, or the page is empty; check `hitachi_website_scraping_error_log.csv` for details

**Issue**: Error log shows many TIMEOUT errors
- **Solution**: Increase the delay between requests: `--delay 1.0` or check network connectivity

**Issue**: HTTP_403 errors
- **Solution**: The browser headers should prevent this; if it persists, the website may be blocking automated requests

## Project Structure

```
hitachi_website_data_collection/
├── Phase 1: Cross-Reference Scraping
│   ├── hitachi_website_data_scraper.py          # Core scraper module
│   ├── hitachi_website_data_batch_scraper.py    # Batch processing script
│   ├── hitachi_website_bushing_master_list.csv  # Output: 7,100+ cross-references
│   ├── hitachi_website_scraping_error_log.csv   # Phase 1 error log
│   └── hitachi_website_data_raw/cross_reference_data/  # Phase 1 HTML archives
│
├── Phase 2: Catalog Data Scraping (NEW)
│   ├── hitachi_website_catalog_scraper.py       # Catalog scraper module
│   ├── hitachi_website_catalog_batch_scraper.py # Batch catalog processor
│   ├── hitachi_website_bushing_catalog_master_list.csv  # Output: 1,364 detailed specs
│   ├── hitachi_website_catalog_scraping_error_log.csv   # Phase 2 error log
│   └── hitachi_website_data_raw/catalog_data/   # Phase 2 HTML archives
│
└── Documentation
    ├── README.md                                # This file (main overview)
    ├── CATALOG_DATA_COLLECTION_README.md        # Phase 2 complete guide
    ├── CATALOG_SCRAPER_ARCHITECTURE.md          # Technical architecture (Phase 2)
    ├── PERFORMANCE_IMPROVEMENTS.md              # Phase 1 optimizations
    ├── QUICK_START.md                           # Quick reference guide
    └── VERIFICATION_REPORT.md                   # Test results and validation
```

## Future Enhancements

Potential improvements for future versions:
- ~~Batch processing: Accept multiple indices in one run~~ ✅ **Added in v1.1**
- ~~Error logging: CSV error log for large-scale automation~~ ✅ **Added in v2.0**
- ~~Catalog data collection: Detailed specifications for ABB bushings~~ ✅ **Added in v4.0**
- Duplicate detection: Enhanced skip logic for efficiency
- Parallel scraping: Process multiple indices simultaneously
- GUI interface: User-friendly interface for non-technical users
- Auto-retry: Automatic retry on network failures with exponential backoff
- Progress persistence: Resume interrupted large-scale runs
- Database support: Option to save to database instead of CSV

## Version History
4.0** (February 13, 2026) - **Catalog Data Collection Added**
- **NEW: Phase 2 catalog scraping system**
- Added `hitachi_website_catalog_scraper.py` for detailed specifications
- Added `hitachi_website_catalog_batch_scraper.py` for batch catalog processing
- Extracts 1,364 unique ABB style numbers from cross-reference data
- Collects 53 specification fields per bushing
- Complete catalog documentation (README + Architecture guide)
- Independent storage: separate CSV, error log, HTML archive
- Same robust features: append/overwrite/scratch modes, error handling
- Two-phase data collection pipeline: cross-reference → catalog enrichment

**v
**v3.2** (February 11, 2026)
- **Error log format updated**: Timestamp, Index, Error_Message (more descriptive)
- **Removed automatic cleanup on startup** - more controlled behavior
- **Selective HTML deletion during processing** - only when error index is encountered
- **Error log preservation** - never cleared between runs (append only)
- **Smart skip logic** - automatically skips error log indices
- **Better error messages** - detailed descriptions for debugging

**v3.1** (February 11, 2026)
- **Storage optimization**: Only saves HTML for valid/partial data
- **Invalid bushing detection**: Detects "No bushing found" messages
- **Automatic HTML cleanup**: Deletes error index HTML files
- **Performance improvements**: 3-5x faster in append mode
- **Error log checking**: Skips known error indices (no redundant scraping)
- **Space savings**: ~500MB freed by removing unnecessary HTML files

**v2.0** (February 10, 2026)
- **Major reorganization for multi-website support**
- Renamed files with `hitachi_website_data_` prefix
- Updated directory structure for parallel website collectors
- All output files now use consistent naming convention
- Enhanced documentation for organized structure

**v1.3** (February 10, 2026)
- Added comprehensive error handling and CSV error logging
- Support for large-scale automation (1-50,000+ indices)
- 10+ error types with detailed categorization
- Stack trace logging for debugging
- Tested with indices 1-100 (89% success rate)

**v1.2** (February 10, 2026)
- Added raw HTML storage for data archival and debugging
- Automatically saves HTML responses to structured directory
- Enhanced documentation with raw data file information

**v1.1** (February 10, 2026)
- Added batch_scraper.py for processing multiple indices
- Comprehensive testing with indices 1-10 (100% success rate)
- Updated documentation with test results
- Enhanced error handling for empty fields

**v1.0** (February 10, 2026)
- Initial release
- Single-index scraping
- CSV output with proper column formatting
- Browser-like headers for anti-bot bypass
- Comprehensive logging
3, 2026  
**Version**: 4.0  
**Latest Features**: Catalog data collection (Phase 2), 53 specification fields, two-phase pipeline
Internal use only - Electrical Bushing Data Collection System

## Contact

For issues or questions, contact the development team.

---

**Last Updated**: February 11, 2026
**Version**: 3.2
**Latest Features**: Error log optimization, selective HTML cleanup, performance improvements
