# Hitachi Energy Bushing Data Collector

A web scraping system to collect electrical bushing cross-reference information from the Hitachi Energy website.

> **Note**: This is part of a multi-website data collection system. Additional website collectors (PCORE, etc.) will be organized in parallel directories.

## Overview

This tool scrapes bushing data from the Hitachi Energy Bushing Cross Reference website and saves the information to a CSV file. It extracts key information including original bushing manufacturer, catalog numbers, and ABB replacement style numbers.

## Features

- ✅ Scrapes bushing cross-reference data from Hitachi Energy website
- ✅ Parses pseudo-table HTML structures to extract structured data
- ✅ Saves data to CSV format with standardized column names
- ✅ **Saves raw HTML responses for archival and debugging purposes**
- ✅ **Comprehensive error handling with CSV error logging**
- ✅ Handles large-scale automation (tested 1-100, supports up to 50,000+ indices)
- ✅ Supports incremental data collection (appends to existing CSV)
- ✅ Batch processing support for multiple indices
- ✅ Detailed logging and progress tracking

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Navigate to the hitachi_website_data_collection directory:
```powershell
cd data_collection/hitachi_website_data_collection
```

2. Install required dependencies:
```powershell
pip install -r ../requirements.txt
```

Or from the parent data_collection directory:
```powershell
pip install -r requirements.txt
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

**Scrape a range of indices:**
```powershell
python hitachi_website_data_batch_scraper.py --start 1 --end 10
```

**Scrape specific indices:**
```powershell
python hitachi_website_data_batch_scraper.py --indices 42131,42246,50000
```

**Scrape from a file (one index per line):**
```powershell
python hitachi_website_data_batch_scraper.py --file indices.txt
```

**Custom delay between requests:**
```powershell
python hitachi_website_data_batch_scraper.py --start 1 --end 100 --delay 0.5
```

**Large-scale automation (tested with 1-100, supports up to 50,000+):**
```powershell
python hitachi_website_data_batch_scraper.py --start 1 --end 50000 --delay 0.5
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

### Output

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
- Format: CSV with timestamp, index, error type, message, and details
- Columns:
  - `Timestamp`: When the error occurred
  - `Index`: Which bushing index failed
  - `Error_Type`: Category of error (HTTP_404, NO_DATA, TIMEOUT, etc.)
  - `Error_Message`: Brief error description
  - `Details`: Full error details including stack traces
- Purpose:
  - Track failures during large-scale automation
  - Identify problematic index numbers
  - Debug scraping issues
  - Analyze error patterns

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
Timestamp,Index,Error_Type,Error_Message,Details
2026-02-10 21:23:07,24,NO_DATA,All fields empty after parsing,Page loaded but no bushing data extracted
2026-02-10 21:23:38,47,NO_DATA,All fields empty after parsing,Page loaded but no bushing data extracted
```

## Logging

The scraper provides detailed logging information:
- **INFO**: Successful operations and progress updates
- **WARNING**: Missing fields or data quality issues
- **ERROR**: Failed requests or parsing errors (also logged to CSV)

Logs are displayed in the console during execution.

## Error Handling

The scraper handles various error conditions with comprehensive error logging:

### Error Types

1. **HTTP_404**: Page not found (invalid index)
2. **HTTP_403**: Access forbidden (rare, handled with browser headers)
3. **HTTP_ERROR**: Other HTTP errors
4. **TIMEOUT**: Request timeout after 30 seconds
5. **CONNECTION_ERROR**: Network connection issues
6. **REQUEST_ERROR**: General request exceptions
7. **EMPTY_RESPONSE**: Response too short or empty
8. **NO_DATA**: Page loaded but no bushing data found
9. **PARSE_FAILED**: Parser returned None
10. **UNKNOWN_ERROR**: Unexpected errors with full stack trace

### Error Recovery

- All errors are logged to `hitachi_website_scraping_error_log.csv`
- Scraper continues to next index after logging errors
- Failed indices can be retried later using the error log
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
1. `scrape_bushing_data(index)`: Main orchestration function with error handling
2. `log_error_to_csv(index, error_type, error_message, details)`: **NEW** - CSV error logging
3. `save_raw_html(html_content, index, directory)`: Save raw HTML to file
4. `parse_bushing_info(soup, index)`: Extracts structured data from HTML
5. `extract_field_value(text, label)`: Generic field extraction
6. `extract_catalog_number(soup, text)`: Specialized catalog number extraction
7. `extract_abb_style_number(soup, text)`: Specialized ABB style number extraction
8. `save_to_csv(data, filepath)`: CSV file operations

#### Batch Scraper (hitachi_website_data_batch_scraper.py)

**Functions:**
1. `scrape_range(start, end, delay)`: Scrape consecutive index range
2. `scrape_list(indices, delay)`: Scrape specific list of indices
3. `scrape_from_file(filepath, delay)`: Read indices from file and scrape

**Features:**
- Progress tracking with success/failure counts
- Configurable delay between requests
- Support for multiple input methods (range, list, file)
- Detailed logging and summary statistics
- Error log file notifications

### Data Extraction Strategy

The website uses a pseudo-table layout with:
- Label-value pairs separated by visual dividers
- Section-based organization (Original vs. Replacement info)
- Clickable links for certain fields

The parser:
1. Extracts all text content from the webpage
2. Identifies sections by text markers
3. Uses label-based searching within sections
4. Falls back to link extraction for style numbers
5. Validates extracted data before saving
6. Logs all failures to error CSV for analysis

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

**Issue**: "Failed to fetch data"
- **Solution**: Check internet connection and verify the website is accessible

**Issue**: "Missing Original Bushing Manufacturer"
- **Solution**: This is normal for some indices where the manufacturer field is empty on the website; the field will be blank in the CSV and logged in error log

**Issue**: "No valid data found"
- **Solution**: The index may not exist, or the page is empty; check `hitachi_website_scraping_error_log.csv` for details

**Issue**: Error log shows many TIMEOUT errors
- **Solution**: Increase the delay between requests or check network connectivity

**Issue**: HTTP_403 errors
- **Solution**: The browser headers should prevent this; if it persists, the website may be blocking automated requests

## Project Structure

```
hitachi_website_data_collection/
├── hitachi_website_data_scraper.py          # Core scraper module
├── hitachi_website_data_batch_scraper.py    # Batch processing script
├── hitachi_website_bushing_master_list.csv  # Output CSV (created after run)
├── hitachi_website_scraping_error_log.csv   # Error log (created if errors occur)
├── hitachi_website_data_raw/                # Raw HTML archive
│   └── cross_reference_data/
│       ├── Hitachi_website_bushing_1.html
│       ├── Hitachi_website_bushing_2.html
│       └── ...
├── README.md                                # This file
└── test_results.md                          # Detailed test results
```

## Future Enhancements

Potential improvements for future versions:
- ~~Batch processing: Accept multiple indices in one run~~ ✅ **Added in v1.1**
- ~~Error logging: CSV error log for large-scale automation~~ ✅ **Added in v2.0**
- Duplicate detection: Skip already-scraped indices
- Parallel scraping: Process multiple indices simultaneously
- GUI interface: User-friendly interface for non-technical users
- Auto-retry: Automatic retry on network failures with exponential backoff
- Progress persistence: Resume interrupted large-scale runs
- Database support: Option to save to database instead of CSV

## Version History

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

## License

Internal use only - Electrical Bushing Data Collection System

## Contact

For issues or questions, contact the development team.

---

**Last Updated**: February 10, 2026
**Version**: 2.0
