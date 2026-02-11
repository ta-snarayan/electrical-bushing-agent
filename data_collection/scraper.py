"""
Hitachi Energy Bushing Cross-Reference Data Scraper

This module scrapes electrical bushing cross-reference information from the 
Hitachi Energy website and saves it to a CSV file.

Author: Data Collection System
Date: February 10, 2026
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sys
import logging
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://bushing.hitachienergy.com/Scripts/BushingCrossReferenceBU.asp"
OUTPUT_CSV = "master_bushing_list_from_hitachi_website.csv"
COLUMNS = [
    "Website Index",
    "Original Bushing Information - Original Bushing Manufacturer",
    "Original Bushing Information - Catalog Number",
    "Replacement Information - Replacement Bushing Manufacturer",
    "Replacement Information - ABB Style Number"
]


def scrape_bushing_data(index: int) -> Optional[Dict[str, str]]:
    """
    Scrape bushing data for a given index from the Hitachi Energy website.
    
    Args:
        index: The bushing index number to scrape
        
    Returns:
        Dictionary containing scraped data or None if scraping fails
    """
    url = f"{BASE_URL}?INDEX={index}"
    logger.info(f"Scraping data for index {index} from {url}")
    
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
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract bushing information
        bushing_data = parse_bushing_info(soup, index)
        
        if bushing_data:
            logger.info(f"Successfully scraped data for index {index}")
            return bushing_data
        else:
            logger.warning(f"No valid data found for index {index}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data for index {index}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing data for index {index}: {e}")
        return None


def parse_bushing_info(soup: BeautifulSoup, index: int) -> Optional[Dict[str, str]]:
    """
    Parse bushing information from the HTML soup.
    
    Args:
        soup: BeautifulSoup object containing the parsed HTML
        index: The bushing index number
        
    Returns:
        Dictionary with extracted bushing data or None if parsing fails
    """
    try:
        # Get all text content
        page_text = soup.get_text()
        
        # Initialize data dictionary
        data = {
            "Website Index": str(index),
            "Original Bushing Information - Original Bushing Manufacturer": "",
            "Original Bushing Information - Catalog Number": "",
            "Replacement Information - Replacement Bushing Manufacturer": "ABB",
            "Replacement Information - ABB Style Number": ""
        }
        
        # Extract Original Bushing Manufacturer
        manufacturer = extract_field_value(
            page_text, 
            "Original Bushing Manufacturer:"
        )
        if manufacturer:
            data["Original Bushing Information - Original Bushing Manufacturer"] = manufacturer
        
        # Extract Original Catalog Number
        # Look for catalog number in the Original Bushing Information section
        catalog_number = extract_catalog_number(soup, page_text)
        if catalog_number:
            data["Original Bushing Information - Catalog Number"] = catalog_number
        
        # Extract ABB Style Number from Replacement Information section
        abb_style = extract_abb_style_number(soup, page_text)
        if abb_style:
            data["Replacement Information - ABB Style Number"] = abb_style
        
        # Validate that we got essential data
        if not data["Original Bushing Information - Original Bushing Manufacturer"]:
            logger.warning(f"Missing Original Bushing Manufacturer for index {index}")
        
        if not data["Original Bushing Information - Catalog Number"]:
            logger.warning(f"Missing Catalog Number for index {index}")
        
        if not data["Replacement Information - ABB Style Number"]:
            logger.warning(f"Missing ABB Style Number for index {index}")
        
        return data
        
    except Exception as e:
        logger.error(f"Error in parse_bushing_info: {e}")
        return None


def extract_field_value(text: str, label: str) -> str:
    """
    Extract value following a label in the text.
    
    Args:
        text: Text content to search
        label: Label to find (e.g., "Original Bushing Manufacturer:")
        
    Returns:
        Extracted value or empty string
    """
    try:
        if label not in text:
            return ""
        
        # Find the label position
        start_pos = text.find(label) + len(label)
        # Extract text after label (look at next 300 chars to find next field)
        remaining_text = text[start_pos:start_pos+300]
        
        # Common field labels that indicate the next field
        next_field_indicators = [
            'Mounting Position:', 'Catalog Number:', 'Voltage Class', 
            'BIL (kV):', 'Application', 'Current Rating', 'ABB Style Number:'
        ]
        
        # Find the position of the earliest next field indicator
        next_field_pos = len(remaining_text)
        for indicator in next_field_indicators:
            pos = remaining_text.find(indicator)
            if pos != -1 and pos < next_field_pos:
                next_field_pos = pos
        
        # Extract the value between the label and the next field
        value = remaining_text[:next_field_pos].strip()
        
        # Clean up the value - remove newlines and extra spaces
        value = ' '.join(value.split())
        
        return value
        
    except Exception as e:
        logger.error(f"Error extracting field value for '{label}': {e}")
        return ""


def extract_catalog_number(soup: BeautifulSoup, text: str) -> str:
    """
    Extract the original catalog number from the page.
    
    Args:
        soup: BeautifulSoup object
        text: Page text content
        
    Returns:
        Catalog number or empty string
    """
    try:
        # Look for "Catalog Number:" in the Original Bushing Information section
        # We need to find it before "Replacement Information" section
        
        original_section_marker = "Original Bushing Information"
        replacement_section_marker = "Replacement Information"
        
        if original_section_marker in text and replacement_section_marker in text:
            # Extract only the original section
            start = text.find(original_section_marker)
            end = text.find(replacement_section_marker)
            original_section = text[start:end]
            
            # Now find catalog number in this section
            catalog_label = "Catalog Number:"
            if catalog_label in original_section:
                start_pos = original_section.find(catalog_label) + len(catalog_label)
                remaining = original_section[start_pos:].strip()
                
                # Get the first line that looks like a catalog number
                lines = remaining.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not any(x in line for x in ['Catalog Number', 'Original', 'Dimensional']):
                        return line
        
        # Fallback: try to find any catalog number
        catalog_value = extract_field_value(text, "Catalog Number:")
        return catalog_value
        
    except Exception as e:
        logger.error(f"Error extracting catalog number: {e}")
        return ""


def extract_abb_style_number(soup: BeautifulSoup, text: str) -> str:
    """
    Extract the ABB Style Number from the Replacement Information section.
    
    Args:
        soup: BeautifulSoup object
        text: Page text content
        
    Returns:
        ABB Style Number or empty string
    """
    try:
        # Method 1: Try to find link with the style number
        # ABB Style Numbers are often clickable links
        links = soup.find_all('a')
        for link in links:
            link_text = link.get_text().strip()
            # ABB style numbers typically match pattern like: 138N0812BA
            if link_text and len(link_text) > 5 and any(char.isdigit() for char in link_text):
                # Check if this link is in the Replacement Information section
                parent_text = str(link.parent)
                if 'ABB Style' in parent_text or 'Replacement' in parent_text:
                    return link_text
        
        # Method 2: Text-based extraction from Replacement Information section
        replacement_marker = "Replacement Information"
        if replacement_marker in text:
            start = text.find(replacement_marker)
            replacement_section = text[start:start+500]  # Look ahead 500 chars
            
            abb_style_label = "ABB Style Number:"
            if abb_style_label in replacement_section:
                start_pos = replacement_section.find(abb_style_label) + len(abb_style_label)
                remaining = replacement_section[start_pos:].strip()
                
                lines = remaining.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not any(x in line for x in ['ABB Style', 'Replacement', 'Dimensional']):
                        return line
        
        # Method 3: Fallback
        abb_value = extract_field_value(text, "ABB Style Number:")
        return abb_value
        
    except Exception as e:
        logger.error(f"Error extracting ABB Style Number: {e}")
        return ""


def save_to_csv(data: Dict[str, str], filepath: str = OUTPUT_CSV) -> bool:
    """
    Save bushing data to CSV file.
    
    Args:
        data: Dictionary containing bushing data
        filepath: Path to the CSV file
        
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
        print("Usage: python scraper.py <index>")
        print("Example: python scraper.py 42131")
        sys.exit(1)
    
    try:
        index = int(sys.argv[1])
    except ValueError:
        logger.error("Index must be a valid integer")
        sys.exit(1)
    
    # Scrape data
    bushing_data = scrape_bushing_data(index)
    
    if bushing_data:
        # Save to CSV
        if save_to_csv(bushing_data):
            print(f"✓ Successfully scraped and saved data for index {index}")
            print(f"  Manufacturer: {bushing_data['Original Bushing Information - Original Bushing Manufacturer']}")
            print(f"  Catalog Number: {bushing_data['Original Bushing Information - Catalog Number']}")
            print(f"  ABB Style Number: {bushing_data['Replacement Information - ABB Style Number']}")
        else:
            print(f"✗ Failed to save data for index {index}")
            sys.exit(1)
    else:
        print(f"✗ Failed to scrape data for index {index}")
        sys.exit(1)


if __name__ == "__main__":
    main()
