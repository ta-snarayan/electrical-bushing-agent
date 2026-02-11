# Hitachi Energy Bushing Data Collector

A web scraping system to collect electrical bushing cross-reference information from the Hitachi Energy website.

## Overview

This tool scrapes bushing data from the Hitachi Energy Bushing Cross Reference website and saves the information to a CSV file. It extracts key information including original bushing manufacturer, catalog numbers, and ABB replacement style numbers.

## Features

- Scrapes bushing cross-reference data from Hitachi Energy website
- Parses pseudo-table HTML structures to extract structured data
- Saves data to CSV format with standardized column names
- Handles errors gracefully with detailed logging
- Supports incremental data collection (appends to existing CSV)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Navigate to the data_collection directory:
```powershell
cd data_collection
```

2. Install required dependencies:
```powershell
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the scraper with a bushing index number:

```powershell
python scraper.py <index>
```

### Examples

Scrape data for index 42131:
```powershell
python scraper.py 42131
```

Scrape data for index 42246:
```powershell
python scraper.py 42246
```

### Batch Scraping

For scraping multiple indices, use the batch scraper:

**Scrape a range of indices:**
```powershell
python batch_scraper.py --start 1 --end 10
```

**Scrape specific indices:**
```powershell
python batch_scraper.py --indices 42131,42246,50000
```

**Scrape from a file (one index per line):**
```powershell
python batch_scraper.py --file indices.txt
```

**Custom delay between requests:**
```powershell
python batch_scraper.py --start 1 --end 100 --delay 2.0
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
python batch_scraper.py --file indices.txt
```

### Output

The scraper will:
1. Fetch data from: `https://bushing.hitachienergy.com/Scripts/BushingCrossReferenceBU.asp?INDEX=<index>`
2. Extract the following fields:
   - Website Index
   - Original Bushing Manufacturer
   - Original Catalog Number
   - Replacement Bushing Manufacturer (defaults to "ABB")
   - ABB Style Number
3. Save/append the data to: `master_bushing_list_from_hitachi_website.csv`

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

```csv
Website Index,Original Bushing Information - Original Bushing Manufacturer,Original Bushing Information - Catalog Number,Replacement Information - Replacement Bushing Manufacturer,Replacement Information - ABB Style Number
42131,ABB,138W0800XA,ABB,138N0812BA
42246,<Manufacturer>,<Catalog>,ABB,<Style Number>
```

## Logging

The scraper provides detailed logging information:
- INFO: Successful operations and progress updates
- WARNING: Missing fields or data quality issues
- ERROR: Failed requests or parsing errors

Logs are displayed in the console during execution.

## Error Handling

The scraper handles various error conditions:
- **Network Errors**: Timeout, connection refused, DNS failures
- **Invalid Index**: Non-existent index numbers return appropriate warnings
- **Missing Data**: Fields that cannot be found are logged as warnings
- **Parsing Errors**: HTML structure changes are caught and logged

## Technical Details

### Dependencies

- **requests**: HTTP requests to fetch webpage content
- **beautifulsoup4**: HTML parsing and data extraction
- **lxml**: Fast XML and HTML parser
- **pandas**: CSV file operations and data management

### Architecture

The scraper consists of several key components:

#### Core Scraper (scraper.py)

**Functions:**
1. `scrape_bushing_data(index)`: Main orchestration function
2. `parse_bushing_info(soup, index)`: Extracts structured data from HTML
3. `extract_field_value(text, label)`: Generic field extraction
4. `extract_catalog_number(soup, text)`: Specialized catalog number extraction
5. `extract_abb_style_number(soup, text)`: Specialized ABB style number extraction
6. `save_to_csv(data, filepath)`: CSV file operations

#### Batch Scraper (batch_scraper.py)

**Functions:**
1. `scrape_range(start, end, delay)`: Scrape consecutive index range
2. `scrape_list(indices, delay)`: Scrape specific list of indices
3. `scrape_from_file(filepath, delay)`: Read indices from file and scrape

**Features:**
- Progress tracking with success/failure counts
- Configurable delay between requests
- Support for multiple input methods (range, list, file)
- Detailed logging and summary statistics

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

## Testing & Validation

The scraper has been thoroughly tested and validated against the Hitachi Energy website. See [test_results.md](test_results.md) for detailed test results.

### Test Summary

- ✅ **Test Range:** Indices 1-10
- ✅ **Success Rate:** 100% (10/10)
- ✅ **Accuracy:** Perfect match across all fields
- ✅ **Date Validated:** February 10, 2026

The scraper correctly handles:
- Multiple manufacturer formats (PCORE, LAPP, WEST, G.E., ABB)
- Various catalog number formats
- Different ABB style number patterns
- Empty or missing field values

### Quick Validation

To verify the scraper is working correctly:

1. Test with known index (42131):
```powershell
python scraper.py 42131
```

2. Check the output CSV file exists:
```powershell
ls master_bushing_list_from_hitachi_website.csv
```

3. Verify the data matches expected values:
   - Manufacturer: ABB
   - Catalog Number: 138W0800XA
   - ABB Style Number: 138N0812BA

### Batch Testing

To test multiple indices at once:
```powershell
for ($i=1; $i -le 10; $i++) { python scraper.py $i; Start-Sleep -Seconds 1 }
```

## Troubleshooting

### Common Issues

**Issue**: "Failed to fetch data"
- **Solution**: Check internet connection and verify the website is accessible

**Issue**: "Missing Original Bushing Manufacturer"
- **Solution**: This is normal for some indices where the manufacturer field is empty on the website; the field will be blank in the CSV

**Issue**: "No valid data found"
- **Solution**: The index may not exist, or the website structure may have changed

## Future Enhancements

Potential improvements for future versions:
- ~~Batch processing: Accept multiple indices in one run~~ ✅ **Added in v1.1** (see batch_scraper.py)
- Duplicate detection: Skip already-scraped indices
- Parallel scraping: Process multiple indices simultaneously
- GUI interface: User-friendly interface for non-technical users
- Auto-retry: Automatic retry on network failures
- Data validation: Enhanced validation rules for data quality
- Database support: Option to save to database instead of CSV

## Files in This Project

- **scraper.py** - Main single-index scraper
- **batch_scraper.py** - Batch processing scraper for multiple indices
- **requirements.txt** - Python package dependencies
- **README.md** - This documentation file
- **test_results.md** - Detailed test results and validation report
- **master_bushing_list_from_hitachi_website.csv** - Output CSV file (created after first run)

## Version History

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

Internal use only - Hitachi Energy Bushing Data Collection System

## Contact

For issues or questions, contact the development team.

---

**Last Updated**: February 10, 2026
