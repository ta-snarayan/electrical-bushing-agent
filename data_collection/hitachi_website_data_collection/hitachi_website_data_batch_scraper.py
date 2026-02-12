"""
Hitachi Website Batch Bushing Data Scraper

This script allows scraping multiple bushing indices in one run, with configurable
delay between requests to be respectful to the server. Features robust error handling
and logging for large-scale automation (supports 1 to 50,000+ indices).

Write Modes:
    --mode append (default): Skip indices that already exist in CSV and raw data folder
    --mode overwrite: Overwrite existing data file-by-file (incremental updates)
    --mode scratch: Delete all existing data and start fresh

Usage:
    python hitachi_website_data_batch_scraper.py --start 1 --end 10
    python hitachi_website_data_batch_scraper.py --start 1 --end 50000 --delay 0.5
    python hitachi_website_data_batch_scraper.py --start 1 --end 100 --delay 0.5 --mode append
    python hitachi_website_data_batch_scraper.py --indices 42131,42246,50000 --mode overwrite
    python hitachi_website_data_batch_scraper.py --file indices.txt --mode scratch

Author: Data Collection System
Date: February 10, 2026
Version: 3.0 - Added write modes (append/overwrite/scratch)
"""

import argparse
import time
import sys
import os
import shutil
import pandas as pd
from pathlib import Path
from hitachi_website_data_scraper import (
    scrape_bushing_data, 
    save_to_csv, 
    logger, 
    ERROR_LOG_CSV, 
    OUTPUT_CSV, 
    RAW_DATA_DIR,
    get_error_log_indices,
    delete_raw_html
)


def check_index_exists(index: int) -> bool:
    """
    Check if an index already exists in CSV or raw HTML files.
    Does NOT check error log (error log is checked separately).
    
    Args:
        index: The bushing index to check
        
    Returns:
        True if the index exists in CSV or HTML file; False otherwise
    """
    # Check if raw HTML file exists
    html_file = Path(RAW_DATA_DIR) / f"Hitachi_website_bushing_{index}.html"
    html_exists = html_file.exists()
    
    # Check if index exists in CSV
    csv_exists = False
    if os.path.exists(OUTPUT_CSV):
        try:
            df = pd.read_csv(OUTPUT_CSV)
            csv_exists = index in df['Website Index'].values
        except Exception as e:
            logger.warning(f"Error checking CSV for index {index}: {e}")
    
    return html_exists or csv_exists


def clean_scratch_mode():
    """
    Clean all existing data for scratch mode (fresh start).
    Deletes the CSV file, error log, and all raw HTML files.
    """
    logger.info("SCRATCH MODE: Cleaning all existing data...")
    
    # Delete CSV file
    if os.path.exists(OUTPUT_CSV):
        os.remove(OUTPUT_CSV)
        logger.info(f"Deleted {OUTPUT_CSV}")
    
    # Delete error log
    if os.path.exists(ERROR_LOG_CSV):
        os.remove(ERROR_LOG_CSV)
        logger.info(f"Deleted {ERROR_LOG_CSV}")
    
    # Delete all raw HTML files
    raw_data_path = Path(RAW_DATA_DIR)
    if raw_data_path.exists():
        shutil.rmtree(raw_data_path)
        logger.info(f"Deleted {RAW_DATA_DIR}/ directory")
    
    # Recreate the raw data directory
    raw_data_path.mkdir(parents=True, exist_ok=True)
    logger.info("Clean completed - starting fresh")


def scrape_range(start: int, end: int, delay: float = 1.0, mode: str = 'append'):
    """
    Scrape a range of indices.
    
    Args:
        start: Starting index (inclusive)
        end: Ending index (inclusive)
        delay: Delay in seconds between requests (default: 1.0)
        mode: Write mode - 'append' (skip existing), 'overwrite' (replace existing), 'scratch' (delete all first)
    """
    # Handle scratch mode
    if mode == 'scratch':
        clean_scratch_mode()
    
    # Load error log indices once at the start
    error_log_indices = get_error_log_indices()
    logger.info(f"Loaded {len(error_log_indices)} indices from error log")
    
    total = end - start + 1
    success_count = 0
    failure_count = 0
    skipped_count = 0
    
    logger.info(f"Starting batch scrape for indices {start} to {end} ({total} total) - Mode: {mode.upper()}")
    
    for i in range(start, end + 1):
        # Check if this index is in the error log
        if i in error_log_indices:
            skipped_count += 1
            # Delete HTML file if it exists
            delete_raw_html(i)
            logger.info(f"Skipping index {i} (in error log, HTML deleted if existed) ({i - start + 1}/{total})")
            print(f"⊘ Index {i}: Skipped (in error log)")
            continue
        
        # Check if we should skip this index (append mode only)
        if mode == 'append' and check_index_exists(i):
            skipped_count += 1
            logger.info(f"Skipping index {i} (already exists) ({i - start + 1}/{total})")
            print(f"⊘ Index {i}: Skipped (already processed)")
            continue
        
        action = "Overwriting" if mode == 'overwrite' and check_index_exists(i) else "Processing"
        logger.info(f"{action} index {i} ({i - start + 1}/{total})")
        
        bushing_data = scrape_bushing_data(i)
        
        if bushing_data:
            if save_to_csv(bushing_data, mode=mode):
                success_count += 1
                prefix = "↻" if mode == 'overwrite' and check_index_exists(i) else "✓"
                print(f"{prefix} Index {i}: {bushing_data['Original Bushing Information - Original Bushing Manufacturer'] or '(empty)'} | "
                      f"{bushing_data['Original Bushing Information - Catalog Number']} | "
                      f"{bushing_data['Replacement Information - ABB Style Number']}")
            else:
                failure_count += 1
                print(f"✗ Index {i}: Failed to save to CSV")
        else:
            failure_count += 1
            print(f"✗ Index {i}: Failed to scrape (logged to error log)")
        
        # Delay between requests (except for the last one)
        if i < end:
            time.sleep(delay)
    
    logger.info(f"Batch scrape completed: {success_count} successful, {failure_count} failed, {skipped_count} skipped")
    print(f"\n{'='*70}")
    print(f"Batch Scraping Complete - Mode: {mode.upper()}")
    print(f"{'='*70}")
    print(f"Index Range: {start} to {end}")
    print(f"Total Indices: {total}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    if mode == 'append':
        print(f"Skipped (already exist): {skipped_count}")
    print(f"Success Rate: {(success_count/(total-skipped_count)*100 if total-skipped_count > 0 else 0):.1f}%")
    
    # Check if error log exists and inform user
    if failure_count > 0 and os.path.exists(ERROR_LOG_CSV):
        print(f"\n⚠  Errors logged to: {ERROR_LOG_CSV}")
        print(f"   Review this file for details on {failure_count} failed indices")
    
    if success_count > 0:
        print(f"\n✓ Data saved to: {OUTPUT_CSV}")
        print(f"✓ Raw HTML saved to: {RAW_DATA_DIR}/")


def scrape_list(indices: list, delay: float = 1.0, mode: str = 'append'):
    """
    Scrape a list of specific indices.
    
    Args:
        indices: List of index numbers to scrape
        delay: Delay in seconds between requests (default: 1.0)
        mode: Write mode - 'append' (skip existing), 'overwrite' (replace existing), 'scratch' (delete all first)
    """
    # Handle scratch mode
    if mode == 'scratch':
        clean_scratch_mode()
    
    # Load error log indices once at the start
    error_log_indices = get_error_log_indices()
    logger.info(f"Loaded {len(error_log_indices)} indices from error log")
    
    total = len(indices)
    success_count = 0
    failure_count = 0
    skipped_count = 0
    
    logger.info(f"Starting batch scrape for {total} indices - Mode: {mode.upper()}")
    
    for idx, i in enumerate(indices, 1):
        # Check if this index is in the error log
        if i in error_log_indices:
            skipped_count += 1
            # Delete HTML file if it exists
            delete_raw_html(i)
            logger.info(f"Skipping index {i} (in error log, HTML deleted if existed) ({idx}/{total})")
            print(f"⊘ Index {i}: Skipped (in error log)")
            continue
        
        # Check if we should skip this index (append mode only)
        if mode == 'append' and check_index_exists(i):
            skipped_count += 1
            logger.info(f"Skipping index {i} (already exists) ({idx}/{total})")
            print(f"⊘ Index {i}: Skipped (already processed)")
            continue
        
        action = "Overwriting" if mode == 'overwrite' and check_index_exists(i) else "Processing"
        logger.info(f"{action} index {i} ({idx}/{total})")
        
        bushing_data = scrape_bushing_data(i)
        
        if bushing_data:
            if save_to_csv(bushing_data, mode=mode):
                success_count += 1
                prefix = "↻" if mode == 'overwrite' and check_index_exists(i) else "✓"
                print(f"{prefix} Index {i}: {bushing_data['Original Bushing Information - Original Bushing Manufacturer'] or '(empty)'} | "
                      f"{bushing_data['Original Bushing Information - Catalog Number']} | "
                      f"{bushing_data['Replacement Information - ABB Style Number']}")
            else:
                failure_count += 1
                print(f"✗ Index {i}: Failed to save to CSV")
        else:
            failure_count += 1
            print(f"✗ Index {i}: Failed to scrape (logged to error log)")
        
        # Delay between requests (except for the last one)
        if idx < total:
            time.sleep(delay)
    
    logger.info(f"Batch scrape completed: {success_count} successful, {failure_count} failed, {skipped_count} skipped")
    print(f"\n{'='*70}")
    print(f"Batch Scraping Complete - Mode: {mode.upper()}")
    print(f"{'='*70}")
    print(f"Total Indices: {total}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    if mode == 'append':
        print(f"Skipped (already exist): {skipped_count}")
    print(f"Success Rate: {(success_count/(total-skipped_count)*100 if total-skipped_count > 0 else 0):.1f}%")
    
    # Check if error log exists and inform user
    if failure_count > 0 and os.path.exists(ERROR_LOG_CSV):
        print(f"\n⚠  Errors logged to: {ERROR_LOG_CSV}")
        print(f"   Review this file for details on {failure_count} failed indices")
    
    if success_count > 0:
        print(f"\n✓ Data saved to: {OUTPUT_CSV}")
        print(f"✓ Raw HTML saved to: {RAW_DATA_DIR}/")


def scrape_from_file(filepath: str, delay: float = 1.0, mode: str = 'append'):
    """
    Scrape indices listed in a text file (one index per line).
    
    Args:
        filepath: Path to file containing indices
        delay: Delay in seconds between requests (default: 1.0)
        mode: Write mode - 'append' (skip existing), 'overwrite' (replace existing), 'scratch' (delete all first)
    """
    try:
        with open(filepath, 'r') as f:
            indices = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    try:
                        indices.append(int(line))
                    except ValueError:
                        logger.warning(f"Skipping invalid index in file: {line}")
        
        if not indices:
            logger.error(f"No valid indices found in file: {filepath}")
            sys.exit(1)
        
        scrape_list(indices, delay, mode)
        
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Batch scraper for Hitachi Energy bushing data',
        epilog='Examples:\n'
               '  python hitachi_website_data_batch_scraper.py --start 1 --end 10\n'
               '  python hitachi_website_data_batch_scraper.py --start 1 --end 100 --mode append\n'
               '  python hitachi_website_data_batch_scraper.py --indices 42131,42246 --mode overwrite\n'
               '  python hitachi_website_data_batch_scraper.py --file indices.txt --mode scratch\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Create mutually exclusive group for input methods
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--start', type=int, help='Starting index (use with --end)')
    input_group.add_argument('--indices', type=str, help='Comma-separated list of indices')
    input_group.add_argument('--file', type=str, help='File containing indices (one per line)')
    
    parser.add_argument('--end', type=int, help='Ending index (use with --start)')
    parser.add_argument('--delay', type=float, default=1.0, 
                       help='Delay in seconds between requests (default: 1.0)')
    parser.add_argument('--mode', type=str, default='append', 
                       choices=['append', 'overwrite', 'scratch'],
                       help='Write mode: append (default, skip existing), overwrite (replace existing), scratch (delete all first)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.start is not None:
        if args.end is None:
            parser.error('--start requires --end')
        if args.start > args.end:
            parser.error('--start must be less than or equal to --end')
        scrape_range(args.start, args.end, args.delay, args.mode)
    
    elif args.indices:
        try:
            indices = [int(x.strip()) for x in args.indices.split(',')]
            scrape_list(indices, args.delay, args.mode)
        except ValueError:
            parser.error('--indices must be comma-separated integers')
    
    elif args.file:
        scrape_from_file(args.file, args.delay, args.mode)


if __name__ == "__main__":
    main()
