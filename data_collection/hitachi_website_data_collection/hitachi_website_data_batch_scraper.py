"""
Hitachi Website Batch Bushing Data Scraper

This script allows scraping multiple bushing indices in one run, with configurable
delay between requests to be respectful to the server. Features robust error handling
and logging for large-scale automation (supports 1 to 50,000+ indices).

Usage:
    python hitachi_website_data_batch_scraper.py --start 1 --end 10
    python hitachi_website_data_batch_scraper.py --start 1 --end 50000 --delay 0.5
    python hitachi_website_data_batch_scraper.py --indices 42131,42246,50000
    python hitachi_website_data_batch_scraper.py --file indices.txt

Author: Data Collection System
Date: February 10, 2026
Version: 2.0 - Reorganized for multi-website support
"""

import argparse
import time
import sys
import os
from hitachi_website_data_scraper import scrape_bushing_data, save_to_csv, logger, ERROR_LOG_CSV, OUTPUT_CSV, RAW_DATA_DIR


def scrape_range(start: int, end: int, delay: float = 1.0):
    """
    Scrape a range of indices.
    
    Args:
        start: Starting index (inclusive)
        end: Ending index (inclusive)
        delay: Delay in seconds between requests (default: 1.0)
    """
    total = end - start + 1
    success_count = 0
    failure_count = 0
    
    logger.info(f"Starting batch scrape for indices {start} to {end} ({total} total)")
    
    for i in range(start, end + 1):
        logger.info(f"Processing index {i} ({i - start + 1}/{total})")
        
        bushing_data = scrape_bushing_data(i)
        
        if bushing_data:
            if save_to_csv(bushing_data):
                success_count += 1
                print(f"✓ Index {i}: {bushing_data['Original Bushing Information - Original Bushing Manufacturer'] or '(empty)'} | "
                      f"{bushing_data['Original Bushing Information - Catalog Number']} | "
                      f"{bushing_data['Replacement Information - ABB Style Number']}")
            else:
                failure_count += 1
                print(f"✗ Index {i}: Failed to save to CSV")
        else:
            failure_count += 1
            print(f"✗ Index {i}: Failed to scrape")
        
        # Delay between requests (except for the last one)
        if i < end:
            time.sleep(delay)
    
    logger.info(f"Batch scrape completed: {success_count} successful, {failure_count} failed")
    print(f"\n{'='*70}")
    print(f"Batch Scraping Complete")
    print(f"{'='*70}")
    print(f"Index Range: {start} to {end}")
    print(f"Total Processed: {total}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    print(f"Success Rate: {(success_count/total)*100:.1f}%")
    
    # Check if error log exists and inform user
    if failure_count > 0 and os.path.exists(ERROR_LOG_CSV):
        print(f"\n⚠  Errors logged to: {ERROR_LOG_CSV}")
        print(f"   Review this file for details on {failure_count} failed indices")
    
    if success_count > 0:
        print(f"\n✓ Data saved to: {OUTPUT_CSV}")
        print(f"✓ Raw HTML saved to: {RAW_DATA_DIR}/")


def scrape_list(indices: list, delay: float = 1.0):
    """
    Scrape a list of specific indices.
    
    Args:
        indices: List of index numbers to scrape
        delay: Delay in seconds between requests (default: 1.0)
    """
    total = len(indices)
    success_count = 0
    failure_count = 0
    
    logger.info(f"Starting batch scrape for {total} indices")
    
    for idx, i in enumerate(indices, 1):
        logger.info(f"Processing index {i} ({idx}/{total})")
        
        bushing_data = scrape_bushing_data(i)
        
        if bushing_data:
            if save_to_csv(bushing_data):
                success_count += 1
                print(f"✓ Index {i}: {bushing_data['Original Bushing Information - Original Bushing Manufacturer'] or '(empty)'} | "
                      f"{bushing_data['Original Bushing Information - Catalog Number']} | "
                      f"{bushing_data['Replacement Information - ABB Style Number']}")
            else:
                failure_count += 1
                print(f"✗ Index {i}: Failed to save to CSV")
        else:
            failure_count += 1
            print(f"✗ Index {i}: Failed to scrape")
        
        # Delay between requests (except for the last one)
        if idx < total:
            time.sleep(delay)
    
    logger.info(f"Batch scrape completed: {success_count} successful, {failure_count} failed")
    print(f"\n{'='*70}")
    print(f"Batch Scraping Complete")
    print(f"{'='*70}")
    print(f"Total Processed: {total}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    print(f"Success Rate: {(success_count/total)*100:.1f}%")
    
    # Check if error log exists and inform user
    if failure_count > 0 and os.path.exists(ERROR_LOG_CSV):
        print(f"\n⚠  Errors logged to: {ERROR_LOG_CSV}")
        print(f"   Review this file for details on {failure_count} failed indices")
    
    if success_count > 0:
        print(f"\n✓ Data saved to: {OUTPUT_CSV}")
        print(f"✓ Raw HTML saved to: {RAW_DATA_DIR}/")


def scrape_from_file(filepath: str, delay: float = 1.0):
    """
    Scrape indices listed in a text file (one index per line).
    
    Args:
        filepath: Path to file containing indices
        delay: Delay in seconds between requests (default: 1.0)
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
        
        scrape_list(indices, delay)
        
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
               '  python hitachi_website_data_batch_scraper.py --indices 42131,42246,50000\n'
               '  python hitachi_website_data_batch_scraper.py --file indices.txt\n',
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
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.start is not None:
        if args.end is None:
            parser.error('--start requires --end')
        if args.start > args.end:
            parser.error('--start must be less than or equal to --end')
        scrape_range(args.start, args.end, args.delay)
    
    elif args.indices:
        try:
            indices = [int(x.strip()) for x in args.indices.split(',')]
            scrape_list(indices, args.delay)
        except ValueError:
            parser.error('--indices must be comma-separated integers')
    
    elif args.file:
        scrape_from_file(args.file, args.delay)


if __name__ == "__main__":
    main()
