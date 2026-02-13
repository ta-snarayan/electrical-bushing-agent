# BIL Field Filtering Analysis - Major Discovery

**Date**: February 13, 2026  
**Discovery**: BIL filtering can capture **109 additional products** (67.7% of remaining gap!)  
**Potential Coverage**: 98.1% (2,628 / 2,680 products)

---

## Executive Summary

Exploration of alternative filtering fields revealed that **BIL (Basic Impulse Level)** filtering can capture 109 products missed by kV Class filtering, potentially increasing coverage from **94.0% to 98.1%** - a gain of **+4.1%**.

This reduces the missing product count from 161 to just **52 products** (1.9% gap).

---

## Field Analysis Results

### Available Fields for Filtering

| Field | Unique Values | % with Field (PCORE) | % with Field (Electro) | Suitability |
|-------|---------------|----------------------|------------------------|-------------|
| **kV Class** | 52 | 96.1% | 100.0% | ✅ Currently used |
| **BIL** | 28 | 94.9% | 99.9% | ✅ **EXCELLENT** |
| **Current Rating** | 89 | 86.9% | 100.0% | ⚠️ Many values, lower coverage |
| Product Type | 4 | ? | ? | ❌ Too few values |
| Industry Standards | 14 | ? | ? | ⚠️ May help marginally |

### Key Insight: BIL Complements kV Class

**PCORE Electric field coverage:**
- With kV Class: 1,176 / 1,224 = **96.1%**
- With BIL: 1,162 / 1,224 = **94.9%**
- **Without kV Class: ~48 products** (3.9%)
- **Without BIL: ~62 products** (5.1%)

**Critical finding**: Some products have BIL but not kV Class, and vice versa. This creates an opportunity to capture products missed by kV-only filtering.

---

## BIL Filtering Test Results

### Products Found by BIL Filtering

| Brand | Products via BIL | Products via kV (current) | Difference |
|-------|------------------|---------------------------|------------|
| **PCORE Electric** | 1,160 | 1,075 | +85 |
| **Electro Composites** | 1,455 | 1,444 | +11 |
| **Total** | **2,615** | **2,519** | **+96** |

### Overlap Analysis

- **Products in BOTH datasets**: 2,506 (overlap)
- **TRULY NEW products**: **109** ⭐
- **Products missed by BIL filter**: 13 (captured by kV but not BIL)

**Interpretation**: 
- BIL finds 109 products that kV filtering missed
- BIL misses 13 products that kV filtering captured
- **Net gain potential**: 109 - 13 = **+96 products** if using BIL alone
- **Combined strategy**: Use BOTH kV AND BIL → capture all 2,628 products

---

## Sample of NEW Products Found (via BIL)

First 20 of 109 new catalog numbers:

1. B-88922-70
2. B-88923-68-70
3. B-88923-8-70
4. B-88933-149-70
5. B-88943-176-70
6. B-88943-203-70
7. B-88943-70
8. B-89401-10-15-70
9. B-89401-10-70
10. B-89411-10-55-70
11. B-89411-55-70
12. B-89411-70
13. B-89413-328-70
14. B-89421-150-70
15. B-89421-345-70
16. B-89423-308-70
17. B-89493-10-70
18. B-89493-200-70
19. B-89493-40-70
20. B-89493-6-70

... and 89 more

---

## BIL Values Discovered

### PCORE Electric (13 BIL values)
- 110 kV → 155 products
- 150 kV → 266 products
- 200 kV → 165 products
- 350 kV → 137 products
- (9 more values with products)

### Electro Composites (21 BIL values)
- 110 kV → 388 products
- 150 kV → 385 products
- 200 kV → 184 products
- 250 kV → 121 products
- 350 kV → 149 products
- (16 more values with products)

**Total unique BIL values**: 28 (combining both brands)

---

## Recommended Implementation Strategy

### Option 1: BIL-Only Filtering (Simpler)
**Replace** kV Class filtering with BIL filtering
- **Pros**: Simpler code, captures 96 net additional products
- **Cons**: Loses 13 products that kV captured
- **Result**: 2,615 products (97.6% coverage)

### Option 2: Combined kV + BIL Filtering ⭐ **RECOMMENDED**
**Supplement** existing kV Class filtering with BIL filtering
- **Pros**: Maximum coverage, captures everything from both methods
- **Cons**: More queries, slightly longer execution time
- **Result**: ~2,628 products (98.1% coverage)

### Option 3: BIL Gap-Filling (Conservative)
Keep kV filtering as primary, use BIL only for gap-filling
- **Pros**: Minimal code changes, targeted improvement
- **Cons**: More complex logic
- **Result**: 2,519 + 109 = 2,628 products (98.1% coverage)

---

## Implementation: Option 2 (Combined Filtering)

### Proposed Scraper Enhancement

```python
def scrape_with_combined_filtering(brand: str, all_products: List[Dict]) -> None:
    """
    Use BOTH kV Class and BIL filtering to maximize coverage.
    
    Strategy:
    1. Query all brand+kV combinations (existing logic)
    2. Query all brand+BIL combinations (new)
    3. Deduplicate by catalog number
    """
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Scraping {brand} with COMBINED kV + BIL filtering")
    logger.info(f"{'='*80}")
    
    # Step 1: kV Class filtering (existing)
    brand_filter = f"{CATEGORY_FILTER} AND Brands:'{brand}'"
    kv_classes = get_unique_kv_classes(brand_filter)
    
    for kv_class in kv_classes:
        filter_str = f"{brand_filter} AND 'kV Class':'{kv_class}'"
        scrape_with_filter(filter_str, all_products)
    
    # Step 2: BIL filtering (new)
    bil_values = get_unique_bil_values(brand_filter)
    
    for bil in bil_values:
        filter_str = f"{brand_filter} AND 'BIL':'{bil}'"
        scrape_with_filter(filter_str, all_products)


def get_unique_bil_values(brand_filter: str, max_samples: int = 500) -> List[str]:
    """
    Discover all unique BIL values for a given brand filter.
    Similar to get_unique_kv_classes() but for BIL field.
    """
    logger.info("  Discovering unique BIL values...")
    bil_values = set()
    
    pages_to_sample = min(10, max_samples // 100)
    
    for page in range(pages_to_sample):
        response = search_products(category_filter=brand_filter, 
                                   hits_per_page=100, page=page)
        if response and 'results' in response:
            hits = response['results'][0].get('hits', [])
            for hit in hits:
                bil = hit.get('BIL')
                if bil:
                    bil_values.add(bil)
    
    sorted_bil = sorted(bil_values)
    logger.info(f"  ✓ Found {len(sorted_bil)} unique BIL values")
    return sorted_bil
```

### Expected Performance Impact

- **Additional queries**: ~28 BIL values × 2 brands = ~56 queries
- **Current queries**: ~52 kV values × 2 brands = ~104 queries
- **New total**: ~160 queries (vs 104 currently)
- **Execution time**: ~90-100 seconds (vs 68 currently)
- **Worth it?**: **YES** - 109 additional products for 30 seconds

---

## Coverage Projection

### Current State (v2.1)
- Products: 2,519
- Coverage: 94.0%
- Missing: 161 (6.0%)

### After BIL Enhancement (v2.2 - Projected)
- Products: **2,628** (+109)
- Coverage: **98.1%** (+4.1%)
- Missing: **52** (-109, only 1.9% gap!)

### Remaining 52 Products
After combined kV + BIL filtering, only 52 products remain uncaptured. These are likely:
1. Products with NULL for BOTH kV Class AND BIL (~40 products estimated)
2. API index inconsistencies (~12 products)

**Analysis**: PCORE has 48 products without kV Class and 62 without BIL. If the overlap is high (products missing both fields), the remaining gap of 52 aligns with expectations.

---

## Data Quality Considerations

### Why BIL Filtering Works

**BIL (Basic Impulse Level)** is a critical electrical specification for bushings:
- Measures insulation strength against voltage surges
- Industry-standard specification (always present in datasheets)
- Low-cardinality field (28 values) → good for sub-filtering
- High coverage (95-100% of products have this field)

### Products with BIL but not kV Class

Some products may have:
- BIL specified but kV Class missing (data entry inconsistency)
- BIL as primary specification, kV Class as derived/optional
- Legacy products with only BIL in database

**Implication**: BIL filtering is not redundant with kV filtering - it captures different products!

---

## Cost-Benefit Analysis

| Metric | Current (v2.1) | After BIL (v2.2) | Change |
|--------|----------------|------------------|--------|
| **Coverage** | 94.0% | 98.1% | **+4.1%** ✅ |
| **Products** | 2,519 | 2,628 | **+109** ✅ |
| **Missing** | 161 (6.0%) | 52 (1.9%) | **-109** ✅ |
| **Execution Time** | 68 sec | ~100 sec | +32 sec ⚠️ |
| **API Requests** | ~280 | ~420 | +140 ⚠️ |
| **Code Complexity** | Medium | Medium+ | Slight ⚠️ |

### Verdict: **HIGHLY RECOMMENDED**

- **Major coverage improvement**: 4.1% gain is significant
- **Closes most of remaining gap**: 161 → 52 missing (67.7% reduction)
- **Minimal cost**: 30 seconds execution time is trivial
- **Clean data**: All 109 products validated as truly new

---

## Next Steps

1. ✅ **Validate findings** - Confirm 109 new products exist
2. ⏭️ **Implement BIL filtering** - Add to scraper (Option 2 recommended)
3. ⏭️ **Test combined approach** - Verify 2,628 products captured
4. ⏭️ **Update documentation** - Reflect 98.1% coverage
5. ⏭️ **Final gap analysis** - Analyze remaining 52 products

### If 52 Products Still Missing

After BIL implementation, can try:
- **Current Rating filtering** (89 values) - may capture some of remaining 52
- **Product Type filtering** (4 values) - quick check
- **Industry Standards filtering** (14 values) - may help marginally

**Expected final coverage**: 98-99% (2,628-2,650 products)

---

## Conclusion

BIL field filtering represents a **major breakthrough** in Hubbell bushing data collection:

- Discovered through systematic field exploration
- Captures **109 products** (67.7% of remaining gap)
- Increases coverage from 94.0% to **98.1%**
- Reduces missing products from 161 to just **52**
- Implementation is straightforward (similar to kV filtering)

**This brings coverage close to the theoretical maximum**, with only ~50 products remaining that likely have NULL values for both kV Class and BIL fields.

---

**Status**: ✅ Analysis Complete - Ready for Implementation  
**Recommendation**: Implement Option 2 (Combined kV + BIL filtering)  
**Expected Result**: 2,628 products (98.1% coverage)  
**Execution Time**: ~100 seconds (acceptable)
