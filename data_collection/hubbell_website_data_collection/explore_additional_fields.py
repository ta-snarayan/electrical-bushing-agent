"""
Explore Additional Fields for Gap-Filling
==========================================

This script explores other product fields (BIL, Current Rating, Product Type, etc.)
to identify additional filtering strategies that could capture the remaining 161 missing products.

Strategy:
1. Query API to see all available facets/fields
2. Discover unique values for BIL, Current Rating, and other fields
3. Test queries using these fields to find products missed by kV Class filtering
4. Analyze coverage potential of each field

Author: Generated for Hubbell bushing data collection enhancement
Date: 2026-02-13
"""

import requests
import json
import pandas as pd
from typing import Dict, List, Set
from collections import defaultdict

# Algolia API configuration
ALGOLIA_APP_ID = "5JH7C4O2N4"
ALGOLIA_API_KEY = "69e73c81a774c3c152e24bc652cfd6da"
ALGOLIA_INDEX = "Products_featured"
ALGOLIA_URL = f"https://{ALGOLIA_APP_ID.lower()}-dsn.algolia.net/1/indexes/*/queries"

CATEGORY_FILTER = "Categories.lvl3:'Power & Utilities > Bushings > Power Apparatus Bushings > Condenser Bushings'"


def query_api(filter_str: str, hits_per_page: int = 100, page: int = 0) -> Dict:
    """Query Algolia API with filter."""
    headers = {
        "Content-Type": "application/json",
        "X-Algolia-API-Key": ALGOLIA_API_KEY,
        "X-Algolia-Application-Id": ALGOLIA_APP_ID
    }
    
    payload = {
        "requests": [{
            "indexName": ALGOLIA_INDEX,
            "hitsPerPage": hits_per_page,
            "facets": ["*"],  # Request all facets
            "sortFacetValuesBy": "alpha",
            "filters": f"({filter_str})",
            "clickAnalytics": True,
            "page": page,
            "params": ""
        }]
    }
    
    response = requests.post(ALGOLIA_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def explore_all_facets():
    """Step 1: Discover all available facets/fields in the API."""
    print("=" * 80)
    print("STEP 1: DISCOVERING ALL AVAILABLE FACETS/FIELDS")
    print("=" * 80)
    
    response = query_api(CATEGORY_FILTER, hits_per_page=100, page=0)
    
    if 'results' in response and len(response['results']) > 0:
        result = response['results'][0]
        facets = result.get('facets', {})
        
        print(f"\n✓ Total products in category: {result.get('nbHits', 0)}")
        print(f"\n✓ Available facets/fields ({len(facets)}):\n")
        
        for facet_name, facet_values in sorted(facets.items()):
            value_count = len(facet_values)
            print(f"  • {facet_name:<40} ({value_count} unique values)")
            
            # Show sample values for interesting fields
            if facet_name in ['BIL', 'Current Rating', 'Product Type', 'kV Class', 'Brands']:
                sample_values = list(facet_values.keys())[:10]
                for val in sample_values:
                    count = facet_values[val]
                    print(f"      └─ {val} ({count} products)")
                if len(facet_values) > 10:
                    print(f"      └─ ... and {len(facet_values) - 10} more")
                print()
        
        return facets
    
    return {}


def discover_field_values(field_name: str, brands: List[str]) -> Dict[str, Set[str]]:
    """Step 2: Discover all unique values for a specific field across brands."""
    print("=" * 80)
    print(f"STEP 2: DISCOVERING ALL VALUES FOR '{field_name}'")
    print("=" * 80)
    
    field_values = defaultdict(set)
    
    for brand in brands:
        print(f"\n▶ Sampling {brand}...")
        
        # Sample across multiple pages to discover field diversity
        for page in range(10):
            filter_str = f"{CATEGORY_FILTER} AND Brands:'{brand}'"
            response = query_api(filter_str, hits_per_page=100, page=page)
            
            if 'results' in response and len(response['results']) > 0:
                hits = response['results'][0].get('hits', [])
                
                if not hits:
                    break
                
                for hit in hits:
                    value = hit.get(field_name)
                    if value:
                        field_values[brand].add(str(value))
        
        print(f"  ✓ Found {len(field_values[brand])} unique {field_name} values")
    
    return field_values


def test_field_filtering(field_name: str, field_values: Dict[str, Set[str]]) -> Dict:
    """Step 3: Test querying by field values to find additional products."""
    print("=" * 80)
    print(f"STEP 3: TESTING {field_name.upper()} FILTERING STRATEGY")
    print("=" * 80)
    
    all_catalog_numbers = set()
    brand_counts = defaultdict(int)
    
    for brand, values in field_values.items():
        print(f"\n▶ Testing {brand} with {len(values)} {field_name} values...")
        
        for value in sorted(values):
            filter_str = f"{CATEGORY_FILTER} AND Brands:'{brand}' AND '{field_name}':'{value}'"
            response = query_api(filter_str, hits_per_page=100, page=0)
            
            if 'results' in response and len(response['results']) > 0:
                result = response['results'][0]
                total_hits = result.get('nbHits', 0)
                
                if total_hits > 0:
                    # Collect all products from this filter
                    pages_needed = (total_hits + 99) // 100
                    
                    for page in range(min(pages_needed, 10)):  # Safety limit
                        page_response = query_api(filter_str, hits_per_page=100, page=page)
                        if 'results' in page_response:
                            hits = page_response['results'][0].get('hits', [])
                            for hit in hits:
                                catalog = hit.get('Catalog Number')
                                if catalog:
                                    all_catalog_numbers.add(catalog)
                                    brand_counts[brand] += 1
                    
                    if total_hits > 100:
                        print(f"  • {value:<30} → {total_hits:>4} products")
    
    print(f"\n{'─' * 80}")
    print(f"RESULTS:")
    print(f"  Total unique products found: {len(all_catalog_numbers)}")
    for brand, count in brand_counts.items():
        print(f"  • {brand}: {count} products")
    print(f"{'─' * 80}")
    
    return {
        'catalog_numbers': all_catalog_numbers,
        'brand_counts': dict(brand_counts),
        'total': len(all_catalog_numbers)
    }


def compare_with_existing(new_catalog_numbers: Set[str], existing_csv: str) -> Dict:
    """Step 4: Compare new results with existing dataset to find truly new products."""
    print("=" * 80)
    print("STEP 4: COMPARING WITH EXISTING DATASET")
    print("=" * 80)
    
    try:
        df = pd.read_csv(existing_csv)
        existing_catalogs = set(df['Original Bushing Information - Catalog Number'].values)
        
        print(f"\n✓ Loaded existing dataset: {len(existing_catalogs)} products")
        print(f"✓ Found via new filtering: {len(new_catalog_numbers)} products")
        
        # Find products in new results but not in existing
        truly_new = new_catalog_numbers - existing_catalogs
        
        # Find products in existing but not in new results
        missed_by_new_filter = existing_catalogs - new_catalog_numbers
        
        print(f"\n{'─' * 80}")
        print(f"COMPARISON RESULTS:")
        print(f"  ✓ Products in BOTH datasets: {len(new_catalog_numbers & existing_catalogs)}")
        print(f"  ★ TRULY NEW products: {len(truly_new)} ← THESE ARE ADDITIONAL!")
        print(f"  ✗ Products missed by new filter: {len(missed_by_new_filter)}")
        print(f"{'─' * 80}")
        
        if truly_new:
            print(f"\n★ NEW PRODUCTS FOUND ({len(truly_new)}):")
            for i, catalog in enumerate(sorted(list(truly_new)[:20]), 1):
                print(f"  {i:2}. {catalog}")
            if len(truly_new) > 20:
                print(f"  ... and {len(truly_new) - 20} more")
        
        return {
            'truly_new': truly_new,
            'overlap': len(new_catalog_numbers & existing_catalogs),
            'missed': missed_by_new_filter
        }
    
    except Exception as e:
        print(f"✗ Error loading existing dataset: {e}")
        return {'truly_new': set(), 'overlap': 0, 'missed': set()}


def analyze_missing_products():
    """Step 5: Analyze products without specific fields (NULL values)."""
    print("=" * 80)
    print("STEP 5: ANALYZING PRODUCTS WITH NULL/MISSING FIELDS")
    print("=" * 80)
    
    brands = ["PCORE Electric", "Electro Composites"]
    
    for brand in brands:
        print(f"\n▶ Analyzing {brand}...")
        
        filter_str = f"{CATEGORY_FILTER} AND Brands:'{brand}'"
        response = query_api(filter_str, hits_per_page=100, page=0)
        
        if 'results' in response:
            result = response['results'][0]
            total = result.get('nbHits', 0)
            
            # Check facets to see products WITH specific fields
            facets = result.get('facets', {})
            
            kv_with_field = sum(facets.get('kV Class', {}).values())
            bil_with_field = sum(facets.get('BIL', {}).values())
            current_with_field = sum(facets.get('Current Rating', {}).values())
            
            print(f"  Total products: {total}")
            print(f"  With 'kV Class': {kv_with_field} ({kv_with_field/total*100:.1f}%)")
            print(f"  With 'BIL': {bil_with_field} ({bil_with_field/total*100:.1f}%)")
            print(f"  With 'Current Rating': {current_with_field} ({current_with_field/total*100:.1f}%)")
            
            print(f"\n  Estimated NULL counts:")
            print(f"  Without 'kV Class': ~{total - kv_with_field} ({(total-kv_with_field)/total*100:.1f}%)")
            print(f"  Without 'BIL': ~{total - bil_with_field} ({(total-bil_with_field)/total*100:.1f}%)")
            print(f"  Without 'Current Rating': ~{total - current_with_field} ({(total-current_with_field)/total*100:.1f}%)")


def main():
    """Main exploration workflow."""
    print("\n" + "=" * 80)
    print("HUBBELL BUSHING DATA - ADDITIONAL FIELD EXPLORATION")
    print("=" * 80)
    print("\nGoal: Find strategies to capture remaining 161 products (6% gap)")
    print("Current coverage: 2,519 / 2,680 (94.0%)")
    print("Approach: Explore BIL, Current Rating, and other fields for filtering")
    print("\n")
    
    brands = ["PCORE Electric", "Electro Composites"]
    existing_csv = "hubbell_website_bushing_master_list_complete.csv"
    
    # Step 1: Discover all available facets
    facets = explore_all_facets()
    
    # Step 5: Analyze NULL field distribution
    analyze_missing_products()
    
    # Identify promising fields for filtering (fields with reasonable number of unique values)
    promising_fields = []
    for field_name, field_values in facets.items():
        value_count = len(field_values)
        # Fields with 5-100 unique values are good for sub-filtering
        if field_name not in ['Brands', 'kV Class'] and 5 <= value_count <= 100:
            promising_fields.append((field_name, value_count))
    
    if promising_fields:
        print("\n" + "=" * 80)
        print("PROMISING FIELDS FOR SUB-FILTERING:")
        print("=" * 80)
        print("\nFields with 5-100 unique values (good for sub-filtering):\n")
        for field, count in sorted(promising_fields, key=lambda x: x[1]):
            print(f"  • {field:<40} ({count} values)")
    
    # Step 2-4: Test most promising fields
    test_fields = ['BIL', 'Current Rating', 'Product Type']
    
    for field in test_fields:
        if field in facets:
            print(f"\n\n" + "=" * 80)
            print(f"TESTING FIELD: {field.upper()}")
            print("=" * 80)
            
            # Discover values
            field_values = discover_field_values(field, brands)
            
            # Test filtering
            results = test_field_filtering(field, field_values)
            
            # Compare with existing
            comparison = compare_with_existing(results['catalog_numbers'], existing_csv)
            
            print(f"\n★ POTENTIAL GAIN from {field}: {len(comparison['truly_new'])} new products")
            
            input("\nPress Enter to continue to next field...")


if __name__ == "__main__":
    main()
