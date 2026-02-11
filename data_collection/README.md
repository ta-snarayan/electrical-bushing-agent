# Electrical Bushing Data Collection System

A comprehensive multi-website data collection system for electrical bushing cross-reference information.

## Overview

This project collects electrical bushing cross-reference data from multiple manufacturer and distributor websites. Each website has its own dedicated scraper module organized in separate directories for maintainability and scalability.

## Project Structure

```
data_collection/
├── hitachi_website_data_collection/        # Hitachi Energy website scraper
│   ├── hitachi_website_data_scraper.py
│   ├── hitachi_website_data_batch_scraper.py
│   ├── hitachi_website_bushing_master_list.csv
│   ├── hitachi_website_scraping_error_log.csv
│   ├── hitachi_website_data_raw/
│   └── README.md
├── pcore_website_data_collection/          # PCORE website scraper (future)
├── <other_website>_data_collection/        # Additional scrapers (future)
└── requirements.txt                        # Shared Python dependencies
```

## Available Data Collectors

### ✅ Hitachi Energy Bushing Cross-Reference

**Status**: Fully operational (v2.0)  
**Location**: `hitachi_website_data_collection/`  
**Test Results**: 89% success rate (89/100 indices), 11 empty pages  
**Features**:
- Comprehensive error handling with CSV logging
- Raw HTML archival
- Batch processing (1-50,000+ indices)
- Detailed documentation

**Quick Start**:
```powershell
cd hitachi_website_data_collection
python hitachi_website_data_batch_scraper.py --start 1 --end 100 --delay 0.5
```

**Documentation**: See [hitachi_website_data_collection/README.md](hitachi_website_data_collection/README.md)

### 🔜 PCORE Website (Coming Soon)

**Status**: Planned  
**Location**: `pcore_website_data_collection/` (to be created)

### 🔜 Additional Websites (Coming Soon)

Additional manufacturer and distributor websites will be added following the same organizational pattern.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Internet connection

### Setup

1. Navigate to the data_collection directory:
```powershell
cd data_collection
```

2. Install shared dependencies:
```powershell
pip install -r requirements.txt
```

3. Navigate to the specific website collector you want to use:
```powershell
cd hitachi_website_data_collection
```

4. Follow the specific README for usage instructions

## Shared Dependencies

All website collectors use the following shared dependencies (defined in `requirements.txt`):

- **requests 2.31.0**: HTTP client with browser-like headers
- **beautifulsoup4 4.12.3**: HTML parsing and data extraction
- **lxml 5.1.0**: Fast XML and HTML parser
- **pandas 2.2.0**: CSV operations and data management

## Design Principles

### Modular Organization

Each website scraper is organized in its own directory with:
- Self-contained Python modules
- Dedicated output files with website-specific prefixes
- Independent documentation
- Isolated raw data storage
- Separate error logs

### Naming Convention

All files follow a consistent naming pattern:
- Python modules: `<website>_data_scraper.py`, `<website>_data_batch_scraper.py`
- Output CSV: `<website>_bushing_master_list.csv`
- Error log: `<website>_scraping_error_log.csv`
- Raw data directory: `<website>_data_raw/`
- Documentation: `README.md` within each directory

### Shared Features

All scrapers implement:
- ✅ CSV output with standardized column structure
- ✅ Raw HTML archival for debugging and re-parsing
- ✅ Comprehensive error handling and logging
- ✅ Batch processing capabilities
- ✅ Progress tracking and summary statistics
- ✅ Configurable request delays
- ✅ Detailed logging (INFO/WARNING/ERROR levels)

## Usage Patterns

### Single Index Scraping

```powershell
cd <website>_data_collection
python <website>_data_scraper.py <index>
```

### Batch Scraping

```powershell
cd <website>_data_collection
python <website>_data_batch_scraper.py --start <start> --end <end> --delay <delay>
```

### Error Analysis

After a large batch run, check the error log:
```powershell
# View error summary
Get-Content <website>_scraping_error_log.csv | Select-Object -First 20

# Count errors by type
Import-Csv <website>_scraping_error_log.csv | Group-Object Error_Type | Select-Object Name, Count
```

## Testing & Validation

### Hitachi Energy

- **Test Range**: Indices 1-100
- **Success Rate**: 89% (89 valid, 11 empty pages)
- **Test Date**: February 10, 2026
- **Status**: ✅ Production ready

See [hitachi_website_data_collection/README.md](hitachi_website_data_collection/README.md) for detailed test results.

## Adding New Website Collectors

To add a new website collector:

1. Create a new directory: `<website>_data_collection/`
2. Copy the template structure from `hitachi_website_data_collection/`
3. Update all file names with the new website prefix
4. Modify the scraper logic for the target website
5. Update constants (BASE_URL, OUTPUT_CSV, etc.)
6. Test thoroughly and document
7. Update this README with the new collector

## Troubleshooting

### Common Issues

**Issue**: Import errors when running scrapers  
**Solution**: Install requirements: `pip install -r requirements.txt`

**Issue**: Files not found  
**Solution**: Ensure you're in the correct website directory: `cd <website>_data_collection`

**Issue**: Permission denied  
**Solution**: Run PowerShell as administrator or check file permissions

**Issue**: Network timeouts  
**Solution**: Increase delay between requests or check internet connection

### Getting Help

1. Check the specific website collector's README
2. Review error logs: `<website>_scraping_error_log.csv`
3. Check Python logs in console output
4. Verify internet connectivity to target website

## Performance Considerations

### Request Delays

- **Minimum recommended**: 0.5 seconds between requests
- **Conservative**: 1.0-2.0 seconds for large batches
- **Rationale**: Be respectful to target servers, avoid rate limiting

### Large-Scale Operations

For processing thousands of indices:
- Use batch scraper with appropriate delays
- Monitor error logs for patterns
- Consider running during off-peak hours
- Save progress incrementally (CSV appends automatically)

### Resource Usage

- **Memory**: Minimal (~50-100 MB per scraper instance)
- **Disk**: ~20 KB per raw HTML file
- **Network**: ~30 KB download per index

## Data Management

### Output Organization

Each website collector produces:
- **Structured CSV**: Main data file for analysis
- **Raw HTML**: Archive of original source data
- **Error Log**: CSV tracking all failures

### Data Retention

- Raw HTML files enable re-parsing if scraper logic improves
- Error logs allow retry of failed indices
- CSV files support incremental updates (append mode)

### Backup Recommendations

Regular backups of:
- CSV output files (master lists)
- Error logs (for analysis and retry)
- Raw HTML directories (if re-parsing needed)

## Version History

**v2.0** (February 10, 2026)
- Major reorganization for multi-website support
- Modular directory structure
- Consistent naming convention across all files
- Prepared for PCORE and additional website collectors

**v1.3** (February 10, 2026)
- Added comprehensive error handling with CSV logging
- Support for large-scale automation (50,000+ indices)
- Tested with Hitachi indices 1-100

**v1.0-1.2** (February 10, 2026)
- Initial Hitachi Energy scraper development
- Raw HTML storage implementation
- Batch processing capabilities

## License

Internal use only - Electrical Bushing Data Collection System

## Contact

For issues, questions, or to contribute new website collectors, contact the development team.

---

**Last Updated**: February 10, 2026  
**System Version**: 2.0  
**Active Collectors**: 1 (Hitachi Energy)  
**Planned Collectors**: PCORE, additional manufacturers
