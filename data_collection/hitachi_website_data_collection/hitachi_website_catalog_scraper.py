"""
Hitachi Energy Bushing Catalog Data Scraper

This module scrapes detailed electrical bushing catalog specifications from the 
Hitachi Energy website and saves them to a CSV file. This is Phase 2 of the data 
collection system - it enriches ABB style numbers from the cross-reference master 
list with complete technical specifications.

Author: Data Collection System
Date: February 13, 2026
Version: 1.0 - Initial catalog scraping implementation
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sys
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Set
from datetime import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://bushing.hitachienergy.com/Scripts/BushingLookupBU.asp"
CROSS_REFERENCE_CSV = "hitachi_website_bushing_master_list.csv"
OUTPUT_CSV = "hitachi_website_bushing_catalog_master_list.csv"
ERROR_LOG_CSV = "hitachi_website_catalog_scraping_error_log.csv"
RAW_DATA_DIR = "hitachi_website_data_raw/catalog_data"

# All 53 columns from sample_data_2.csv
COLUMNS = [
    "Style Number",
    "Alternate Style Number (usually other color)",
    "Catalog Number",
    "Delivery Ex-Works",
    "Delivery Last Update",
    "List Price US$",
    "Insulator Type",
    "Color",
    "Outline Drawing",
    "Download Drawing",
    "Apparatus",
    "Standard",
    "Bushing Type",
    "Oil Indication",
    "Application",
    "Mounting Position",
    "Connection Type",
    "Current Version",
    "Voltage Class",
    "kV BIL",
    "Max kV L-G",
    "Cantilever Design Test Rating Upper Value",
    "Cantilever Design Test Rating Lower Value",
    "Approximate Capacitance C1",
    "Approximate Capacitance C2",
    "Current Rating Draw Lead",
    "Bottom Connected",
    "Oil Circuit Breaker",
    "Lower End Length (L)",
    "C.T. Pocket Transformer",
    "C.T. Pocket Oil Circuit Breaker",
    "Exposable Length Transformer (EL)",
    "Exposable Length Oil Circuit Breaker (EL)",
    'Max. Dia. From 1" below Flange to Lower End of Bushing (D)',
    "Upper End Length (B)",
    "Minimum Creep",
    "Arcing Distance",
    "Lowest High Voltage (LHV)",
    "Cable Height/Pin Height for AB Bushings (CH)",
    "Maximum Altitude",
    "Approximate Weight",
    "Top End Terminal - Thread Dia and Class or number of Pads and Holes Per Pad",
    "Top End Terminal - Length and Type or Dia, and Type of Holes",
    "Top End Terminal - Thread Plating",
    "Top End Terminal - Top Terminal Comments",
    "Bottom End Terminal - Terminal Type",
    "Bottom End Terminal - Min Outside Diameter",
    "Bottom End Terminal - Bottom Terminal Comments",
    "Max Inside Diameter (P)",
    "Min Outside Diameter (Q)",
    "Number of Holes",
    "Hole/Slot Size",
    "Bolt Circle Diameter",
    "Epoxy Coated Shield and Terminal Kit",
    "Flange Mounting Comments",
    "Special Features"
]


def extract_unique_abb_style_numbers() -> Set[str]:
    """
    Extract unique ABB style numbers from the cross-reference master list.
    Filters for ABB bushings from both replacement and original manufacturer columns.
    
    Returns:
        Set of unique ABB style numbers (excludes empty values)
    """
    try:
        if not os.path.exists(CROSS_REFERENCE_CSV):
            logger.error(f"Cross-reference file not found: {CROSS_REFERENCE_CSV}")
            return set()
        
        df = pd.read_csv(CROSS_REFERENCE_CSV)
        style_numbers = set()
        
        # Extract from Replacement Information where manufacturer is ABB
        replacement_col = "Replacement Information - Replacement Bushing Manufacturer"
        style_col = "Replacement Information - ABB Style Number"
        
        if replacement_col in df.columns and style_col in df.columns:
            abb_replacements = df[df[replacement_col] == "ABB"]
            replacement_styles = abb_replacements[style_col].dropna()
            replacement_styles = replacement_styles[replacement_styles != ""]
            style_numbers.update(replacement_styles.values)
        
        # Also check Original Bushing Information where manufacturer is ABB
        original_mfr_col = "Original Bushing Information - Original Bushing Manufacturer"
        original_cat_col = "Original Bushing Information - Catalog Number"
        
        if original_mfr_col in df.columns and original_cat_col in df.columns:
            abb_originals = df[df[original_mfr_col] == "ABB"]
            original_styles = abb_originals[original_cat_col].dropna()
            original_styles = original_styles[original_styles != ""]
            style_numbers.update(original_styles.values)
        
        logger.info(f"Extracted {len(style_numbers)} unique ABB style numbers")
        return style_numbers
        
    except Exception as e:
        logger.error(f"Error extracting ABB style numbers: {e}")
        return set()


def log_error_to_csv(style_number: str, error_message: str) -> bool:
    """
    Log scraping errors to a CSV file for analysis.
    
    Args:
        style_number: The bushing style number that failed
        error_message: Descriptive error message
        
    Returns:
        True if logged successfully, False otherwise
    """
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        error_data = {
            'Timestamp': timestamp,
            'Style_Number': style_number,
            'Error_Message': error_message
        }
        
        # Create DataFrame
        df = pd.DataFrame([error_data])
        
        # Append to existing file or create new one
        try:
            existing_df = pd.read_csv(ERROR_LOG_CSV)
            # Check if this style number already exists in error log
            if style_number not in existing_df['Style_Number'].values:
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                combined_df.to_csv(ERROR_LOG_CSV, index=False)
                logger.info(f"Logged error for style {style_number}: {error_message}")
            else:
                logger.debug(f"Style {style_number} already in error log")
        except FileNotFoundError:
            df.to_csv(ERROR_LOG_CSV, index=False)
            logger.info(f"Created error log and logged style {style_number}: {error_message}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to log error to CSV: {e}")
        return False


def save_raw_html(html_content: str, style_number: str, directory: str = RAW_DATA_DIR) -> bool:
    """
    Save raw HTML response to file.
    
    Args:
        html_content: Raw HTML content from the webpage
        style_number: The bushing style number
        directory: Directory to save the file (default: RAW_DATA_DIR)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Create filename - sanitize style number for filesystem
        safe_style = style_number.replace("/", "_").replace("\\", "_")
        filename = f"Hitachi_website_bushing_{safe_style}.html"
        filepath = os.path.join(directory, filename)
        
        # Save HTML content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Saved raw HTML to {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving raw HTML for style {style_number}: {e}")
        return False


def delete_raw_html(style_number: str, directory: str = RAW_DATA_DIR) -> bool:
    """
    Delete raw HTML file for a given style number.
    Used to clean up files for style numbers with errors.
    
    Args:
        style_number: The bushing style number
        directory: Directory containing the file (default: RAW_DATA_DIR)
        
    Returns:
        True if successful or file doesn't exist, False on error
    """
    try:
        safe_style = style_number.replace("/", "_").replace("\\", "_")
        filename = f"Hitachi_website_bushing_{safe_style}.html"
        filepath = os.path.join(directory, filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Deleted raw HTML file: {filepath}")
            return True
        else:
            logger.debug(f"HTML file not found (already deleted): {filepath}")
            return True
        
    except Exception as e:
        logger.error(f"Error deleting raw HTML for style {style_number}: {e}")
        return False


def get_error_log_style_numbers() -> set:
    """
    Load all style numbers from the error log CSV.
    
    Returns:
        Set of style numbers that have errors
    """
    try:
        if os.path.exists(ERROR_LOG_CSV):
            df = pd.read_csv(ERROR_LOG_CSV)
            return set(df['Style_Number'].values)
        return set()
    except Exception as e:
        logger.warning(f"Error reading error log: {e}")
        return set()


def scrape_catalog_data(style_number: str) -> Optional[Dict[str, str]]:
    """
    Scrape catalog data for a given ABB style number from the Hitachi Energy website.
    Enhanced with comprehensive error handling and logging for large-scale automation.
    Only saves HTML files when valid data is found.
    
    Args:
        style_number: The ABB style number to scrape (e.g., "138W0800XA")
        
    Returns:
        Dictionary containing scraped catalog data or None if scraping fails
    """
    url = f"{BASE_URL}?StyleNumber={style_number}&Language=English&Units=English"
    logger.info(f"Scraping catalog data for style {style_number} from {url}")
    
    # Headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://bushing.hitachienergy.com/'
    }
    
    try:
        # Send GET request with browser headers
        response = requests.get(url, headers=headers, timeout=30)
        
        # Check for HTTP errors
        if response.status_code == 404:
            log_error_to_csv(style_number, 'Page not found (HTTP 404)')
            logger.warning(f"Style {style_number} not found (404)")
            delete_raw_html(style_number)
            return None
        elif response.status_code == 403:
            log_error_to_csv(style_number, 'Access forbidden (HTTP 403)')
            logger.warning(f"Access forbidden for style {style_number} (403)")
            delete_raw_html(style_number)
            return None
        
        response.raise_for_status()
        
        # Check if response has content
        if not response.text or len(response.text) < 100:
            log_error_to_csv(style_number, 'Empty or too short response from server')
            logger.warning(f"Empty or invalid response for style {style_number}")
            delete_raw_html(style_number)
            return None
        
        # Check for "No bushing found" message
        if "No bushing found by that style number" in response.text:
            log_error_to_csv(style_number, 'No bushing found by that style number')
            logger.warning(f"No bushing found for style {style_number}")
            delete_raw_html(style_number)
            return None
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract catalog information
        catalog_data = parse_catalog_info(soup, style_number)
        
        if catalog_data:
            # Validate that we got at least the style number confirmed
            if catalog_data.get("Style Number"):
                # Save HTML for valid data
                if not save_raw_html(response.text, style_number):
                    logger.warning(f"Failed to save raw HTML for style {style_number}, but continuing...")
                logger.info(f"Successfully scraped catalog data for style {style_number}")
                return catalog_data
            else:
                log_error_to_csv(style_number, 'Style number field empty - no valid data extracted')
                logger.warning(f"No valid data found for style {style_number}")
                delete_raw_html(style_number)
                return None
        else:
            log_error_to_csv(style_number, 'HTML parser returned None - could not parse page')
            logger.warning(f"Parser failed for style {style_number}")
            delete_raw_html(style_number)
            return None
    
    except requests.exceptions.Timeout:
        log_error_to_csv(style_number, 'Request timeout after 30 seconds')
        logger.error(f"Timeout fetching data for style {style_number}")
        delete_raw_html(style_number)
        return None
    
    except requests.exceptions.ConnectionError as e:
        log_error_to_csv(style_number, f'Network connection error: {str(e)[:100]}')
        logger.error(f"Connection error for style {style_number}: {e}")
        delete_raw_html(style_number)
        return None
    
    except requests.exceptions.HTTPError as e:
        log_error_to_csv(style_number, f'HTTP error {e.response.status_code}: {str(e)[:100]}')
        logger.error(f"HTTP error for style {style_number}: {e}")
        delete_raw_html(style_number)
        return None
    
    except requests.exceptions.RequestException as e:
        log_error_to_csv(style_number, f'Request exception: {str(e)[:100]}')
        logger.error(f"Request exception for style {style_number}: {e}")
        delete_raw_html(style_number)
        return None
    
    except Exception as e:
        log_error_to_csv(style_number, f'Unexpected error: {str(e)[:100]}')
        logger.error(f"Unexpected error for style {style_number}: {e}")
        delete_raw_html(style_number)
        return None


def extract_table_value(soup: BeautifulSoup, label: str) -> str:
    """
    Extract value from HTML table by searching for label in table cells.
    
    Args:
        soup: BeautifulSoup object containing the parsed HTML
        label: Label text to search for (e.g., "Style Number:")
        
    Returns:
        Extracted value or empty string
    """
    try:
        # Find all table rows
        all_rows = soup.find_all('tr')
        
        for row in all_rows:
            cells = row.find_all(['td', 'th'])
            
            # Check each cell in this row for the label
            for i, cell in enumerate(cells):
                # Replace BR tags with spaces BEFORE getting text
                for br in cell.find_all('br'):
                    br.replace_with(' ')
                
                # Get text and normalize whitespace
                cell_text = cell.get_text(separator=' ', strip=True)
                # Normalize whitespace (multiple spaces to single space)
                cell_text = ' '.join(cell_text.split())
                
                # Check if this cell contains our label (exact or partial match)
                # Try exact match first
                if label == cell_text or (label in cell_text and len(label) > len(cell_text) * 0.7):
                    # Value should be in the next cell in the same row
                    if i + 1 < len(cells):
                        value_cell = cells[i + 1]
                        # Process BR tags in value cell too
                        for br in value_cell.find_all('br'):
                            br.replace_with(' ')
                        value = value_cell.get_text(separator=' ', strip=True)
                        # Clean up the value
                        value = ' '.join(value.split())  # Normalize whitespace
                        return value
                
                # Sometimes value is in same cell after label (with colon)
                if label in cell_text and ':' in cell_text:
                    parts = cell_text.split(':', 1)
                    if len(parts) == 2 and label in parts[0]:
                        value = parts[1].strip()
                        return value
        
        return ""
        
    except Exception as e:
        logger.debug(f"Error extracting table value for '{label}': {e}")
        return ""


def parse_catalog_info(soup: BeautifulSoup, style_number: str) -> Optional[Dict[str, str]]:
    """
    Parse catalog information from the HTML soup.
    Extracts all 53 fields from the bushing specification page.
    
    Args:
        soup: BeautifulSoup object containing the parsed HTML
        style_number: The bushing style number being scraped
        
    Returns:
        Dictionary with extracted catalog data or None if parsing fails
    """
    try:
        # Initialize data dictionary with all columns
        data = {col: "" for col in COLUMNS}
        
        # Set the style number we're looking for
        data["Style Number"] = style_number
        
        # Extract basic information
        data["Alternate Style Number (usually other color)"] = extract_table_value(soup, "Alternate Style Number")
        data["Catalog Number"] = extract_table_value(soup, "Catalog Number:")
        data["Delivery Ex-Works"] = extract_table_value(soup, "Delivery Ex-Works:")
        data["Delivery Last Update"] = extract_table_value(soup, "Delivery Last Update:")
        data["List Price US$"] = extract_table_value(soup, "List Price US$:")
        
        # Extract insulator information
        data["Insulator Type"] = extract_table_value(soup, "Insulator Type:")
        data["Color"] = extract_table_value(soup, "Color:")
        data["Outline Drawing"] = extract_table_value(soup, "Outline Drawing:")
        data["Download Drawing"] = extract_table_value(soup, "Download Drawing:")
        
        # Extract specifications
        data["Apparatus"] = extract_table_value(soup, "Apparatus:")
        data["Standard"] = extract_table_value(soup, "Standard:")
        data["Bushing Type"] = extract_table_value(soup, "Bushing Type:")
        data["Oil Indication"] = extract_table_value(soup, "Oil Indication:")
        data["Application"] = extract_table_value(soup, "Application:")
        data["Mounting Position"] = extract_table_value(soup, "Mounting Position:")
        data["Connection Type"] = extract_table_value(soup, "Connection Type:")
        data["Current Version"] = extract_table_value(soup, "Current Version:")
        
        # Extract electrical ratings
        data["Voltage Class"] = extract_table_value(soup, "Voltage Class")
        data["kV BIL"] = extract_table_value(soup, "kV BIL")
        data["Max kV L-G"] = extract_table_value(soup, "Max kV L-G")
        data["Cantilever Design Test Rating Upper Value"] = extract_table_value(soup, "Cantilever Design Test Rating Upper Value")
        
        # Try alternate label for lower value
        lower_value = extract_table_value(soup, "Lower Value")
        if not lower_value:
            lower_value = extract_table_value(soup, "Cantilever Design Test Rating Lower Value")
        data["Cantilever Design Test Rating Lower Value"] = lower_value
        
        # Extract capacitance and current
        c1 = extract_table_value(soup, "Approximate Capacitance C1")
        if not c1:
            c1 = extract_table_value(soup, "C1")
        data["Approximate Capacitance C1"] = c1
        
        c2 = extract_table_value(soup, "C2")
        if not c2:
            c2 = extract_table_value(soup, "Approximate Capacitance C2")
        data["Approximate Capacitance C2"] = c2
        
        data["Current Rating Draw Lead"] = extract_table_value(soup, "Current Rating Draw Lead")
        data["Bottom Connected"] = extract_table_value(soup, "Bottom Connected")
        data["Oil Circuit Breaker"] = extract_table_value(soup, "Oil Circuit Breaker")
        
        # Extract dimensions
        data["Lower End Length (L)"] = extract_table_value(soup, "Lower End Length (L)")
        data["C.T. Pocket Transformer"] = extract_table_value(soup, "C.T. Pocket Transformer")
        data["C.T. Pocket Oil Circuit Breaker"] = extract_table_value(soup, "C.T. Pocket Oil Circuit Breaker")
        data["Exposable Length Transformer (EL)"] = extract_table_value(soup, "Exposable Length Transformer (EL)")
        data["Exposable Length Oil Circuit Breaker (EL)"] = extract_table_value(soup, "Exposable Length Oil Circuit Breaker (EL)")
        data['Max. Dia. From 1" below Flange to Lower End of Bushing (D)'] = extract_table_value(soup, 'Max. Dia. From 1" below Flange to Lower End of Bushing (D)')
        data["Upper End Length (B)"] = extract_table_value(soup, "Upper End Length (B)")
        data["Minimum Creep"] = extract_table_value(soup, "Minimum Creep")
        data["Arcing Distance"] = extract_table_value(soup, "Arcing Distance")
        data["Lowest High Voltage (LHV)"] = extract_table_value(soup, "Lowest High Voltage (LHV)")
        data["Cable Height/Pin Height for AB Bushings (CH)"] = extract_table_value(soup, "Cable Height/Pin Height for AB Bushings (CH)")
        data["Maximum Altitude"] = extract_table_value(soup, "Maximum Altitude")
        data["Approximate Weight"] = extract_table_value(soup, "Approximate Weight")
        
        # Extract terminal information
        data["Top End Terminal - Thread Dia and Class or number of Pads and Holes Per Pad"] = extract_table_value(soup, "Thread Dia and Class or number of Pads and Holes Per Pad")
        data["Top End Terminal - Length and Type or Dia, and Type of Holes"] = extract_table_value(soup, "Length and Type or Dia, and Type of Holes")
        data["Top End Terminal - Thread Plating"] = extract_table_value(soup, "Thread Plating")
        data["Top End Terminal - Top Terminal Comments"] = extract_table_value(soup, "Top Terminal Comments")
        
        data["Bottom End Terminal - Terminal Type"] = extract_table_value(soup, "Terminal Type")
        data["Bottom End Terminal - Min Outside Diameter"] = extract_table_value(soup, "Min Outside Diameter")
        data["Bottom End Terminal - Bottom Terminal Comments"] = extract_table_value(soup, "Bottom Terminal Comments")
        
        # Extract flange mounting information
        data["Max Inside Diameter (P)"] = extract_table_value(soup, "Max Inside Diameter (P)")
        data["Min Outside Diameter (Q)"] = extract_table_value(soup, "Min Outside Diameter (Q)")
        data["Number of Holes"] = extract_table_value(soup, "Number of Holes")
        data["Hole/Slot Size"] = extract_table_value(soup, "Hole/Slot Size")
        data["Bolt Circle Diameter"] = extract_table_value(soup, "Bolt Circle Diameter")
        data["Epoxy Coated Shield and Terminal Kit"] = extract_table_value(soup, "Epoxy Coated Shield and Terminal Kit")
        
        # Extract comments and special features
        # These are often in paragraph form, not tables
        page_text = soup.get_text()
        
        # Extract Flange Mounting Comments
        if "Flange Mounting Comments:" in page_text:
            start = page_text.find("Flange Mounting Comments:") + len("Flange Mounting Comments:")
            end = start + 200
            comment = page_text[start:end].strip()
            # Find end of comment (usually before "Special Features" or next section)
            for delimiter in ["Special Features:", "Top End Terminal", "\n\n"]:
                if delimiter in comment:
                    comment = comment[:comment.find(delimiter)].strip()
                    break
            data["Flange Mounting Comments"] = comment
        
        # Extract Special Features
        if "Special Features:" in page_text:
            start = page_text.find("Special Features:") + len("Special Features:")
            end = start + 200
            features = page_text[start:end].strip()
            # Clean up
            features = features.split('\n')[0].strip()
            data["Special Features"] = features
        
        return data
        
    except Exception as e:
        logger.error(f"Error in parse_catalog_info for style {style_number}: {e}")
        return None


def save_to_csv(data: Dict[str, str], filepath: str = OUTPUT_CSV, mode: str = 'append') -> bool:
    """
    Save catalog data to CSV file.
    
    Args:
        data: Dictionary containing catalog data
        filepath: Path to the CSV file
        mode: Write mode - 'append' (add new), 'overwrite' (replace existing row with same style number)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create DataFrame with single row
        df = pd.DataFrame([data])
        
        # Reorder columns to match specification
        df = df[COLUMNS]
        
        # Check if file exists
        try:
            existing_df = pd.read_csv(filepath)
            
            # In overwrite mode, remove any existing row with the same Style Number
            if mode == 'overwrite':
                style_to_check = data['Style Number']
                existing_df = existing_df[existing_df['Style Number'] != style_to_check]
            
            # Append new data
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.to_csv(filepath, index=False)
            logger.info(f"Appended data to {filepath}")
        except FileNotFoundError:
            # Create new file
            df.to_csv(filepath, index=False)
            logger.info(f"Created new file {filepath}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving to CSV: {e}")
        return False


def main():
    """
    Main execution function.
    """
    if len(sys.argv) < 2:
        print("Usage: python hitachi_website_catalog_scraper.py <style_number>")
        print("Example: python hitachi_website_catalog_scraper.py 138W0800XA")
        sys.exit(1)
    
    style_number = sys.argv[1].strip()
    
    # Scrape catalog data
    catalog_data = scrape_catalog_data(style_number)
    
    if catalog_data:
        # Save to CSV
        if save_to_csv(catalog_data):
            print(f"✓ Successfully scraped and saved catalog data for style {style_number}")
            print(f"  Catalog Number: {catalog_data['Catalog Number']}")
            print(f"  Voltage Class: {catalog_data['Voltage Class']}")
            print(f"  Current Rating: {catalog_data['Current Rating Draw Lead']}")
        else:
            print(f"✗ Failed to save data for style {style_number}")
            sys.exit(1)
    else:
        print(f"✗ Failed to scrape catalog data for style {style_number}")
        sys.exit(1)


if __name__ == "__main__":
    main()
