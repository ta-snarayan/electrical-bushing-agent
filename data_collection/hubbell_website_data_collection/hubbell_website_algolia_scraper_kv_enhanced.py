"""
Hubbell Website Algolia API Scraper - kV Class Enhanced Version
================================================================

This is an enhanced version that uses kV Class sub-filtering to bypass 
Algolia's 1,000-product pagination limit and retrieve ALL 2,680+ products.

Strategy:
1. For each brand (PCORE Electric, Electro Composites)
2. Discover all unique kV Class values
3. Query each brand+kV combination separately (each will be < 1,000 products)
4. Combine all results to get complete dataset

Author: Generated for Hubbell electrical bushing data collection
Date: 2026-02-12
"""

import requests
import json
import pandas as pd
import logging
import time
from typing import Optional, Dict, List
from urllib.parse import quote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Algolia API configuration (from website inspection)
ALGOLIA_APP_ID = "5JH7C4O2N4"
ALGOLIA_API_KEY = "69e73c81a774c3c152e24bc652cfd6da"
ALGOLIA_INDEX = "Products_featured"
ALGOLIA_URL = f"https://{ALGOLIA_APP_ID.lower()}-dsn.algolia.net/1/indexes/*/queries"

# Category filter for Condenser Bushings
CATEGORY_FILTER = "Categories.lvl3:'Power & Utilities > Bushings > Power Apparatus Bushings > Condenser Bushings'"


def search_products(category_filter: str, hits_per_page: int = 100, page: int = 0) -> Optional[Dict]:
    """
    Query Algolia Search API with category filter, pagination.
    
    Args:
        category_filter: Algolia filter string for category (can include brand, kV filters)
        hits_per_page: Number of results per page (max 100)
        page: Page number (0-indexed)
    
    Returns:
        API response as dictionary, or None if request failed
    """
    headers = {
        "Content-Type": "application/json",
        "X-Algolia-API-Key": ALGOLIA_API_KEY,
        "X-Algolia-Application-Id": ALGOLIA_APP_ID
    }
    
    # Use the same payload structure as the original working scraper
    payload = {
        "requests": [{
            "indexName": ALGOLIA_INDEX,
            "hitsPerPage": hits_per_page,
            "facets": ["*"],
            "sortFacetValuesBy": "alpha",
            "filters": f"({category_filter})",
            "clickAnalytics": True,
            "page": page,
            "params": ""
        }]
    }
    
    try:
        response = requests.post(ALGOLIA_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None


def parse_algolia_product(hit: Dict) -> Optional[Dict]:
    """
    Parse a product from Algolia API hit result.
    
    Args:
        hit: Product hit from Algolia response
    
    Returns:
        Dictionary with Website Link, Brand, Catalog Number
    """
    try:
        # Extract required fields directly from API response
        brand = hit.get('Brand', '').strip()
        catalog_number = hit.get('Catalog Number', '').strip()
        object_id = hit.get('objectID', '').strip()
        title = hit.get('title', '').strip()
        
        # Generate URL from title slug and objectID
        if title and object_id:
            title_slug = title.lower().replace(' ', '-').replace('®', '').replace('™', '')
            # Remove multiple consecutive dashes
            import re
            title_slug = re.sub(r'-+', '-', title_slug)
            title_slug = title_slug.strip('-')
            
            url = f"https://www.hubbell.com/hubbell/en/products/{title_slug}/p/{object_id}"
        else:
            url = f"https://www.hubbell.com/hubbell/en/p/{object_id}"
        
        return {
            "Website Link": url,
            "Original Bushing Information - Original Bushing Manufacturer": brand,
            "Original Bushing Information - Catalog Number": catalog_number
        }
        
    except Exception as e:
        logger.warning(f"Error parsing product: {e}")
        return None


def get_unique_kv_classes(brand_filter: str, max_samples: int = 500) -> List[str]:
    """
    Discover all unique kV classes for a given brand filter.
    Samples up to max_samples products to find kV class diversity.
    
    Args:
        brand_filter: Base filter string for the brand
        max_samples: Maximum number of products to sample for kV class discovery
    
    Returns:
        List of unique kV class values found
    """
    logger.info("  Discovering unique kV classes...")
    kv_classes = set()
    
    # Sample products across multiple pages
    pages_to_sample = min(10, max_samples // 100)
    
    for page in range(pages_to_sample):
        response = search_products(category_filter=brand_filter, hits_per_page=100, page=page)
        if response and 'results' in response:
            hits = response['results'][0].get('hits', [])
            for hit in hits:
                kv_class = hit.get('kV Class')
                if kv_class:
                    kv_classes.add(kv_class)
        time.sleep(0.2)
    
    kv_list = sorted(list(kv_classes))
    logger.info(f"  Found {len(kv_list)} unique kV classes: {kv_list}")
    return kv_list


def scrape_with_kv_filtering(brand: str, all_products: List[Dict]) -> int:
    """
    Scrape products for a specific brand using kV Class sub-filtering
    to bypass the 1,000-product Algolia pagination limit.
    
    Args:
        brand: Brand name to filter by
        all_products: List to append products to
    
    Returns:
        Number of products scraped for this brand
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Scraping brand: {brand} (with kV Class sub-filtering)")
    logger.info(f"{'='*60}")
    
    brand_filter = f"{CATEGORY_FILTER} AND Brands:'{brand}'"
    
    # Discover kV classes for this brand
    kv_classes = get_unique_kv_classes(brand_filter)
    
    brand_product_count = 0
    
    # Scrape each kV class separately
    for kv_class in kv_classes:
        logger.info(f"\n  --- {brand} - {kv_class} ---")
        
        kv_filter = f"{brand_filter} AND 'kV Class':'{kv_class}'"
        page = 0
        hits_per_page = 100
        max_pages = 10
        
        try:
            kv_total = 0
            
            while page < max_pages:
                response = search_products(category_filter=kv_filter, hits_per_page=hits_per_page, page=page)
                
                if not response:
                    logger.error(f"    Failed to get response for {brand} - {kv_class} page {page}")
                    break
                
                results = response['results'][0]
                hits = results.get('hits', [])
                nb_hits = results.get('nbHits', 0)
                nb_pages = results.get('nbPages', 0)
                
                if page == 0:
                    kv_total = nb_hits
                    logger.info(f"    Total for {kv_class}: {nb_hits} products")
                
                # Parse products
                for hit in hits:
                    product = parse_algolia_product(hit)
                    if product:
                        all_products.append(product)
                        brand_product_count += 1
                
                if page > 0 and page % 5 == 0:
                    logger.info(f"    Progress: page {page + 1}/{nb_pages}, {len(hits)} products")
                
                # Check if done
                if page >= nb_pages - 1 or page >= max_pages - 1 or len(hits) == 0:
                    logger.info(f"    ✓ Completed {kv_class}: {brand_product_count} products so far")
                    break
                
                page += 1
                time.sleep(0.3)
                
        except Exception as e:
            logger.error(f"    Error scraping {brand} - {kv_class} page {page}: {e}")
            continue
    
    logger.info(f"\n✓ Completed {brand}: {brand_product_count} products total")
    return brand_product_count


def scrape_missing_products(all_products: List[Dict]) -> int:
    """
    Attempt to capture products missed by standard brand+kV filtering.
    
    Targets:
    1. Products without kV Class field (NULL/empty)
    2. Rare kV Class values not discovered during sampling
    3. Products without brand tags
    
    Args:
        all_products: List to append found products to
    
    Returns:
        Number of additional products found
    """
    logger.info(f"\n{'='*60}")
    logger.info("Attempting to capture missing products...")
    logger.info(f"{'='*60}")
    
    initial_count = len(all_products)
    
    # Known missing kV classes from analysis (12 values, 23 products expected)
    missing_kv_classes = [
        '0.693 kV', '13.8 kV', '14.4 kV', '22 kV', '23 kV', '24.5 kV',
        '245 kV', '30 kV', '300 kV', '4 kV', '44 kV', '92 kV'
    ]
    
    brands = ["PCORE Electric", "Electro Composites"]
    
    # Strategy 1: Query each missing kV class
    logger.info(f"\n1. Querying {len(missing_kv_classes)} rare kV classes...")
    for kv_class in missing_kv_classes:
        for brand in brands:
            filter_str = f"{CATEGORY_FILTER} AND Brands:'{brand}' AND 'kV Class':'{kv_class}'"
            
            try:
                response = search_products(category_filter=filter_str, hits_per_page=100, page=0)
                if response and 'results' in response:
                    hits = response['results'][0].get('hits', [])
                    if hits:
                        logger.info(f"  Found {len(hits)} products for {brand} - {kv_class}")
                        for hit in hits:
                            product = parse_algolia_product(hit)
                            if product:
                                all_products.append(product)
                time.sleep(0.2)
            except Exception as e:
                logger.error(f"  Error querying {brand} - {kv_class}: {e}")
                continue
    
    # Strategy 2: Try products without brand filter (catch untagged/other brands)
    logger.info(f"\n2. Querying products without brand filter...")
    try:
        # Query category only, no brand filter
        response = search_products(category_filter=CATEGORY_FILTER, hits_per_page=100, page=0)
        if response and 'results' in response:
            results = response['results'][0]
            total_no_brand_filter = results.get('nbHits', 0)
            logger.info(f"  Total with category-only filter: {total_no_brand_filter}")
            
            # Sample first few pages to find products not matching known brands
            for page in range(min(5, results.get('nbPages', 0))):
                response = search_products(category_filter=CATEGORY_FILTER, hits_per_page=100, page=page)
                if response and 'results' in response:
                    hits = response['results'][0].get('hits', [])
                    for hit in hits:
                        brand = hit.get('Brand', '').strip()
                        # Check if brand is not one of the known brands
                        if brand and brand not in brands:
                            logger.info(f"  Found product from unexpected brand: {brand}")
                            product = parse_algolia_product(hit)
                            if product:
                                all_products.append(product)
                    time.sleep(0.3)
    except Exception as e:
        logger.error(f"  Error querying without brand filter: {e}")
    
    additional_found = len(all_products) - initial_count
    logger.info(f"\n✓ Found {additional_found} additional products using gap-filling queries")
    
    return additional_found


def scrape_all_products_complete(output_file: str = "hubbell_website_bushing_master_list_complete.csv") -> int:
    """
    Scrape ALL condenser bushing products using kV Class sub-filtering
    to bypass Algolia's 1,000-product pagination limit.
    
    This function will retrieve all 2,680+ products by:
    1. Splitting queries by brand (PCORE Electric, Electro Composites)
    2. Further splitting each brand by kV Class
    3. Querying missing rare kV classes
    4. Attempting to capture untagged/other brand products
    
    Args:
        output_file: Output CSV filename
        
    Returns:
        Number of unique products scraped
    """
    logger.info("="*80)
    logger.info("STARTING COMPLETE ALGOLIA API SCRAPE (kV Class Enhanced)")
    logger.info("="*80)
    logger.info("Strategy: Brand + kV Class sub-filtering to bypass 1,000-product limit")
    logger.info("Target: All 2,680+ Condenser Bushing products\n")
    
    all_products = []
    brands = ["PCORE Electric", "Electro Composites"]
    
    for brand in brands:
        scrape_with_kv_filtering(brand, all_products)
    
    # NEW: Attempt to capture missing products
    scrape_missing_products(all_products)
    
    # Save to CSV with deduplication
    if all_products:
        logger.info(f"\n{'='*80}")
        logger.info("Processing results...")
        logger.info(f"{'='*80}")
        
        df = pd.DataFrame(all_products)
        
        # Remove duplicates based on catalog number
        original_count = len(df)
        df = df.drop_duplicates(subset=['Original Bushing Information - Catalog Number'], keep='first')
        
        if len(df) < original_count:
            logger.info(f"Removed {original_count - len(df)} duplicate products")
        
        df.to_csv(output_file, index=False)
        logger.info(f"✓ Saved {len(df)} unique products to {output_file}")
        
        # Brand distribution
        logger.info("\nBrand distribution:")
        brand_counts = df['Original Bushing Information - Original Bushing Manufacturer'].value_counts()
        for brand, count in brand_counts.items():
            logger.info(f"  {brand}: {count} products")
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"COMPLETE SCRAPING FINISHED (with gap-filling)")
        print(f"{'='*80}")
        print(f"Total products retrieved: {original_count}")
        print(f"Unique products saved: {len(df)}")
        print(f"Target products: 2680")
        print(f"Coverage: {len(df)/2680*100:.1f}%")
        
        if len(df) < 2680:
            missing = 2680 - len(df)
            print(f"Missing: {missing} products ({missing/2680*100:.1f}%)")
            print(f"\nPossible reasons for missing products:")
            print(f"  • Products with NULL/empty fields not queryable via API")
            print(f"  • API index inconsistencies (count vs actual results)")
            print(f"  • Soft-deleted or hidden products in index")
        else:
            print(f"✓✓ COMPLETE COVERAGE ACHIEVED! ✓✓")
        
        print(f"\nOutput file: {output_file}")
        print(f"\nSample (first product):")
        if len(df) > 0:
            first = df.iloc[0]
            print(f"  Brand: {first['Original Bushing Information - Original Bushing Manufacturer']}")
            print(f"  Catalog: {first['Original Bushing Information - Catalog Number']}")
            print(f"  Link: {first['Website Link']}")
        print(f"{'='*80}\n")
        
        return len(df)
    else:
        logger.error("No products scraped")
        return 0


def test_kv_filtering():
    """
    Test kV Class filtering strategy by checking one brand.
    """
    logger.info("Testing kV Class filtering strategy...")
    
    brand = "PCORE Electric"
    brand_filter = f"{CATEGORY_FILTER} AND Brands:'{brand}'"
    
    # Get unique kV classes
    kv_classes = get_unique_kv_classes(brand_filter)
    
    # Test first kV class
    if kv_classes:
        test_kv = kv_classes[0]
        kv_filter = f"{brand_filter} AND 'kV Class':'{test_kv}'"
        
        response = search_products(category_filter=kv_filter, hits_per_page=5, page=0)
        
        if response:
            results = response['results'][0]
            logger.info(f"\nTest results for {brand} - {test_kv}:")
            logger.info(f"  Total products: {results.get('nbHits', 0)}")
            logger.info(f"  Total pages: {results.get('nbPages', 0)}")
            
            # Show sample
            if results.get('hits'):
                sample = results['hits'][0]
                logger.info(f"\n  Sample product:")
                logger.info(f"    Brand: {sample.get('Brand')}")
                logger.info(f"    kV Class: {sample.get('kV Class')}")
                logger.info(f"    Catalog: {sample.get('Catalog Number')}")
            
            logger.info("\n✓ kV filtering test successful")
            return True
    
    logger.error("✗ kV filtering test failed")
    return False


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Test mode: check kV filtering strategy
        test_kv_filtering()
    else:
        # Production mode: scrape all products with kV filtering
        scrape_all_products_complete()
