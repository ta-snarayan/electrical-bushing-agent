# Hitachi Energy Bushing Catalog Data Collector

A comprehensive web scraping system to collect detailed electrical bushing specifications from the Hitachi Energy website. This is **Phase 2** of the Hitachi data collection system.

## Overview

### Two-Phase Data Collection System

**Phase 1: Cross-Reference Data Collection** ([hitachi_website_data_scraper.py](hitachi_website_data_scraper.py))
- Collects bushing cross-reference mappings (original → ABB replacement)
- Extracts ABB style numbers from cross-reference database
- Creates master list with 7,100+ cross-reference records

**Phase 2: Catalog Data Collection** (This Module)
- Takes unique ABB style numbers from Phase 1
- Scrapes complete technical specifications for each bushing
- Enriches data with 53 detailed specification fields

This catalog scraper extracts comprehensive bushing specifications including electrical ratings, physical dimensions, terminal configurations, and mounting details from the Hitachi Energy Bushing Product Information Database.

## Features

- ✅ **Automated Initialization**: Extracts 1,364 unique ABB style numbers from cross-reference master list
- ✅ **Comprehensive Data Extraction**: Captures all 53 specification fields
- ✅ **Smart Duplicate Detection**: Checks CSV, HTML files, and error log to avoid redundant scraping
- ✅ **Three Write Modes**: append (skip existing), overwrite (update existing), scratch (fresh start)
- ✅ **Raw HTML Archival**: Saves HTML only for valid data (storage optimization)
- ✅ **Robust Error Handling**: Comprehensive error logging with timestamps
- ✅ **Batch Processing**: Process single, multiple, or all style numbers
- ✅ **Performance Optimized**: Skip existing, error log caching, configurable delays
- ✅ **Respectful Scraping**: Configurable delays between requests
- ✅ **Detailed Logging**: Progress tracking and success/failure reporting

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

2. Install required dependencies (same as Phase 1):
```powershell
pip install -r ../requirements.txt
```

Or install individually:
```powershell
pip install requests==2.31.0 beautifulsoup4==4.12.3 lxml==5.1.0 pandas==2.2.0
```

## Usage

### Step 1: Initialize Catalog Master List

Before scraping catalog data, you must initialize the master list with unique ABB style numbers:

```powershell
python hitachi_website_catalog_batch_scraper.py --initialize
```

This command:
- Reads `hitachi_website_bushing_master_list.csv` (from Phase 1)
- Extracts 1,364 unique ABB style numbers
- Creates `hitachi_website_bushing_catalog_master_list.csv` with all column headers
- Populates first column with style numbers, leaving other fields empty

**Output:**
```
📋 Extracting unique ABB style numbers from cross-reference master list...
✓ Found 1364 unique ABB style numbers
✓ Created catalog master list: hitachi_website_bushing_catalog_master_list.csv
  Total style numbers: 1364

Next step: Run batch scraper to populate catalog data
  python hitachi_website_catalog_batch_scraper.py --all --delay 0.5
```

### Step 2: Scrape Catalog Data

#### Single Bushing

Scrape catalog data for a single bushing style:

```powershell
python hitachi_website_catalog_scraper.py 138W0800XA
```

**Output:**
```
✓ Successfully scraped and saved catalog data for style 138W0800XA
  Catalog Number: W11B450BB
  Voltage Class: 138 kV
  Current Rating: 800 Amps
```

#### Multiple Bushings

**Scrape all style numbers (recommended):**
```powershell
python hitachi_website_catalog_batch_scraper.py --all --delay 0.5
```

**Scrape specific style numbers:**
```powershell
python hitachi_website_catalog_batch_scraper.py --styles 138W0800XA,196W1620UW,115W0800AA --delay 0.5
```

**Scrape from a file (one style per line):**
```powershell
python hitachi_website_catalog_batch_scraper.py --file priority_styles.txt --delay 0.5
```

Example `priority_styles.txt`:
```
138W0800XA
196W1620UW
115W0800AA
# Comments are ignored
550W2000UN
```

### Write Modes

The batch scraper supports three write modes (default is `append`):

| Mode | Flag | Behavior | Use Case |
|------|------|----------|----------|
| **Append** | `--mode append` | Skips style numbers in CSV (with data), HTML, or error log | Default, incremental data collection |
| **Overwrite** | `--mode overwrite` | Overwrites existing data, skips error log entries | Update specific entries |
| **Scratch** | `--mode scratch` | Deletes ALL catalog data and starts fresh | Complete reset ⚠️ |

**Examples:**

```powershell
# Append mode (default) - skip existing data
python hitachi_website_catalog_batch_scraper.py --all --delay 0.5

# Overwrite mode - update existing entries
python hitachi_website_catalog_batch_scraper.py --styles 138W0800XA,196W1620UW --mode overwrite

# Scratch mode - fresh start (deletes everything!)
python hitachi_website_catalog_batch_scraper.py --all --delay 0.5 --mode scratch
```

### Advanced Options

**Adjust delay between requests:**
```powershell
# Faster (be respectful to server)
python hitachi_website_catalog_batch_scraper.py --all --delay 0.3

# Slower (more conservative)
python hitachi_website_catalog_batch_scraper.py --all --delay 2.0
```

**Force reinitialize master list:**
```powershell
python hitachi_website_catalog_batch_scraper.py --initialize --force
```

## Data Structure

### Output Files

| File | Description |
|------|-------------|
| `hitachi_website_bushing_catalog_master_list.csv` | Master catalog with 53 specification fields for each bushing |
| `hitachi_website_catalog_scraping_error_log.csv` | Error log with timestamps and failure reasons |
| `hitachi_website_data_raw/catalog_data/*.html` | Raw HTML files (only saved for valid data) |

### CSV Columns (53 fields)

#### Basic Information (10 fields)
- Style Number
- Alternate Style Number (usually other color)
- Catalog Number
- Delivery Ex-Works
- Delivery Last Update
- List Price US$
- Insulator Type
- Color
- Outline Drawing
- Download Drawing

#### Specifications (8 fields)
- Apparatus
- Standard
- Bushing Type
- Oil Indication
- Application
- Mounting Position
- Connection Type
- Current Version

#### Electrical Ratings (11 fields)
- Voltage Class
- kV BIL
- Max kV L-G
- Cantilever Design Test Rating Upper Value
- Cantilever Design Test Rating Lower Value
- Approximate Capacitance C1
- Approximate Capacitance C2
- Current Rating Draw Lead
- Bottom Connected
- Oil Circuit Breaker

#### Physical Dimensions (13 fields)
- Lower End Length (L)
- C.T. Pocket Transformer
- C.T. Pocket Oil Circuit Breaker
- Exposable Length Transformer (EL)
- Exposable Length Oil Circuit Breaker (EL)
- Max. Dia. From 1" below Flange to Lower End of Bushing (D)
- Upper End Length (B)
- Minimum Creep
- Arcing Distance
- Lowest High Voltage (LHV)
- Cable Height/Pin Height for AB Bushings (CH)
- Maximum Altitude
- Approximate Weight

#### Terminal Information (7 fields)
- Top End Terminal - Thread Dia and Class or number of Pads and Holes Per Pad
- Top End Terminal - Length and Type or Dia, and Type of Holes
- Top End Terminal - Thread Plating
- Top End Terminal - Top Terminal Comments
- Bottom End Terminal - Terminal Type
- Bottom End Terminal - Min Outside Diameter
- Bottom End Terminal - Bottom Terminal Comments

#### Flange Mounting (8 fields)
- Max Inside Diameter (P)
- Min Outside Diameter (Q)
- Number of Holes
- Hole/Slot Size
- Bolt Circle Diameter
- Epoxy Coated Shield and Terminal Kit
- Flange Mounting Comments
- Special Features

## Performance Features

### Duplicate Detection

The scraper checks three sources before scraping:

1. **CSV File**: Checks if style number exists with populated data
2. **HTML Files**: Checks if raw HTML already saved
3. **Error Log**: Checks if style number previously failed

In **append mode**, any of these triggers a skip. In **overwrite mode**, only error log triggers a skip.

### Error Log Caching

Error log is loaded once at batch start and cached in memory, avoiding repeated disk reads for each style number.

### Storage Optimization

- **HTML saved only for valid data**: Reduces disk usage significantly
- **Automatic cleanup**: Deletes HTML files for error log entries
- **Empty field handling**: Empty values stored as empty strings (not "N/A")

### Batch Processing Tips

**For small tests (10-50 style numbers):**
```powershell
python hitachi_website_catalog_batch_scraper.py --styles 138W0800XA,196W1620UW,115W0800AA --delay 0.5
```

**For medium batches (50-500 style numbers):**
```powershell
python hitachi_website_catalog_batch_scraper.py --file batch_styles.txt --delay 0.5
```

**For full dataset (1,364 style numbers):**
```powershell
# First run
python hitachi_website_catalog_batch_scraper.py --all --delay 0.5

# Resume after interruption (append mode skips existing)
python hitachi_website_catalog_batch_scraper.py --all --delay 0.5
```

**Estimated Time:**
- 1,364 style numbers × 0.5s delay = ~11-12 minutes
- Add ~1-2 seconds per request for network/processing = ~45-60 minutes total

## Error Handling

### Error Log Format

`hitachi_website_catalog_scraping_error_log.csv`:
```csv
Timestamp,Style_Number,Error_Message
2026-02-13 14:30:15,INVALID123,No bushing found by that style number
2026-02-13 14:31:22,TEST456,Request timeout after 30 seconds
```

### Common Error Types

| Error | Description | Action |
|-------|-------------|--------|
| `No bushing found by that style number` | Style number doesn't exist in database | Normal - not all styles have catalog pages |
| `Request timeout after 30 seconds` | Network timeout | Retry with longer delay |
| `Page not found (HTTP 404)` | URL not accessible | Check if style number is valid |
| `Empty or too short response` | Server returned minimal content | Temporary server issue, retry later |
| `Network connection error` | Internet connectivity issue | Check network connection |

### Handling Failed Scrapes

1. **Review error log**: Check `hitachi_website_catalog_scraping_error_log.csv`
2. **Retry failed styles**: Extract failed styles and retry:
   ```powershell
   # Extract failed styles from error log
   # Then retry
   python hitachi_website_catalog_batch_scraper.py --file failed_styles.txt --delay 1.0 --mode overwrite
   ```

## Troubleshooting

### Issue: "Catalog master list not found"

**Cause**: Trying to scrape before initialization

**Fix**: Run initialization first:
```powershell
python hitachi_website_catalog_batch_scraper.py --initialize
```

### Issue: "No ABB style numbers found"

**Cause**: Phase 1 cross-reference master list missing or empty

**Fix**: Ensure `hitachi_website_bushing_master_list.csv` exists and has data:
```powershell
# Check if file exists
dir hitachi_website_bushing_master_list.csv
```

### Issue: All bushings being skipped

**Cause**: Data already exists and running in append mode

**Fix**: Either:
- Use overwrite mode to update: `--mode overwrite`
- Use scratch mode to start fresh: `--mode scratch`
- This is expected behavior if data is complete

### Issue: "Can't open file" or "No such file or directory"

**Cause**: Running from wrong directory

**Fix**: Always navigate to correct directory first:
```powershell
cd C:\Users\snarayan\Desktop\electrical-bushing-agent\data_collection\hitachi_website_data_collection
```

### Issue: Many failures with "Request timeout"

**Cause**: Network issues or server rate limiting

**Fix**: Increase delay and retry:
```powershell
python hitachi_website_catalog_batch_scraper.py --all --delay 2.0
```

## Best Practices

1. **Always initialize first**: Run `--initialize` before batch scraping
2. **Start with small batch**: Test with a few style numbers before running `--all`
3. **Use append mode by default**: Safely resumes interrupted scraping
4. **Be respectful**: Use delays of 0.5-1.0 seconds minimum
5. **Monitor errors**: Check error log periodically during large batches
6. **Backup data**: Save copies of CSV before running scratch mode

## Integration with Phase 1

This Phase 2 catalog scraper depends on Phase 1 cross-reference data:

```
Phase 1 (Cross-Reference)
  ↓
hitachi_website_bushing_master_list.csv
  ↓ (extract unique ABB styles)
hitachi_website_bushing_catalog_master_list.csv (initialized)
  ↓ (scrape catalog data)
hitachi_website_bushing_catalog_master_list.csv (enriched with 53 fields)
```

**Workflow:**
```powershell
# Phase 1: Cross-reference data (run once or periodically)
python hitachi_website_data_batch_scraper.py --start 1 --end 10000 --delay 0.5

# Phase 2: Initialize catalog from Phase 1 results
python hitachi_website_catalog_batch_scraper.py --initialize

# Phase 2: Scrape catalog specifications
python hitachi_website_catalog_batch_scraper.py --all --delay 0.5
```

## Project Structure

```
hitachi_website_data_collection/
├── hitachi_website_data_scraper.py           # Phase 1: Cross-reference scraper
├── hitachi_website_data_batch_scraper.py     # Phase 1: Batch scraper
├── hitachi_website_catalog_scraper.py        # Phase 2: Catalog scraper (NEW)
├── hitachi_website_catalog_batch_scraper.py  # Phase 2: Batch catalog scraper (NEW)
├── hitachi_website_bushing_master_list.csv   # Phase 1 output: 7,100+ cross-references
├── hitachi_website_bushing_catalog_master_list.csv  # Phase 2 output: 1,364 detailed specs
├── hitachi_website_scraping_error_log.csv    # Phase 1 errors
├── hitachi_website_catalog_scraping_error_log.csv   # Phase 2 errors (NEW)
├── hitachi_website_data_raw/
│   ├── cross_reference_data/                 # Phase 1 HTML archives
│   └── catalog_data/                         # Phase 2 HTML archives (NEW)
├── README.md                                 # Main documentation
├── CATALOG_DATA_COLLECTION_README.md         # This file
└── CATALOG_SCRAPER_ARCHITECTURE.md           # Technical architecture
```

## Related Documentation

- [Main README](README.md) - Overall Hitachi data collection system
- [Catalog Scraper Architecture](CATALOG_SCRAPER_ARCHITECTURE.md) - Technical implementation details
- [Performance Improvements](PERFORMANCE_IMPROVEMENTS.md) - Phase 1 optimization notes
- [Quick Start Guide](QUICK_START.md) - Phase 1 getting started

## License & Disclaimer

This tool is for data collection purposes. Always respect the website's terms of service and robots.txt. Use reasonable delays between requests to avoid overloading the server.

## Version History

- **v1.0** (February 13, 2026) - Initial release
  - Complete catalog scraping functionality
  - 53 specification fields
  - Three write modes (append/overwrite/scratch)
  - Comprehensive error handling
  - Integration with Phase 1 cross-reference data
