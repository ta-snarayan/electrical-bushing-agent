"""
Hitachi Website Batch Bushing Catalog Data Scraper

This script allows scraping multiple bushing catalog specifications in one run, with 
configurable delay between requests to be respectful to the server. Features robust 
error handling and logging for large-scale automation (supports 1,000+ style numbers).

This is Phase 2 of the data collection:
  Phase 1: Cross-reference scraper collects ABB style numbers
  Phase 2: Catalog scraper enriches those style numbers with full specifications

Write Modes:
    --mode append (default): Skip style numbers that already exist in CSV and raw data folder
    --mode overwrite: Overwrite existing data file-by-file (incremental updates)
    --mode scratch: Delete all existing catalog data and start fresh

Usage:
    python hitachi_website_catalog_batch_scraper.py --initialize
    python hitachi_website_catalog_batch_scraper.py --all --delay 0.5
    python hitachi_website_catalog_batch_scraper.py --style 138W0800XA
    python hitachi_website_catalog_batch_scraper.py --styles 138W0800XA,196W1620UW --mode overwrite
    python hitachi_website_catalog_batch_scraper.py --file style_numbers.txt --delay 0.5

Author: Data Collection System
Date: February 13, 2026
Version: 1.0 - Initial catalog batch scraping implementation
"""

import argparse
import time
import sys
import os
import shutil
import pandas as pd
from pathlib import Path
from hitachi_website_catalog_scraper import (
    scrape_catalog_data,
    save_to_csv,
    extract_unique_abb_style_numbers,
    logger,
    ERROR_LOG_CSV,
    OUTPUT_CSV,
    RAW_DATA_DIR,
    COLUMNS,
    get_error_log_style_numbers,
    delete_raw_html
)


def initialize_catalog_master_list(force: bool = False) -> bool:
    """
    Initialize the catalog master list CSV with unique ABB style numbers.
    Creates a CSV with headers and unique style numbers in the first column.
    
    Args:
        force: If True, recreate even if file exists
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if file already exists
        if os.path.exists(OUTPUT_CSV) and not force:
            logger.info(f"Catalog master list already exists: {OUTPUT_CSV}")
            print(f"ℹ  Catalog master list already exists: {OUTPUT_CSV}")
            print(f"   Use --force to recreate it")
            return True
        
        logger.info("Extracting unique ABB style numbers from cross-reference master list...")
        print("📋 Extracting unique ABB style numbers from cross-reference master list...")
        
        # Extract unique style numbers
        style_numbers = extract_unique_abb_style_numbers()
        
        if not style_numbers:
            logger.error("No ABB style numbers found")
            print("✗ No ABB style numbers found in cross-reference master list")
            return False
        
        logger.info(f"Found {len(style_numbers)} unique ABB style numbers")
        print(f"✓ Found {len(style_numbers)} unique ABB style numbers")
        
        # Create DataFrame with style numbers in first column, other columns empty
        data_rows = []
        for style in sorted(style_numbers):
            row = {col: "" for col in COLUMNS}
            row["Style Number"] = style
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        df = df[COLUMNS]  # Ensure column order
        
        # Save to CSV
        df.to_csv(OUTPUT_CSV, index=False)
        logger.info(f"Created catalog master list: {OUTPUT_CSV}")
        print(f"✓ Created catalog master list: {OUTPUT_CSV}")
        print(f"  Total style numbers: {len(style_numbers)}")
        print(f"\nNext step: Run batch scraper to populate catalog data")
        print(f"  python hitachi_website_catalog_batch_scraper.py --all --delay 0.5")
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing catalog master list: {e}")
        print(f"✗ Error initializing catalog master list: {e}")
        return False


def check_style_exists(style_number: str) -> bool:
    """
    Check if a style number already has complete data in CSV or raw HTML files.
    Does NOT check error log (error log is checked separately).
    
    Args:
        style_number: The bushing style number to check
        
    Returns:
        True if the style number has data in CSV or HTML file; False otherwise
    """
    # Check if raw HTML file exists
    safe_style = style_number.replace("/", "_").replace("\\", "_")
    html_file = Path(RAW_DATA_DIR) / f"Hitachi_website_bushing_{safe_style}.html"
    html_exists = html_file.exists()
    
    # Check if style number exists in CSV with populated data
    csv_exists = False
    if os.path.exists(OUTPUT_CSV):
        try:
            df = pd.read_csv(OUTPUT_CSV)
            matching_rows = df[df['Style Number'] == style_number]
            if not matching_rows.empty:
                # Check if at least one field besides Style Number is populated
                row = matching_rows.iloc[0]
                for col in COLUMNS[1:]:  # Skip first column (Style Number)
                    if pd.notna(row[col]) and str(row[col]).strip() != "":
                        csv_exists = True
                        break
        except Exception as e:
            logger.warning(f"Error checking CSV for style {style_number}: {e}")
    
    return html_exists or csv_exists


def clean_scratch_mode():
    """
    Clean all existing catalog data for scratch mode (fresh start).
    Deletes the CSV file, error log, and all raw HTML files in catalog_data/.
    """
    logger.info("SCRATCH MODE: Cleaning all existing catalog data...")
    print("🗑️  SCRATCH MODE: Cleaning all existing catalog data...")
    
    # Delete CSV file
    if os.path.exists(OUTPUT_CSV):
        os.remove(OUTPUT_CSV)
        logger.info(f"Deleted {OUTPUT_CSV}")
        print(f"  ✓ Deleted {OUTPUT_CSV}")
    
    # Delete error log
    if os.path.exists(ERROR_LOG_CSV):
        os.remove(ERROR_LOG_CSV)
        logger.info(f"Deleted {ERROR_LOG_CSV}")
        print(f"  ✓ Deleted {ERROR_LOG_CSV}")
    
    # Delete all raw HTML files in catalog_data
    raw_data_path = Path(RAW_DATA_DIR)
    if raw_data_path.exists():
        file_count = len(list(raw_data_path.glob("*.html")))
        shutil.rmtree(raw_data_path)
        logger.info(f"Deleted {RAW_DATA_DIR}/ directory ({file_count} HTML files)")
        print(f"  ✓ Deleted {RAW_DATA_DIR}/ directory ({file_count} HTML files)")
    
    # Recreate the raw data directory
    raw_data_path.mkdir(parents=True, exist_ok=True)
    logger.info("Clean completed - starting fresh")
    print("  ✓ Clean completed - starting fresh\n")


def scrape_batch(style_numbers: list, delay: float = 1.0, mode: str = 'append'):
    """
    Scrape a list of style numbers.
    
    Args:
        style_numbers: List of ABB style numbers to scrape
        delay: Delay in seconds between requests (default: 1.0)
        mode: Write mode - 'append' (skip existing), 'overwrite' (replace existing), 'scratch' (delete all first)
    """
    # Handle scratch mode
    if mode == 'scratch':
        clean_scratch_mode()
        # Re-initialize the catalog master list after cleaning
        print("Reinitializing catalog master list after scratch...\n")
        if not initialize_catalog_master_list(force=True):
            logger.error("Failed to reinitialize catalog master list")
            sys.exit(1)
    
    # Load error log style numbers once at the start
    error_log_styles = get_error_log_style_numbers()
    logger.info(f"Loaded {len(error_log_styles)} style numbers from error log")
    
    total = len(style_numbers)
    success_count = 0
    failure_count = 0
    skipped_count = 0
    
    logger.info(f"Starting batch scrape for {total} style numbers - Mode: {mode.upper()}")
    print(f"\n{'='*70}")
    print(f"Batch Scraping Catalog Data - Mode: {mode.upper()}")
    print(f"{'='*70}")
    print(f"Total style numbers to process: {total}")
    print(f"Delay between requests: {delay}s\n")
    
    for idx, style in enumerate(style_numbers, 1):
        # Check if this style is in the error log
        if style in error_log_styles:
            skipped_count += 1
            # Delete HTML file if it exists
            delete_raw_html(style)
            logger.info(f"Skipping style {style} (in error log, HTML deleted if existed) ({idx}/{total})")
            print(f"⊘ [{idx}/{total}] Style {style}: Skipped (in error log)")
            continue
        
        # Check if we should skip this style (append mode only)
        if mode == 'append' and check_style_exists(style):
            skipped_count += 1
            logger.info(f"Skipping style {style} (already exists) ({idx}/{total})")
            print(f"⊘ [{idx}/{total}] Style {style}: Skipped (already processed)")
            continue
        
        action = "Overwriting" if mode == 'overwrite' and check_style_exists(style) else "Processing"
        logger.info(f"{action} style {style} ({idx}/{total})")
        
        catalog_data = scrape_catalog_data(style)
        
        if catalog_data:
            if save_to_csv(catalog_data, mode=mode):
                success_count += 1
                prefix = "↻" if mode == 'overwrite' and check_style_exists(style) else "✓"
                print(f"{prefix} [{idx}/{total}] Style {style}: {catalog_data['Voltage Class']} | "
                      f"{catalog_data['Current Rating Draw Lead']} | "
                      f"{catalog_data['Apparatus']}")
            else:
                failure_count += 1
                print(f"✗ [{idx}/{total}] Style {style}: Failed to save to CSV")
        else:
            failure_count += 1
            print(f"✗ [{idx}/{total}] Style {style}: Failed to scrape (logged to error log)")
        
        # Delay between requests (except for the last one)
        if idx < total:
            time.sleep(delay)
    
    logger.info(f"Batch scrape completed: {success_count} successful, {failure_count} failed, {skipped_count} skipped")
    print(f"\n{'='*70}")
    print(f"Batch Scraping Complete - Mode: {mode.upper()}")
    print(f"{'='*70}")
    print(f"Total Style Numbers: {total}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    if mode == 'append' or mode == 'overwrite':
        print(f"Skipped (already exist or in error log): {skipped_count}")
    print(f"Success Rate: {(success_count/(total-skipped_count)*100 if total-skipped_count > 0 else 0):.1f}%")
    
    # Check if error log exists and inform user
    if failure_count > 0 and os.path.exists(ERROR_LOG_CSV):
        print(f"\n⚠  Errors logged to: {ERROR_LOG_CSV}")
        print(f"   Review this file for details on {failure_count} failed style numbers")
    
    if success_count > 0:
        print(f"\n✓ Data saved to: {OUTPUT_CSV}")
        print(f"✓ Raw HTML saved to: {RAW_DATA_DIR}/")


def scrape_all(delay: float = 1.0, mode: str = 'append'):
    """
    Scrape all style numbers from the catalog master list.
    
    Args:
        delay: Delay in seconds between requests (default: 1.0)
        mode: Write mode - 'append' (skip existing), 'overwrite' (replace existing), 'scratch' (delete all first)
    """
    try:
        # Check if catalog master list exists
        if not os.path.exists(OUTPUT_CSV):
            logger.error(f"Catalog master list not found: {OUTPUT_CSV}")
            print(f"✗ Catalog master list not found: {OUTPUT_CSV}")
            print(f"  Run with --initialize first to create the master list")
            sys.exit(1)
        
        # Load all style numbers from the master list
        df = pd.read_csv(OUTPUT_CSV)
        style_numbers = df['Style Number'].dropna().unique().tolist()
        
        if not style_numbers:
            logger.error("No style numbers found in catalog master list")
            print("✗ No style numbers found in catalog master list")
            sys.exit(1)
        
        logger.info(f"Loaded {len(style_numbers)} style numbers from catalog master list")
        print(f"📋 Loaded {len(style_numbers)} style numbers from catalog master list")
        
        # Start batch scraping
        scrape_batch(style_numbers, delay, mode)
        
    except Exception as e:
        logger.error(f"Error in scrape_all: {e}")
        print(f"✗ Error: {e}")
        sys.exit(1)


def scrape_from_file(filepath: str, delay: float = 1.0, mode: str = 'append'):
    """
    Scrape style numbers listed in a text file (one style number per line).
    
    Args:
        filepath: Path to file containing style numbers
        delay: Delay in seconds between requests (default: 1.0)
        mode: Write mode - 'append' (skip existing), 'overwrite' (replace existing), 'scratch' (delete all first)
    """
    try:
        with open(filepath, 'r') as f:
            style_numbers = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    style_numbers.append(line)
        
        if not style_numbers:
            logger.error(f"No valid style numbers found in file: {filepath}")
            print(f"✗ No valid style numbers found in file: {filepath}")
            sys.exit(1)
        
        logger.info(f"Loaded {len(style_numbers)} style numbers from file: {filepath}")
        print(f"📋 Loaded {len(style_numbers)} style numbers from file: {filepath}")
        
        scrape_batch(style_numbers, delay, mode)
        
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        print(f"✗ File not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        print(f"✗ Error reading file: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Batch scraper for Hitachi Energy bushing catalog data',
        epilog='Examples:\n'
               '  python hitachi_website_catalog_batch_scraper.py --initialize\n'
               '  python hitachi_website_catalog_batch_scraper.py --all --delay 0.5\n'
               '  python hitachi_website_catalog_batch_scraper.py --style 138W0800XA\n'
               '  python hitachi_website_catalog_batch_scraper.py --styles 138W0800XA,196W1620UW --mode overwrite\n'
               '  python hitachi_website_catalog_batch_scraper.py --file style_numbers.txt\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Create mutually exclusive group for input methods
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--initialize', action='store_true',
                            help='Initialize catalog master list with unique ABB style numbers')
    input_group.add_argument('--all', action='store_true',
                            help='Process all style numbers from catalog master list')
    input_group.add_argument('--style', type=str,
                            help='Single style number to scrape')
    input_group.add_argument('--styles', type=str,
                            help='Comma-separated list of style numbers')
    input_group.add_argument('--file', type=str,
                            help='File containing style numbers (one per line)')
    
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay in seconds between requests (default: 1.0)')
    parser.add_argument('--mode', type=str, default='append',
                       choices=['append', 'overwrite', 'scratch'],
                       help='Write mode: append (default, skip existing), overwrite (replace existing), scratch (delete all first)')
    parser.add_argument('--force', action='store_true',
                       help='Force recreation of catalog master list (use with --initialize)')
    
    args = parser.parse_args()
    
    # Handle initialization
    if args.initialize:
        success = initialize_catalog_master_list(force=args.force)
        sys.exit(0 if success else 1)
    
    # Handle all other modes
    elif args.all:
        scrape_all(args.delay, args.mode)
    
    elif args.style:
        scrape_batch([args.style], args.delay, args.mode)
    
    elif args.styles:
        style_numbers = [s.strip() for s in args.styles.split(',')]
        scrape_batch(style_numbers, args.delay, args.mode)
    
    elif args.file:
        scrape_from_file(args.file, args.delay, args.mode)


if __name__ == "__main__":
    main()
