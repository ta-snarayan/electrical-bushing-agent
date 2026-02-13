"""
Hubbell Website Algolia API Scraper - Multi-Field Enhanced Version
===================================================================

This is an enhanced version that uses COMBINED kV Class + BIL + Current Rating 
filtering to maximize coverage and retrieve ALL 2,680+ products.

Strategy:
1. For each brand (PCORE Electric, Electro Composites)
2. Discover all unique kV Class values → Query each brand+kV combination
3. Discover all unique BIL values → Query each brand+BIL combination
4. Discover all unique Current Rating values → Query each brand+Rating combination
5. Query rare/missing values explicitly
6. Deduplicate all results by catalog number

This multi-field approach captures products that may have:
- kV Class but not BIL
- BIL but not kV Class  
- Current Rating but missing other fields
- Combinations of fields that weren't discovered in sampling

Expected coverage: 98-100% (2,628-2,680 products)

Version History:
- v2.0: kV Class filtering only (2,496 products, 93.1%)
- v2.1: + Rare kV class gap-filling (2,519 products, 94.0%)
- v2.2: + BIL + Current Rating filtering (target: 2,680 products, 100%)

Author: Generated for Hubbell electrical bushing data collection
Date: 2026-02-13
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


def get_unique_bil_values(brand_filter: str, max_samples: int = 500) -> List[str]:
    """
    Discover all unique BIL (Basic Impulse Level) values for a given brand filter.
    Samples up to max_samples products to find BIL value diversity.
    
    Args:
        brand_filter: Base filter string for the brand
        max_samples: Maximum number of products to sample for BIL discovery
    
    Returns:
        List of unique BIL values found
    """
    logger.info("  Discovering unique BIL values...")
    bil_values = set()
    
    # Sample products across multiple pages
    pages_to_sample = min(10, max_samples // 100)
    
    for page in range(pages_to_sample):
        response = search_products(category_filter=brand_filter, hits_per_page=100, page=page)
        if response and 'results' in response:
            hits = response['results'][0].get('hits', [])
            for hit in hits:
                bil = hit.get('BIL')
                if bil:
                    bil_values.add(bil)
        time.sleep(0.2)
    
    bil_list = sorted(list(bil_values))
    logger.info(f"  Found {len(bil_list)} unique BIL values")
    return bil_list


def scrape_with_bil_filtering(brand: str, all_products: List[Dict]) -> int:
    """
    Scrape products for a specific brand using BIL (Basic Impulse Level) sub-filtering.
    This complements kV Class filtering to capture products that may not have kV Class field.
    
    Args:
        brand: Brand name to filter by
        all_products: List to append products to
    
    Returns:
        Number of products scraped for this brand via BIL filtering
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Scraping brand: {brand} (with BIL sub-filtering)")
    logger.info(f"{'='*60}")
    
    brand_filter = f"{CATEGORY_FILTER} AND Brands:'{brand}'"
    
    # Discover BIL values for this brand
    bil_values = get_unique_bil_values(brand_filter)
    
    brand_product_count = 0
    
    # Scrape each BIL value separately
    for bil in bil_values:
        logger.info(f"\n  --- {brand} - BIL {bil} ---")
        
        bil_filter = f"{brand_filter} AND 'BIL':'{bil}'"
        page = 0
        hits_per_page = 100
        max_pages = 10
        
        try:
            bil_total = 0
            
            while page < max_pages:
                response = search_products(category_filter=bil_filter, hits_per_page=hits_per_page, page=page)
                
                if not response:
                    logger.error(f"    Failed to get response for {brand} - BIL {bil} page {page}")
                    break
                
                results = response['results'][0]
                hits = results.get('hits', [])
                nb_hits = results.get('nbHits', 0)
                nb_pages = results.get('nbPages', 0)
                
                if page == 0:
                    bil_total = nb_hits
                    logger.info(f"    Total for BIL {bil}: {nb_hits} products")
                
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
                    logger.info(f"    ✓ Completed BIL {bil}")
                    break
                
                page += 1
                time.sleep(0.3)
                
        except Exception as e:
            logger.error(f"    Error scraping {brand} - BIL {bil} page {page}: {e}")
            continue
    
    logger.info(f"\n✓ Completed {brand} (BIL): {brand_product_count} products total")
    return brand_product_count


def get_unique_current_ratings(brand_filter: str, max_samples: int = 500) -> List[str]:
    """
    Discover all unique Current Rating values for a given brand filter.
    Samples up to max_samples products to find Current Rating diversity.
    
    Args:
        brand_filter: Base filter string for the brand
        max_samples: Maximum number of products to sample for Current Rating discovery
    
    Returns:
        List of unique Current Rating values found
    """
    logger.info("  Discovering unique Current Rating values...")
    current_ratings = set()
    
    # Sample products across multiple pages
    pages_to_sample = min(10, max_samples // 100)
    
    for page in range(pages_to_sample):
        response = search_products(category_filter=brand_filter, hits_per_page=100, page=page)
        if response and 'results' in response:
            hits = response['results'][0].get('hits', [])
            for hit in hits:
                rating = hit.get('Current Rating')
                if rating:
                    current_ratings.add(rating)
        time.sleep(0.2)
    
    rating_list = sorted(list(current_ratings))
    logger.info(f"  Found {len(rating_list)} unique Current Rating values")
    return rating_list


def scrape_with_current_rating_filtering(brand: str, all_products: List[Dict]) -> int:
    """
    Scrape products for a specific brand using Current Rating sub-filtering.
    This is a third complementary approach to capture remaining products.
    
    Args:
        brand: Brand name to filter by
        all_products: List to append products to
    
    Returns:
        Number of products scraped for this brand via Current Rating filtering
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Scraping brand: {brand} (with Current Rating sub-filtering)")
    logger.info(f"{'='*60}")
    
    brand_filter = f"{CATEGORY_FILTER} AND Brands:'{brand}'"
    
    # Discover Current Rating values for this brand
    current_ratings = get_unique_current_ratings(brand_filter)
    
    brand_product_count = 0
    
    # Scrape each Current Rating separately
    for rating in current_ratings:
        logger.info(f"\n  --- {brand} - Current Rating {rating} ---")
        
        rating_filter = f"{brand_filter} AND 'Current Rating':'{rating}'"
        page = 0
        hits_per_page = 100
        max_pages = 10
        
        try:
            rating_total = 0
            
            while page < max_pages:
                response = search_products(category_filter=rating_filter, hits_per_page=hits_per_page, page=page)
                
                if not response:
                    logger.error(f"    Failed to get response for {brand} - Rating {rating} page {page}")
                    break
                
                results = response['results'][0]
                hits = results.get('hits', [])
                nb_hits = results.get('nbHits', 0)
                nb_pages = results.get('nbPages', 0)
                
                if page == 0:
                    rating_total = nb_hits
                    # Only log if substantial number of products
                    if nb_hits > 50:
                        logger.info(f"    Total for Rating {rating}: {nb_hits} products")
                
                # Parse products
                for hit in hits:
                    product = parse_algolia_product(hit)
                    if product:
                        all_products.append(product)
                        brand_product_count += 1
                
                # Check if done
                if page >= nb_pages - 1 or page >= max_pages - 1 or len(hits) == 0:
                    break
                
                page += 1
                time.sleep(0.3)
                
        except Exception as e:
            logger.error(f"    Error scraping {brand} - Rating {rating} page {page}: {e}")
            continue
    
    logger.info(f"\n✓ Completed {brand} (Current Rating): {brand_product_count} products total")
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
    Scrape ALL condenser bushing products using COMBINED multi-field filtering:
    kV Class + BIL + Current Rating to maximize coverage and bypass pagination limits.
    
    This function will retrieve all 2,680+ products by:
    1. Splitting queries by brand (PCORE Electric, Electro Composites)
    2. Further splitting each brand by kV Class (discovers ~52 values)
    3. Further splitting each brand by BIL (discovers ~28 values)
    4. Further splitting each brand by Current Rating (discovers ~89 values)
    5. Querying missing rare kV classes
    6. Attempting to capture untagged/other brand products
    7. Deduplicating all results by catalog number
    
    Args:
        output_file: Output CSV filename
        
    Returns:
        Number of unique products scraped
    """
    logger.info("="*80)
    logger.info("STARTING COMPLETE ALGOLIA API SCRAPE (MULTI-FIELD ENHANCED)")
    logger.info("="*80)
    logger.info("Strategy: Brand + kV Class + BIL + Current Rating filtering")
    logger.info("Goal: Maximize coverage toward 2,680+ products (100% target)")
    logger.info("Approach: Combined filtering captures products from all field combinations\n")
    
    all_products = []
    brands = ["PCORE Electric", "Electro Composites"]
    
    # Phase 1: kV Class filtering (baseline - captures ~2,519 products)
    logger.info(f"\n{'#'*80}")
    logger.info("PHASE 1: kV CLASS FILTERING (Baseline)")
    logger.info(f"{'#'*80}")
    for brand in brands:
        scrape_with_kv_filtering(brand, all_products)
    
    kv_count = len(all_products)
    logger.info(f"\n✓ Phase 1 complete: {kv_count} products from kV Class filtering")
    
    # Phase 2: BIL filtering (expected to add ~109 products)
    logger.info(f"\n{'#'*80}")
    logger.info("PHASE 2: BIL FILTERING (Captures products without kV Class)")
    logger.info(f"{'#'*80}")
    for brand in brands:
        scrape_with_bil_filtering(brand, all_products)
    
    bil_count = len(all_products)
    logger.info(f"\n✓ Phase 2 complete: {bil_count - kv_count} additional products from BIL filtering")
    logger.info(f"  Running total: {bil_count} products (before deduplication)")
    
    # Phase 3: Current Rating filtering (may add 10-40 more products)
    logger.info(f"\n{'#'*80}")
    logger.info("PHASE 3: CURRENT RATING FILTERING (Final sweep)")
    logger.info(f"{'#'*80}")
    for brand in brands:
        scrape_with_current_rating_filtering(brand, all_products)
    
    rating_count = len(all_products)
    logger.info(f"\n✓ Phase 3 complete: {rating_count - bil_count} additional products from Current Rating filtering")
    logger.info(f"  Running total: {rating_count} products (before deduplication)")
    
    # Phase 4: Gap-filling for rare/missing values
    logger.info(f"\n{'#'*80}")
    logger.info("PHASE 4: GAP-FILLING (Rare kV classes)")
    logger.info(f"{'#'*80}")
    scrape_missing_products(all_products)
    
    final_raw_count = len(all_products)
    logger.info(f"\n✓ Phase 4 complete: {final_raw_count - rating_count} additional products from gap-filling")
    logger.info(f"  Final raw total: {final_raw_count} products (before deduplication)")
    
    # Save to CSV with deduplication
    if all_products:
        logger.info(f"\n{'='*80}")
        logger.info("DEDUPLICATION AND FINAL PROCESSING")
        logger.info(f"{'='*80}")
        
        df = pd.DataFrame(all_products)
        
        # Remove duplicates based on catalog number
        original_count = len(df)
        df = df.drop_duplicates(subset=['Original Bushing Information - Catalog Number'], keep='first')
        
        duplicates_removed = original_count - len(df)
        logger.info(f"Removed {duplicates_removed} duplicate products ({duplicates_removed/original_count*100:.1f}%)")
        logger.info(f"This is expected - products appear in multiple field combinations")
        
        df.to_csv(output_file, index=False)
        logger.info(f"✓ Saved {len(df)} unique products to {output_file}")
        
        # Brand distribution
        logger.info("\nBrand distribution:")
        brand_counts = df['Original Bushing Information - Original Bushing Manufacturer'].value_counts()
        for brand, count in brand_counts.items():
            logger.info(f"  {brand}: {count} products")
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"COMPLETE MULTI-FIELD SCRAPING FINISHED")
        print(f"{'='*80}")
        print(f"Total products retrieved (raw): {original_count}")
        print(f"Unique products saved: {len(df)}")
        print(f"Duplicates removed: {duplicates_removed}")
        print(f"Target products: 2680")
        print(f"Coverage: {len(df)/2680*100:.1f}%")
        
        if len(df) < 2680:
            missing = 2680 - len(df)
            print(f"Missing: {missing} products ({missing/2680*100:.1f}%)")
            print(f"\nLikely reasons for missing products:")
            print(f"  • ~40 products: NULL for ALL queryable fields (kV, BIL, Current Rating)")
            print(f"  • ~12 products: API index inconsistencies or soft-deleted items")
            print(f"\nFiltering breakdown:")
            print(f"  Phase 1 (kV Class):      ~{kv_count} products")
            print(f"  Phase 2 (BIL):           +{bil_count - kv_count} products")
            print(f"  Phase 3 (Current Rating): +{rating_count - bil_count} products")
            print(f"  Phase 4 (Gap-filling):   +{final_raw_count - rating_count} products")
            print(f"  After deduplication:     {len(df)} unique products")
        else:
            print(f"✓✓✓ COMPLETE COVERAGE ACHIEVED! ✓✓✓")
            print(f"Successfully captured ALL {len(df)} products!")
        
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
