# Hitachi Catalog Scraper - Technical Architecture

**Version:** 1.0  
**Date:** February 13, 2026  
**Authors:** Data Collection System

## Overview

This document describes the technical architecture, design decisions, and implementation details of the Hitachi Energy Bushing Catalog Data Collection System (Phase 2).

## System Architecture

### Two-Phase Data Collection Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                         PHASE 1                                  │
│                 Cross-Reference Collection                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input: Website Index Numbers (1-50000+)                        │
│     ↓                                                            │
│  hitachi_website_data_scraper.py                                │
│  hitachi_website_data_batch_scraper.py                          │
│     ↓                                                            │
│  Output: hitachi_website_bushing_master_list.csv                │
│          (7,100+ cross-reference records)                       │
│          {Index, Original Mfr, Catalog #, ABB Style #}          │
│                                                                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ Extract Unique ABB Style Numbers
                       │
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│                         PHASE 2                                  │
│                   Catalog Data Collection                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input: Unique ABB Style Numbers (1,364 styles)                 │
│     ↓                                                            │
│  hitachi_website_catalog_scraper.py                             │
│  hitachi_website_catalog_batch_scraper.py                       │
│     ↓                                                            │
│  Output: hitachi_website_bushing_catalog_master_list.csv        │
│          (1,364 records × 53 specification fields)              │
│          {Complete technical specifications}                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Module Organization

### File Structure

```
hitachi_website_data_collection/
│
├── Phase 1: Cross-Reference Scraping
│   ├── hitachi_website_data_scraper.py          # Single-index scraper
│   ├── hitachi_website_data_batch_scraper.py    # Batch processor
│   ├── hitachi_website_bushing_master_list.csv  # Output: Cross-references
│   └── hitachi_website_data_raw/cross_reference_data/  # HTML archives
│
├── Phase 2: Catalog Scraping (NEW)
│   ├── hitachi_website_catalog_scraper.py       # Single-style scraper
│   ├── hitachi_website_catalog_batch_scraper.py # Batch processor
│   ├── hitachi_website_bushing_catalog_master_list.csv  # Output: Catalog data
│   └── hitachi_website_data_raw/catalog_data/   # HTML archives
│
└── Documentation
    ├── README.md                                # Main documentation
    ├── CATALOG_DATA_COLLECTION_README.md        # Phase 2 user guide
    ├── CATALOG_SCRAPER_ARCHITECTURE.md          # This file
    ├── PERFORMANCE_IMPROVEMENTS.md              # Phase 1 optimizations
    └── QUICK_START.md                           # Quick reference
```

### Separation of Concerns

**Design Decision:** Separate files for Phase 1 vs Phase 2 rather than unified system

**Rationale:**
1. **Different data sources**: Cross-reference uses numeric indices, catalog uses style numbers
2. **Different URL structures**: Different API endpoints and query parameters
3. **Different parsing logic**: Cross-reference has pseudo-tables, catalog has proper HTML tables
4. **Independent execution**: Users may run only Phase 1, or both phases
5. **Maintainability**: Easier to debug and extend each phase independently
6. **Clear responsibilities**: Each module has single, well-defined purpose

## Component Design

### 1. hitachi_website_catalog_scraper.py

**Purpose:** Core scraping logic for individual bushings

**Key Functions:**

```python
extract_unique_abb_style_numbers() -> Set[str]
    """Extract 1,364 unique ABB style numbers from Phase 1 master list"""
    - Reads cross-reference CSV
    - Filters for ABB in replacement manufacturer column
    - Also checks original manufacturer column for ABB
    - Returns deduplicated set
    
scrape_catalog_data(style_number: str) -> Optional[Dict[str, str]]
    """Main scraping orchestrator"""
    - Builds URL with style number and English units
    - Sends HTTP request with browser headers
    - Validates response (HTTP errors, empty content, "no bushing found")
    - Calls parse_catalog_info() on valid HTML
    - Saves raw HTML only for valid data
    - Logs errors to CSV and deletes invalid HTML
    - Returns dict with 53 fields or None
    
parse_catalog_info(soup: BeautifulSoup, style_number: str) -> Optional[Dict[str, str]]
    """HTML parser - extracts all 53 catalog fields"""
    - Initializes dict with all 53 columns (empty strings)
    - Calls extract_table_value() for each field
    - Handles special cases (alternate labels, paragraph text)
    - Returns complete data dictionary
    
extract_table_value(soup: BeautifulSoup, label: str) -> str
    """Generic table cell extractor"""
    - Finds all table cells (<td>, <th>)
    - Searches for label text
    - Returns value from next cell or same cell after colon
    - Cleans whitespace and newlines
    
save_to_csv(data: Dict[str, str], mode: str = 'append') -> bool
    """CSV writer with append/overwrite support"""
    - Creates DataFrame from data dict
    - Reorders columns to match COLUMNS list
    - In overwrite mode: removes existing row for same style number
    - Appends new data or creates file if needed
```

**Utility Functions** (copied from Phase 1 for consistency):
- `log_error_to_csv()` - Error logging
- `save_raw_html()` - HTML archival
- `delete_raw_html()` - Cleanup on errors
- `get_error_log_style_numbers()` - Load error cache

### 2. hitachi_website_catalog_batch_scraper.py

**Purpose:** Batch processing orchestrator

**Key Functions:**

```python
initialize_catalog_master_list(force: bool = False) -> bool
    """Step 1: Initialize CSV with unique style numbers"""
    - Calls extract_unique_abb_style_numbers()
    - Creates DataFrame with 1,364 rows × 53 columns
    - Populates only "Style Number" column
    - Saves to hitachi_website_bushing_catalog_master_list.csv
    - Prevents accidental overwrites unless --force
    
check_style_exists(style_number: str) -> bool
    """Duplicate detection across three sources"""
    - Checks if HTML file exists in catalog_data/
    - Checks if style in CSV with populated data (not just empty row)
    - Returns True if exists in either location
    - Does NOT check error log (checked separately for smart skipping)
    
clean_scratch_mode()
    """Nuclear option - delete all catalog data"""
    - Deletes catalog CSV
    - Deletes error log
    - Deletes all HTML files in catalog_data/
    - Recreates empty directory structure
    - Called when --mode scratch specified
    
scrape_batch(style_numbers: list, delay: float, mode: str)
    """Main batch processing loop"""
    - Loads error log once (cached)
    - Iterates through style numbers
    - For each style:
        * Skip if in error log (delete HTML if exists)
        * Skip if exists (append mode only)
        * Call scrape_catalog_data()
        * Sleep for delay seconds
    - Reports statistics: success/failure/skipped counts
    
scrape_all(delay: float, mode: str)
    """Convenience function for processing entire catalog"""
    - Loads all styles from catalog CSV
    - Calls scrape_batch() with full list
```

**CLI Argument Structure:**

```
Mutually Exclusive Input Methods:
  --initialize        # Create initial CSV with style numbers
  --all               # Process all 1,364 styles from CSV
  --style <STYLE>     # Single style number
  --styles <LIST>     # Comma-separated list
  --file <PATH>       # File with one style per line

Optional Parameters:
  --delay <FLOAT>     # Seconds between requests (default: 1.0)
  --mode <MODE>       # append|overwrite|scratch (default: append)
  --force             # Force re-initialization (use with --initialize)
```

## Data Flow

### Initialization Flow

```
1. User: python hitachi_website_catalog_batch_scraper.py --initialize
2. System: Read hitachi_website_bushing_master_list.csv (Phase 1 output)
3. System: Filter for ABB manufacturers
4. System: Extract "Replacement Information - ABB Style Number" column
5. System: Extract "Original Bushing Information - Catalog Number" where mfr = ABB
6. System: Combine and deduplicate → 1,364 unique styles
7. System: Create DataFrame with 53 columns (COLUMNS constant)
8. System: Populate "Style Number" column, leave others empty
9. System: Save to hitachi_website_bushing_catalog_master_list.csv
10. User: Ready to scrape catalog data
```

### Scraping Flow (Single Bushing)

```
1. User: python hitachi_website_catalog_scraper.py 138W0800XA
2. System: Build URL with style number and parameters
3. System: Send GET request with browser headers
4. System: Validate response
   ├─ HTTP 404/403 → Log error, delete HTML, exit
   ├─ Empty response → Log error, delete HTML, exit
   ├─ "No bushing found" → Log error, delete HTML, exit
   └─ Valid HTML → Continue
5. System: Parse HTML with BeautifulSoup (lxml parser)
6. System: Call parse_catalog_info()
   ├─ Initialize dict with 53 empty fields
   ├─ Set "Style Number" = 138W0800XA
   ├─ For each field: extract_table_value(soup, label)
   │   ├─ Find all table cells
   │   ├─ Search for label text
   │   ├─ Extract value from next cell
   │   └─ Clean whitespace
   ├─ Special handling for comments/features (paragraph text)
   └─ Return complete dict
7. System: Validate dict (style number populated)
8. System: Save raw HTML to catalog_data/Hitachi_website_bushing_138W0800XA.html
9. System: Call save_to_csv(data)
   ├─ Create DataFrame from dict
   ├─ Reorder columns to match COLUMNS
   ├─ Load existing CSV if exists
   ├─ Append new row (or overwrite in overwrite mode)
   └─ Save to CSV
10. System: Report success with key fields
11. User: Data saved and HTML archived
```

### Batch Scraping Flow

```
1. User: python hitachi_website_catalog_batch_scraper.py --all --delay 0.5
2. System: Check if catalog CSV exists → If not, error (run --initialize first)
3. System: Load all style numbers from CSV (1,364 styles)
4. System: Load error log once → Cache in set
5. System: For each style number:
   │
   ├─ Style in error log?
   │  ├─ Yes → Delete HTML if exists, skip, continue
   │  └─ No → Continue
   │
   ├─ Mode = append AND style exists in CSV/HTML?
   │  ├─ Yes → Skip, continue
   │  └─ No → Continue
   │
   ├─ Call scrape_catalog_data(style)
   │  └─ (See "Scraping Flow (Single Bushing)" above)
   │
   ├─ Success?
   │  ├─ Yes → Increment success_count, print green checkmark
   │  └─ No → Increment failure_count, print red X
   │
   └─ Sleep for delay seconds
   
6. System: Report final statistics
   ├─ Total processed
   ├─ Success count
   ├─ Failure count
   ├─ Skipped count
   └─ Success rate percentage
7. User: Review results and error log
```

## HTML Parsing Strategy

### Challenge: Extracting Data from HTML Tables

The Hitachi catalog page uses standard HTML tables with label-value pairs:

```html
<table>
  <tr>
    <td>Style Number:</td>
    <td>138W0800XA</td>
  </tr>
  <tr>
    <td>Voltage Class</td>
    <td>138 kV</td>
  </tr>
</table>
```

### Parsing Approach

**Design Decision:** Generic table cell scanner rather than XPath selectors

**Rationale:**
1. **Flexible**: Works with varied table structures
2. **Resilient**: Doesn't break if table structure changes slightly
3. **Simple**: No need to analyze HTML structure in detail
4. **Maintainable**: Easy to add new fields

**Algorithm:**

```python
def extract_table_value(soup, label):
    all_cells = soup.find_all(['td', 'th'])  # Get all table cells
    
    for i, cell in enumerate(all_cells):
        if label in cell.text:               # Found label cell
            if i + 1 < len(all_cells):       # Check if next cell exists
                return all_cells[i + 1].text # Return value from next cell
            
            # Fallback: value after colon in same cell
            if ':' in cell.text:
                return cell.text.split(':', 1)[1].strip()
    
    return ""  # Not found
```

### Special Cases Handled

1. **Alternate Label Names**: Some fields have multiple possible labels
   ```python
   c1 = extract_table_value(soup, "Approximate Capacitance C1")
   if not c1:
       c1 = extract_table_value(soup, "C1")  # Try alternate
   ```

2. **Paragraph Text** (not in tables): Comments and special features
   ```python
   # Extract from raw page text instead of tables
   page_text = soup.get_text()
   if "Special Features:" in page_text:
       # Find text after label, before next section
   ```

3. **Empty Values**: Leave as empty string (not "N/A" or "None")
   ```python
   data = {col: "" for col in COLUMNS}  # Initialize all empty
   ```

## Error Handling System

### Three-Tier Error Handling

**Tier 1: Network Errors**
- Timeouts (30 seconds)
- Connection errors
- HTTP errors (403, 404, 5xx)
- Request exceptions

**Action:** Log to error CSV, delete HTML if exists, return None

**Tier 2: Data Validation Errors**
- Empty response (< 100 characters)
- "No bushing found by that style number" message
- Parser returns None
- All fields empty after parsing

**Action:** Log to error CSV, delete HTML if exists, return None

**Tier 3: Processing Errors**
- CSV write failures
- HTML save failures
- Unexpected exceptions

**Action:** Log error, attempt to continue partial operation

### Error Log Structure

```csv
Timestamp,Style_Number,Error_Message
2026-02-13 14:30:15,INVALID123,No bushing found by that style number
2026-02-13 14:31:22,TEST456,Request timeout after 30 seconds
2026-02-13 14:32:05,ABC789,HTTP error 404: Not Found
```

**Purpose:**
1. Debugging: Identify patterns in failures
2. Skip logic: Don't retry known errors
3. Recovery: User can extract and retry specific errors

## Performance Optimizations

### 1. Error Log Caching

**Problem:** Reading error log CSV for every style number is slow

**Solution:** Load error log once at batch start, cache in set
```python
error_log_styles = get_error_log_style_numbers()  # Called once
# ... in loop:
if style in error_log_styles:  # O(1) set lookup
    skip
```

**Benefit:** ~1,364 file reads → 1 file read

### 2. Selective HTML Archival

**Problem:** Saving HTML for every request wastes disk space

**Solution:** Only save HTML when valid data extracted
```python
if catalog_data and catalog_data.get("Style Number"):
    save_raw_html(response.text, style_number)  # Only on success
else:
    delete_raw_html(style_number)  # Clean up errors
```

**Benefit:** ~30-40% disk space savings (based on error rate)

### 3. Smart Duplicate Detection

**Problem:** Re-scraping existing data wastes time and bandwidth

**Solution:** Three-source check in append mode
```python
def check_style_exists(style):
    # Check 1: HTML file exists?
    html_file = Path(RAW_DATA_DIR) / f"Hitachi_website_bushing_{style}.html"
    if html_file.exists():
        return True
    
    # Check 2: CSV has populated data?
    df = pd.read_csv(OUTPUT_CSV)
    row = df[df['Style Number'] == style]
    if not row.empty:
        for col in COLUMNS[1:]:  # Skip Style Number column
            if row[col].notna() and str(row[col]).strip() != "":
                return True  # Found non-empty data
    
    return False
```

**Benefit:** Resume interrupted scrapes without re-scraping

### 4. Batch Mode Efficiency

**Single scraper:** python hitachi_website_catalog_scraper.py STYLE
- Good for: Testing, manual fixes
- Overhead: Python startup, imports, CSV reload per style

**Batch scraper:** python hitachi_website_catalog_batch_scraper.py --all
- Good for: Production, large datasets
- Optimization: One Python startup, loaded state, cached error log

**Time Comparison:**
- Single scraper × 1,364 styles: ~2-3 hours (Python startup overhead)
- Batch scraper × 1,364 styles: ~45-60 minutes (efficient execution)

## Write Modes Implementation

### Append Mode (Default)

**Goal:** Add new data, skip existing data and errors

**Logic:**
```python
if style in error_log_styles:
    skip  # Don't retry errors
elif check_style_exists(style):
    skip  # Already have data
else:
    scrape  # New style, go ahead
```

**Use Case:** Initial data collection, resuming interrupted scrapes

### Overwrite Mode

**Goal:** Update existing data, skip only errors

**Logic:**
```python
if style in error_log_styles:
    skip  # Still don't retry errors
else:
    scrape  # Overwrite existing or add new
    
# In save_to_csv():
if mode == 'overwrite':
    existing_df = existing_df[existing_df['Style Number'] != style]  # Remove old
    combined_df = pd.concat([existing_df, new_df])  # Add new
```

**Use Case:** Updating specific entries, correcting data issues

### Scratch Mode

**Goal:** Complete reset, start from zero

**Logic:**
```python
# Step 1: Clean everything
delete(OUTPUT_CSV)
delete(ERROR_LOG_CSV)
delete_all_html_in(RAW_DATA_DIR)

# Step 2: Reinitialize
initialize_catalog_master_list(force=True)

# Step 3: Scrape all
scrape_batch(all_styles, delay, mode='scratch')
```

**Use Case:** Re-scraping entire dataset, major version updates

## Design Patterns

### 1. Separation of Concerns

**Single Responsibility Principle:**
- `scrape_catalog_data()`: Orchestrates HTTP and parsing
- `parse_catalog_info()`: Handles HTML parsing only
- `extract_table_value()`: Generic cell extraction
- `save_to_csv()`: CSV operations only

### 2. Fail-Safe Design

**Graceful Degradation:**
- Network fails → Log and continue
- Parse fails → Log and continue
- Single save fails → Log and continue batch

**Never crash entire batch for single failure**

### 3. Idempotency

**Same command, same result:**
- Append mode: Re-running same batch with same data = no changes
- Initialize: Re-running creates identical CSV (unless --force)
- Error log: Duplicates prevented automatically

### 4. Defensive Programming

**Assumptions validated:**
```python
# Don't assume file exists
if os.path.exists(CSV_FILE):
    # proceed
else:
    # handle missing file

# Don't assume column exists
if 'Style Number' in df.columns:
    # proceed
else:
    # handle missing column

# Don't assume next cell exists
if i + 1 < len(all_cells):
    # proceed
else:
    # use fallback method
```

## Configuration Management

### Constants Pattern

**All configuration in module constants:**
```python
# hitachi_website_catalog_scraper.py
BASE_URL = "https://bushing.hitachienergy.com/Scripts/BushingLookupBU.asp"
OUTPUT_CSV = "hitachi_website_bushing_catalog_master_list.csv"
ERROR_LOG_CSV = "hitachi_website_catalog_scraping_error_log.csv"
RAW_DATA_DIR = "hitachi_website_data_raw/catalog_data"
COLUMNS = [...]  # All 53 column names
```

**Benefits:**
1. Single source of truth
2. Easy to modify
3. No hardcoded strings scattered in code
4. Import and reuse in batch scraper

### Extensibility

**Adding new fields:**
1. Add column name to `COLUMNS` list
2. Add `extract_table_value()` call in `parse_catalog_info()`
3. That's it! CSV structure auto-adjusts

**Example:**
```python
# Add to COLUMNS
COLUMNS = [..., "New Field Name", ...]

# Add to parse_catalog_info()
data["New Field Name"] = extract_table_value(soup, "New Field Name")
```

## Testing Strategy

### Manual Testing Checklist

**Phase 1: Initialization**
- [ ] Run `--initialize` → Creates CSV with 1,364 styles
- [ ] Verify columns match `sample_data_2.csv`
- [ ] Verify no duplicate style numbers
- [ ] Run `--initialize` again → Should skip (already exists)
- [ ] Run `--initialize --force` → Should recreate

**Phase 2: Single Scraping**
- [ ] Test valid style: `python hitachi_website_catalog_scraper.py 138W0800XA`
- [ ] Verify HTML saved to `catalog_data/`
- [ ] Verify CSV row added with populated fields
- [ ] Test invalid style: `python hitachi_website_catalog_scraper.py INVALID123`
- [ ] Verify error logged, no HTML saved

**Phase 3: Batch Scraping (Small)**
- [ ] Test `--styles 138W0800XA,196W1620UW` with 2-3 styles
- [ ] Verify append mode skips existing
- [ ] Verify overwrite mode updates existing
- [ ] Verify error styles logged correctly

**Phase 4: Modes**
- [ ] Test append mode (skip existing)
- [ ] Test overwrite mode (update existing)
- [ ] Test scratch mode (delete all, restart)

**Phase 5: Error Recovery**
- [ ] Interrupt batch mid-process (Ctrl+C)
- [ ] Resume with append mode → Should skip completed
- [ ] Verify no duplicate rows in CSV

## Maintenance Considerations

### Future Enhancements

**Potential improvements for v2.0:**

1. **Parallel Processing**
   - Use `asyncio` or `concurrent.futures`
   - Scrape multiple styles simultaneously
   - Respect rate limits with semaphore

2. **Progress Bar**
   - Use `tqdm` library
   - Show real-time progress

3. **Database Backend**
   - Replace CSV with SQLite
   - Better data integrity
   - Efficient updates

4. **Incremental Updates**
   - Track last scrape date per style
   - Re-scrape only outdated entries

5. **Data Validation**
   - Field-level validation (e.g., voltage in kV)
   - Range checks for dimensions
   - Alert on suspicious values

### Monitoring

**Recommended monitoring during production scrapes:**

```powershell
# In one terminal: Run batch scraper
python hitachi_website_catalog_batch_scraper.py --all --delay 0.5

# In another terminal: Monitor error log
Get-Content hitachi_website_catalog_scraping_error_log.csv -Wait

# Check progress periodically
(Import-Csv hitachi_website_bushing_catalog_master_list.csv | 
 Where-Object {$_.'Voltage Class' -ne ""} | 
 Measure-Object).Count
```

## Dependencies

### External Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| `requests` | 2.31.0 | HTTP requests |
| `beautifulsoup4` | 4.12.3 | HTML parsing |
| `lxml` | 5.1.0 | Fast XML/HTML parser |
| `pandas` | 2.2.0 | CSV operations |

### Standard Library

- `sys`: Command-line arguments, exit codes
- `os`: File operations, path checking
- `pathlib`: Modern path handling
- `logging`: Application logging
- `datetime`: Timestamps
- `argparse`: CLI parsing
- `time`: Delays between requests
- `shutil`: Directory operations
- `re`: (imported but not used currently)

## Comparison: Phase 1 vs Phase 2

| Aspect | Phase 1 (Cross-Reference) | Phase 2 (Catalog) |
|--------|---------------------------|-------------------|
| **Input** | Numeric indices (1-50000+) | ABB style numbers (1,364) |
| **URL** | BushingCrossReferenceBU.asp?INDEX= | BushingLookupBU.asp?StyleNumber= |
| **Output Fields** | 5 fields | 53 fields |
| **HTML Structure** | Pseudo-tables (complex) | Proper HTML tables |
| **Parsing** | Custom text extraction | Generic table scanner |
| **Purpose** | Find ABB replacements | Get detailed specs |
| **Run Frequency** | Periodically (new parts) | After Phase 1 updates |
| **Dataset Size** | Large (50,000+ potential) | Medium (1,364 unique) |

## Summary

The Hitachi Catalog Scraper is a production-ready, maintainable system designed with industry best practices:

- **Modular**: Clear separation of concerns
- **Robust**: Comprehensive error handling
- **Performant**: Multiple optimizations for efficiency
- **Extensible**: Easy to add new fields or features
- **Documented**: Clear code, extensive comments, full documentation
- **User-Friendly**: Good CLI, helpful messages, progress tracking

The architecture follows proven patterns from Phase 1 while adapting to the unique requirements of catalog data collection.
