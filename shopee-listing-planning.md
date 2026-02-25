# Shopee Listing — Full Analysis & Implementation Plan

> Reference doc for all shopee-listing work.
> Created 25 Feb 2026. Last updated 25 Feb 2026.
> Repo: `it-awesomeree/awesomeree-web-app` (main branch)

---

# PART A — CURRENT STATE ANALYSIS

## A1. Database Tables

### requestDatabase

| Table | Rows | Role |
|---|---|---|
| `new_items` | 563 | Source of truth. One row per product event. Has `product_id`, `product_name_en`, `variation_list_en` (JSON), `variation_list_cn`, `shop`, `launch_type` (469 New Product, 94 New Variation), `date` |
| `shopee_listings` | 1940 | **LEGACY flat table.** One row per variation. The 1688 new_product scraper writes here. Has 1688 columns + n8n columns. Frontend no longer reads from this directly. |
| `shopee_listing_products` | 323 | **NORMALIZED** product-level data. 304 new_product + 19 new_variation. Stores 1688 columns + n8n columns + job state. **Missing Shopee existing data columns.** |
| `shopee_listing_variations` | 1940 | **NORMALIZED** one row per variation per product. Has `1688_variation`, `1688_variation_image`, `n8n_variation`, `n8n_variation_image`, `sort_order`. FK → `shopee_listing_products.product_id` |
| `shopee_listing_reviews` | 3 | Staging table for regenerated content. Status: `pending_review` / `approved` / `rejected` |
| `shopee_existing_listing` | 12 | **LEGACY for New Variation flow only.** Stores both 1688 data AND Shopee existing data. Disconnected from normalized schema. Has `shopee_product_name`, `shopee_description`, `tier_name_*`, `t*_variation`, etc. |
| `hero_templates` | - | Hero image templates per shop. `shop_name` + `template_url` (GCS URL) |
| `ShopeeTokens` | - | Shop credentials for Shopee API. `shop_id`, `shop_name`, `access_token`, `expires_at` |

### allbots DB

| Table | Role |
|---|---|
| `Shopee_Comp` | Competitor data. Linked by `our_item_id`. |

## A2. Scripts (`eten-workspace/my_script/`)

### `1688_web_scrape_new_product.py` (54KB)
- **Reads**: `new_items` (launch_type='New Product'), `shopee_listings` (dedup)
- **Writes to**: `shopee_listings` (legacy) — NOT `shopee_listing_products`
- **Row pattern**: One row PER variation (denormalized)
- **SQL**: `INSERT INTO shopee_listings (product_id, launch_type, 1688_url, 1688_product_name, 1688_variation, 1688_variation_image, 1688_hero, 1688_supporting_image, 1688_product_description_text, 1688_product_description_image, status, item_date)`

### `1688_web_scrape_new_variation.py` (60KB)
- **Reads**: `new_items` (launch_type='New Variation'), `shopee_existing_listing` (dedup)
- **Writes to**: `shopee_existing_listing`
- **Row pattern**: One row PER 1688 source. Variations as JSON arrays.
- **SQL**: `INSERT INTO shopee_existing_listing (product_id, 1688_url, 1688_product_name, 1688_variation, 1688_variation_images, 1688_description_images, item_date, updated_at) ON DUPLICATE KEY UPDATE ...`
- **Key difference vs new_product**: Variations stored as JSON arrays not separate rows. No hero/supporting split. Description text extracted but NOT saved.

### `shopee_api.py` (16KB)
- **Reads**: `new_items` (launch_type='New Variation') JOIN `ShopeeTokens`
- **Writes to**: `shopee_existing_listing` — **UPDATE only, NO INSERT**
- **SQL**: `UPDATE shopee_existing_listing SET shop_name, shopee_product_name, shopee_description, tier_name_1, t1_variation, shopee_variation_images, tier_name_2, t2_variation WHERE product_id = ?`
- **Shopee API**: `GET /api/v2/product/get_item_base_info` (batch 50) + `GET /api/v2/product/get_model_list` (per item)
- **Critical dependency**: Row MUST already exist (created by 1688 variation scraper). If no row, update silently skips.

## A3. Current Data Flow

### New Product Path (WORKING)
```
new_items (469) → 1688 scraper → shopee_listings (legacy, 1940 rows)
                                       ↓
                               [sync process]
                                       ↓
                         shopee_listing_products (304) + shopee_listing_variations
                                       ↓
                              Frontend + n8n webhooks
```

### New Variation Path (BROKEN)
```
new_items (94)
   ├→ 1688 variation scraper → shopee_existing_listing (12 rows, 1688 data)
   └→ shopee_api.py ──────────→ shopee_existing_listing (UPDATE Shopee data)
                                       ↓
                                 ╔═══════════╗
                                 ║  DEAD END  ║
                                 ╚═══════════╝
                     • No sync to normalized tables
                     • Frontend can't see Shopee data
                     • n8n can't read Shopee data
                     • 19 items in shopee_listing_products have ZERO Shopee data
```

## A4. Gap Summary

| # | Gap | Impact |
|---|---|---|
| 1 | `shopee_listing_products` has NO Shopee data columns | n8n variation webhook can't get Shopee data |
| 2 | `shopee_existing_listing` disconnected from normalized schema | Data island — 12 rows that nothing reads |
| 3 | 1688 variation scraper writes to wrong table | Data goes to `shopee_existing_listing` instead of normalized tables |
| 4 | Shopee API script writes to wrong table | Same problem |
| 5 | Shopee API is UPDATE-only (no INSERT) | If 1688 scraper hasn't run, Shopee data is silently lost |
| 6 | 94 New Variation items in `new_items` but only 19 in `shopee_listing_products` | 75 items not in the system at all |
| 7 | All 19 new_variation items in `shopee_listing_products` have zero n8n output | Variation generation has never run through normalized path |

---

# PART B — IMPLEMENTATION PLAN

## Architecture Decision

**Option A: Extend the normalized schema** (CHOSEN)

Add Shopee existing listing columns to `shopee_listing_products`. Update both scripts to write to the normalized tables. This gives us:
- Single source of truth for all listing data
- Frontend can display Shopee existing data alongside 1688 and n8n data
- n8n variation webhook gets all data from the same service layer
- No bridging / syncing between disconnected tables
- Clean deprecation path for `shopee_existing_listing`

---

## Phase 0: Preparation & Backup

**Objective**: Safeguard current data before making any changes.

### Step 0.1 — Back up affected tables
```sql
CREATE TABLE requestDatabase.shopee_existing_listing_backup_20260225
  AS SELECT * FROM requestDatabase.shopee_existing_listing;

CREATE TABLE requestDatabase.shopee_listing_products_backup_20260225
  AS SELECT * FROM requestDatabase.shopee_listing_products;

CREATE TABLE requestDatabase.shopee_listing_variations_backup_20260225
  AS SELECT * FROM requestDatabase.shopee_listing_variations;
```

### Step 0.2 — Verify FK constraint
Confirmed: `shopee_listing_variations.product_id` → FK → `shopee_listing_products.product_id` (`fk_variation_product`). Any INSERT into variations requires the product row to exist first.

### Step 0.3 — Verify unique index on `shopee_existing_listing`
Confirmed: Composite unique index `uq_product_1688url` on `(product_id, 1688_url)`.

**Acceptance**: Backups exist. Can rollback if needed.

---

## Phase 1: Database Schema Changes

**Objective**: Add Shopee existing data columns to the normalized `shopee_listing_products` table so it can store everything the New Variation workflow needs.

### Step 1.1 — ALTER `shopee_listing_products` (on `webapp_test` first)

```sql
ALTER TABLE webapp_test.shopee_listing_products
  ADD COLUMN shopee_product_name     VARCHAR(500) NULL   COMMENT 'Existing Shopee listing name (from Shopee API)'     AFTER n8n_supporting_image,
  ADD COLUMN shopee_description      LONGTEXT     NULL   COMMENT 'Existing Shopee listing description (from Shopee API)' AFTER shopee_product_name,
  ADD COLUMN shopee_variation_images JSON         NULL   COMMENT 'Existing Shopee tier-1 variation images (from Shopee API)' AFTER shopee_description,
  ADD COLUMN tier_name_1             VARCHAR(100) NULL   COMMENT 'Existing Shopee tier 1 name e.g. Colour (from Shopee API)' AFTER shopee_variation_images,
  ADD COLUMN t1_variation            JSON         NULL   COMMENT 'Existing Shopee tier 1 options e.g. ["Red","Blue"] (from Shopee API)' AFTER tier_name_1,
  ADD COLUMN tier_name_2             VARCHAR(100) NULL   COMMENT 'Existing Shopee tier 2 name e.g. Size (from Shopee API)' AFTER t1_variation,
  ADD COLUMN t2_variation            JSON         NULL   COMMENT 'Existing Shopee tier 2 options e.g. ["S","M","L"] (from Shopee API)' AFTER tier_name_2;
```

### Step 1.2 — Run the same ALTER on production

```sql
ALTER TABLE requestDatabase.shopee_listing_products
  ADD COLUMN shopee_product_name     VARCHAR(500) NULL   COMMENT 'Existing Shopee listing name (from Shopee API)'     AFTER n8n_supporting_image,
  ADD COLUMN shopee_description      LONGTEXT     NULL   COMMENT 'Existing Shopee listing description (from Shopee API)' AFTER shopee_product_name,
  ADD COLUMN shopee_variation_images JSON         NULL   COMMENT 'Existing Shopee tier-1 variation images (from Shopee API)' AFTER shopee_description,
  ADD COLUMN tier_name_1             VARCHAR(100) NULL   COMMENT 'Existing Shopee tier 1 name e.g. Colour (from Shopee API)' AFTER shopee_variation_images,
  ADD COLUMN t1_variation            JSON         NULL   COMMENT 'Existing Shopee tier 1 options e.g. ["Red","Blue"] (from Shopee API)' AFTER tier_name_1,
  ADD COLUMN tier_name_2             VARCHAR(100) NULL   COMMENT 'Existing Shopee tier 2 name e.g. Size (from Shopee API)' AFTER t1_variation,
  ADD COLUMN t2_variation            JSON         NULL   COMMENT 'Existing Shopee tier 2 options e.g. ["S","M","L"] (from Shopee API)' AFTER tier_name_2;
```

### Step 1.3 — Verify schema
```sql
DESCRIBE requestDatabase.shopee_listing_products;
-- Confirm 7 new columns exist after n8n_supporting_image
```

**Columns added** (all NULL-able, only populated for `item_type = 'new_variation'`):

| Column | Type | Source | Purpose |
|---|---|---|---|
| `shopee_product_name` | VARCHAR(500) | Shopee API | Our existing listing title |
| `shopee_description` | LONGTEXT | Shopee API | Our existing listing description |
| `shopee_variation_images` | JSON | Shopee API | Existing tier-1 variation image URLs |
| `tier_name_1` | VARCHAR(100) | Shopee API | First tier name (e.g. "Colour") |
| `t1_variation` | JSON | Shopee API | First tier options (e.g. ["Red","Blue"]) |
| `tier_name_2` | VARCHAR(100) | Shopee API | Second tier name (e.g. "Size") |
| `t2_variation` | JSON | Shopee API | Second tier options (e.g. ["S","M","L"]) |

**Acceptance**: `DESCRIBE` shows all 7 new columns. No data loss. Frontend still works (columns are NULL, no breaking change).

**Dependencies**: None — this is the first phase.

---

## Phase 2: Migrate Existing Data

**Objective**: Copy the 12 rows of valid data from `shopee_existing_listing` into the normalized tables so nothing is lost.

### Step 2.1 — Migrate Shopee API data (shopee_product_name, description, tiers)

For items that exist in BOTH `shopee_existing_listing` AND `shopee_listing_products`:

```sql
UPDATE requestDatabase.shopee_listing_products slp
INNER JOIN requestDatabase.shopee_existing_listing sel
  ON slp.product_id = sel.product_id
SET
  slp.shopee_product_name     = sel.shopee_product_name,
  slp.shopee_description      = sel.shopee_description,
  slp.shopee_variation_images = sel.shopee_variation_images,
  slp.tier_name_1             = sel.tier_name_1,
  slp.t1_variation            = sel.t1_variation,
  slp.tier_name_2             = sel.tier_name_2,
  slp.t2_variation            = sel.t2_variation
WHERE sel.shopee_product_name IS NOT NULL;
```

### Step 2.2 — Migrate 1688 description images

For items in `shopee_existing_listing` that have 1688 description images but the normalized table doesn't:

```sql
UPDATE requestDatabase.shopee_listing_products slp
INNER JOIN requestDatabase.shopee_existing_listing sel
  ON slp.product_id = sel.product_id
SET
  slp.`1688_product_description_image` = sel.`1688_description_images`
WHERE slp.`1688_product_description_image` IS NULL
  AND sel.`1688_description_images` IS NOT NULL;
```

### Step 2.3 — Verify migration
```sql
-- Check Shopee data was copied
SELECT product_id, shopee_product_name, tier_name_1
FROM requestDatabase.shopee_listing_products
WHERE shopee_product_name IS NOT NULL;

-- Should return the same products that had Shopee data in shopee_existing_listing
```

### Step 2.4 — Handle items in `shopee_existing_listing` but NOT in `shopee_listing_products`

Check which `shopee_existing_listing` product_ids are missing from the normalized table:

```sql
SELECT sel.product_id, sel.shop_name, sel.`1688_product_name`
FROM requestDatabase.shopee_existing_listing sel
LEFT JOIN requestDatabase.shopee_listing_products slp ON sel.product_id = slp.product_id
WHERE slp.product_id IS NULL;
```

For any results: these items need product rows created in `shopee_listing_products` first, then variations in `shopee_listing_variations`. This will be handled by the updated scripts (Phase 3) — OR can be done manually with INSERT statements if there are only a few.

**Acceptance**: All Shopee data from `shopee_existing_listing` is now in `shopee_listing_products`. Verified with SELECT queries.

**Dependencies**: Phase 1 (columns must exist).

---

## Phase 3: Update Python Scripts

**Objective**: Redirect both scripts to write to the normalized tables instead of `shopee_existing_listing`.

### Step 3.1 — Update `1688_web_scrape_new_variation.py`

**File**: `eten-workspace/my_script/1688_web_scrape_new_variation.py`

**Changes needed:**

#### 3.1a — Change dedup query (reads)
```python
# BEFORE:
"SELECT product_id, `1688_url` FROM shopee_existing_listing WHERE `1688_url` IS NOT NULL"

# AFTER:
"SELECT product_id, `1688_url` FROM shopee_listing_products WHERE `1688_url` IS NOT NULL AND item_type = 'new_variation'"
```

#### 3.1b — Change the write function (`update_existing_listing` → `upsert_normalized_tables`)

**BEFORE** — single INSERT into flat table:
```python
INSERT INTO shopee_existing_listing
    (product_id, 1688_url, 1688_product_name, 1688_variation,
     1688_variation_images, 1688_description_images, item_date, updated_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
ON DUPLICATE KEY UPDATE ...
```

**AFTER** — two-step write to normalized tables:

```python
def upsert_normalized_tables(cursor, product_id, url_1688, product_name,
                              variation_names, variation_imgs, description_imgs,
                              item_date, launch_type='New Variation'):
    """
    Step 1: Upsert product-level row in shopee_listing_products.
    Step 2: Upsert variation rows in shopee_listing_variations (one per variation).
    """

    # --- Step 1: Product row ---
    cursor.execute("""
        INSERT INTO shopee_listing_products
            (product_id, launch_type, item_type, `1688_url`, `1688_product_name`,
             `1688_product_description_image`, item_date, status, created_at, updated_at)
        VALUES (%s, %s, 'new_variation', %s, %s, %s, %s, 'bot', NOW(), NOW())
        ON DUPLICATE KEY UPDATE
            `1688_url` = VALUES(`1688_url`),
            `1688_product_name` = VALUES(`1688_product_name`),
            `1688_product_description_image` = VALUES(`1688_product_description_image`),
            item_date = COALESCE(item_date, VALUES(item_date)),
            updated_at = NOW()
    """, (
        product_id,
        launch_type,
        url_1688,
        product_name,
        json.dumps(description_imgs, ensure_ascii=False) if description_imgs else None,
        item_date
    ))

    # --- Step 2: Variation rows ---
    # Delete existing variations for this product (clean re-insert)
    cursor.execute("""
        DELETE FROM shopee_listing_variations WHERE product_id = %s
    """, (product_id,))

    # Insert one row per variation
    if variation_names:
        for idx, var_name in enumerate(variation_names):
            var_img = variation_imgs[idx] if idx < len(variation_imgs) else None
            cursor.execute("""
                INSERT INTO shopee_listing_variations
                    (product_id, sort_order, `1688_variation`, `1688_variation_image`,
                     created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (
                product_id,
                idx,
                var_name,    # individual string, NOT JSON array
                var_img      # individual URL, NOT JSON array
            ))
```

**Key transformations:**
- `1688_variation`: Was JSON array `["A","B","C"]` → Now individual strings, one per row
- `1688_variation_images`: Was JSON array `["url1","url2"]` → Now individual URLs, one per row
- `1688_description_images`: Maps to `1688_product_description_image` (same data, different column name)
- `sort_order`: Uses the array index (0, 1, 2...) to preserve variation ordering

#### 3.1c — Region detection (optional enhancement)

Add a shop-to-region mapping to auto-populate the `region` column:

```python
SHOP_REGION_MAP = {
    'BahEmas': 'MY', 'ValueSnap': 'MY', 'MurahYa': 'MY',
    'das.nature2': 'MY', 'Hiranai': 'MY',
    # SG shops:
    'BahEmas_SG': 'SG',  # add SG shops as needed
}
```

### Step 3.2 — Update `shopee_api.py`

**File**: `eten-workspace/my_script/shopee_api.py`

**Changes needed:**

#### 3.2a — Change the write function (`save_to_db`)

**BEFORE:**
```python
UPDATE shopee_existing_listing
SET shop_name = %s, shopee_product_name = %s, shopee_description = %s,
    tier_name_1 = %s, t1_variation = %s, shopee_variation_images = %s,
    tier_name_2 = %s, t2_variation = %s
WHERE product_id = %s
```

**AFTER:**
```python
UPDATE shopee_listing_products
SET shopee_product_name = %s, shopee_description = %s,
    shopee_variation_images = %s,
    tier_name_1 = %s, t1_variation = %s,
    tier_name_2 = %s, t2_variation = %s,
    updated_at = NOW()
WHERE product_id = %s AND item_type = 'new_variation'
```

Note: `shop_name` is dropped from the UPDATE — it's already available via `new_items.shop` JOIN in the service layer.

#### 3.2b — Add fallback INSERT

Currently, if the row doesn't exist, the UPDATE silently skips. Add a fallback:

```python
cursor.execute(update_query, params)
if cursor.rowcount == 0:
    # Row doesn't exist yet — create it
    cursor.execute("""
        INSERT INTO shopee_listing_products
            (product_id, launch_type, item_type, status,
             shopee_product_name, shopee_description, shopee_variation_images,
             tier_name_1, t1_variation, tier_name_2, t2_variation,
             created_at, updated_at)
        VALUES (%s, 'New Variation', 'new_variation', 'bot',
                %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON DUPLICATE KEY UPDATE
            shopee_product_name = VALUES(shopee_product_name),
            shopee_description = VALUES(shopee_description),
            shopee_variation_images = VALUES(shopee_variation_images),
            tier_name_1 = VALUES(tier_name_1),
            t1_variation = VALUES(t1_variation),
            tier_name_2 = VALUES(tier_name_2),
            t2_variation = VALUES(t2_variation),
            updated_at = NOW()
    """, (product_id, ...))
    print(f"  Created new row for product_id={product_id}")
```

This ensures the Shopee API script can run independently of the 1688 scraper (either order works).

### Step 3.3 — Execution order going forward

Both scripts can now run in any order:
- **If 1688 scraper runs first**: Creates product + variation rows with 1688 data → Shopee API later fills in Shopee columns
- **If Shopee API runs first**: Creates product row with Shopee data → 1688 scraper later fills in 1688 columns + variation rows

**Acceptance**:
- Both scripts write to `shopee_listing_products` + `shopee_listing_variations`
- Neither script writes to `shopee_existing_listing`
- Test on one known product (e.g. product_id=10059817794, ValueSnap RC Truck) and verify data appears correctly in normalized tables
- Verify dedup works — re-running the script does not create duplicate rows

**Dependencies**: Phase 1 (schema), Phase 2 (migration).

---

## Phase 4: Update Backend Service Layer

**Objective**: Make the web app's backend read the new Shopee columns and include them in the n8n webhook payload for variation generation.

**Repo**: `it-awesomeree/awesomeree-web-app`
**Branch**: Create `feature/new-variation-shopee-data` from `main`

### Step 4.1 — Update type definitions

**File**: `lib/services/shopee-listings/types.ts`

Add to `ProductRow`:
```typescript
// Shopee existing listing data (populated for new_variation items)
shopee_product_name?: string | null
shopee_description?: string | null
shopee_variation_images?: string | string[] | null
tier_name_1?: string | null
t1_variation?: string | string[] | null
tier_name_2?: string | null
t2_variation?: string | null
```

Add to `ListingGeneratePayload` (for variation webhook):
```typescript
// Shopee existing data (for new_variation items only)
shopee_product_name?: string
shopee_description?: string
shopee_variation_images?: string[]
tier_name_1?: string
t1_variation?: string[]
tier_name_2?: string
t2_variation?: string[]
```

### Step 4.2 — Update normalizers

**File**: `lib/services/shopee-listings/normalizers.ts`

Add a function to build Shopee existing content:
```typescript
export function makeShopeeExistingContent(product: ProductRow): ListingContent | null {
  if (!product.shopee_product_name) return null
  return {
    productName: normalizeString(product.shopee_product_name),
    variation: '', // tier structure shown separately
    description: normalizeNullableString(product.shopee_description),
    variationImages: normalizeImageArray(product.shopee_variation_images),
  }
}

export function makeShopeeExistingTiers(product: ProductRow) {
  return {
    tierName1: normalizeNullableString(product.tier_name_1),
    t1Variation: normalizeStringArray(product.t1_variation),
    tierName2: normalizeNullableString(product.tier_name_2),
    t2Variation: normalizeStringArray(product.t2_variation),
  }
}
```

### Step 4.3 — Update `generate.ts` — Detail response

**File**: `lib/services/shopee-listings/generate.ts`

In `fetchShopeeListingDetail()`, add Shopee existing data to the response:

```typescript
// After building supplier/optimized content...
const shopeeExisting = product.item_type === 'new_variation'
  ? makeShopeeExistingContent(product)
  : null

const shopeeExistingTiers = product.item_type === 'new_variation'
  ? makeShopeeExistingTiers(product)
  : null

// Include in returned detail object:
return {
  ...existingDetailFields,
  shopeeExisting,
  shopeeExistingTiers,
}
```

### Step 4.4 — Update `generate.ts` — Webhook payload builder

**File**: `lib/services/shopee-listings/generate.ts`

In `generateShopeeListingForProduct()`, when building the n8n webhook payload for `new_variation` items, include the Shopee fields:

```typescript
const payload: ListingGeneratePayload = {
  product_id: productId,
  product_name_1688: normalizeString(product['1688_product_name']),
  description_1688: normalizeString(product['1688_product_description_text']),
  // ... existing fields ...
}

// Add Shopee existing data for variation items
if (product.item_type === 'new_variation') {
  payload.shopee_product_name = normalizeString(product.shopee_product_name)
  payload.shopee_description = normalizeString(product.shopee_description)
  payload.shopee_variation_images = normalizeImageArray(product.shopee_variation_images)
  payload.tier_name_1 = normalizeNullableString(product.tier_name_1) ?? undefined
  payload.t1_variation = normalizeStringArray(product.t1_variation)
  payload.tier_name_2 = normalizeNullableString(product.tier_name_2) ?? undefined
  payload.t2_variation = normalizeStringArray(product.t2_variation)
}
```

### Step 4.5 — Update `generate.ts` — Summary response

**File**: `lib/services/shopee-listings/generate.ts`

In `fetchShopeeListingSummary()`, the summary already returns enough data (product name, variation count, n8n status). No changes needed for the list view — Shopee data is only relevant in the detail panel.

### Step 4.6 — Update frontend types

**File**: `types/shopee-listing.ts`

Add to `ListingProductDetail`:
```typescript
shopeeExisting?: ListingContent | null
shopeeExistingTiers?: {
  tierName1: string | null
  t1Variation: string[]
  tierName2: string | null
  t2Variation: string[]
} | null
```

**Acceptance**:
- `GET /api/shopee-listings?productId=9193675690` returns `shopeeExisting` and `shopeeExistingTiers` fields
- `POST /api/shopee-listings/generate` for a `new_variation` item includes Shopee fields in the n8n webhook payload
- No regressions for `new_product` items (Shopee fields are null/omitted)

**Dependencies**: Phase 1 (schema), Phase 2 (data).

---

## Phase 5: Update Frontend

**Objective**: Display the Shopee existing listing data in the detail panel for New Variation items.

### Step 5.1 — Add "Shopee Existing" accordion section

**File**: `components/shopee-listing/page.tsx`

For `new_variation` items, add a 4th accordion section between "Supplier Data" and "Optimized / AI Output":

```
Accordion sections for new_variation items:
1. Supplier Data (amber)          — 1688 originals
2. Shopee Existing (green/teal)   — our current Shopee listing  ← NEW
3. Optimized / AI Output (indigo) — n8n generated
4. Competitors (rose)             — competitor listings
```

The "Shopee Existing" section shows:
- Product name (`shopeeExisting.productName`)
- Description (`shopeeExisting.description`)
- Variation images (`shopeeExisting.variationImages`) via `ImageGallery`
- Tier structure: `tier_name_1: [options]`, `tier_name_2: [options]` displayed as labeled tag lists

### Step 5.2 — Conditional rendering

Only show the "Shopee Existing" section when:
```typescript
{activeProduct?.itemType === 'new_variation' && activeProduct?.shopeeExisting && (
  <AccordionItem value="shopee-existing">
    {/* ... */}
  </AccordionItem>
)}
```

### Step 5.3 — Tier display component

Create a small inline component for displaying tier structure:

```typescript
function TierDisplay({ tierName, variations }: { tierName: string | null, variations: string[] }) {
  if (!tierName || !variations.length) return null
  return (
    <div>
      <span className="font-medium text-sm">{tierName}:</span>
      <div className="flex flex-wrap gap-1 mt-1">
        {variations.map((v, i) => (
          <span key={i} className="text-xs bg-muted px-2 py-0.5 rounded">{v}</span>
        ))}
      </div>
    </div>
  )
}
```

**Acceptance**:
- New Variation product detail shows "Shopee Existing" accordion with product name, description, images, and tier structure
- New Product items do NOT show this section
- Section gracefully handles missing data (shows nothing if Shopee data hasn't been fetched yet)

**Dependencies**: Phase 4 (API must return shopeeExisting data).

---

## Phase 6: Update n8n Workflows

**Objective**: Ensure the n8n variation generation workflow accepts and uses the new Shopee fields in the webhook payload.

### Step 6.1 — Update the Variation Generate webhook node

**Workflow**: Shopee Listing New Variation Generation
**Webhook URL**: `https://n8n.barndoguru.com/webhook/generate-variation-listing`

The webhook will now receive additional fields in the JSON body:
```json
{
  "product_id": "10059817794",
  "product_name_1688": "...",
  "variations_1688": ["新变体A", "新变体B"],
  "variation_images": ["https://...", "https://..."],
  "description_images": ["https://...", ...],
  "competitors": [...],
  "shop_name": "ValueSnap",
  "targets": ["all"],

  "shopee_product_name": "Kereta Control Mainan Rc Car ...",
  "shopee_description": "Full existing description...",
  "shopee_variation_images": ["https://...", ...],
  "tier_name_1": "Colour",
  "t1_variation": ["Red", "Blue", "Green"],
  "tier_name_2": "Size",
  "t2_variation": ["S", "M", "L"]
}
```

### Step 6.2 — Update GPT/AI prompt nodes

The LLM prompt nodes in the n8n workflow need to be updated to:
1. Reference `shopee_product_name` and `shopee_description` as context for the existing listing style
2. Use `tier_name_1` and `t1_variation` to understand the existing variation structure
3. Use `tier_name_2` and `t2_variation` if a second tier exists
4. Generate new variation names that are consistent with the existing tier naming convention

### Step 6.3 — Update Variation Regenerate webhook (same changes)

**Webhook URL**: `https://n8n.barndoguru.com/webhook/regenerate-variation-listing`

Same payload structure additions apply.

### Step 6.4 — Verify webhook response format

The n8n variation workflow must return output that the `normalizeWebhookOutput()` function can parse. Expected output fields:
- `n8n_variation` or `variation_names` — array of generated variation names
- `n8n_product_description` or `description` — generated description
- `n8n_variation_image` or `variation_images` — array of generated variation images

**Acceptance**:
- n8n workflow receives Shopee fields in the webhook payload
- AI prompts reference the Shopee existing data for context
- Webhook returns parseable output

**Dependencies**: Phase 4 (service layer sends the payload).

---

## Phase 7: End-to-End Testing

**Objective**: Verify the complete pipeline works from scraping through to frontend display.

### Step 7.1 — Test the 1688 variation scraper

1. Pick a known New Variation product (e.g. product_id=10059817794, RC Truck)
2. Run the updated `1688_web_scrape_new_variation.py`
3. Verify:
   - `shopee_listing_products` row has `1688_url`, `1688_product_name`, `1688_product_description_image` populated
   - `shopee_listing_variations` has one row per variation with correct `1688_variation` and `1688_variation_image`
   - `sort_order` is sequential (0, 1, 2...)
   - No data written to `shopee_existing_listing`
   - Re-running does NOT create duplicates (upsert works)

### Step 7.2 — Test the Shopee API script

1. Run `shopee_api.py` for the same product
2. Verify:
   - `shopee_listing_products` row now has `shopee_product_name`, `shopee_description`, `tier_name_1`, `t1_variation`, `shopee_variation_images` populated
   - No data written to `shopee_existing_listing`
   - If product row didn't exist, fallback INSERT created it

### Step 7.3 — Test the frontend detail view

1. Open `employee.awesomeree.com.my/inventory/shopee-listing`
2. Filter by Type = "New Variation"
3. Click the test product
4. Verify:
   - "Supplier Data" accordion shows 1688 data
   - "Shopee Existing" accordion shows Shopee product name, description, variation images, tier structure
   - "Optimized / AI Output" accordion is empty (n8n hasn't run yet)

### Step 7.4 — Test n8n generation

1. Click "Generate All" on the test product
2. Verify:
   - n8n webhook receives the full payload including Shopee fields
   - n8n processes successfully
   - Output is written back to `shopee_listing_products.n8n_product_description` and `shopee_listing_variations.n8n_variation` / `n8n_variation_image`
   - Frontend shows the AI output in the "Optimized / AI Output" accordion
   - n8n job status shows "completed"

### Step 7.5 — Regression test New Product flow

1. Pick a New Product item
2. Verify:
   - Summary page loads normally
   - Detail panel shows Supplier + Optimized + Competitors (no "Shopee Existing" section)
   - Generate/Regenerate still works
   - No errors in console

**Acceptance**: Complete flow works for both New Product and New Variation items.

---

## Phase 8: Cleanup & Deprecation

**Objective**: Remove dependencies on `shopee_existing_listing` and clean up legacy references.

### Step 8.1 — Stop writing to `shopee_existing_listing`

After Phase 7 passes, both scripts should no longer write to `shopee_existing_listing`. Verify by checking:
```sql
SELECT MAX(updated_at) FROM requestDatabase.shopee_existing_listing;
-- Should stop advancing after deployment
```

### Step 8.2 — Archive the table

```sql
RENAME TABLE requestDatabase.shopee_existing_listing
  TO requestDatabase.shopee_existing_listing_archived_20260225;
```

Do NOT drop it — keep as archive for reference.

### Step 8.3 — (Future, optional) Update 1688 New Product scraper

Lower priority. The `1688_web_scrape_new_product.py` currently writes to `shopee_listings` (legacy). The existing sync process handles the copy to normalized tables. This works, so changing it is optional but reduces technical debt if done:
- Change dedup query to check `shopee_listing_products` instead of `shopee_listings`
- Change INSERT to write to `shopee_listing_products` + `shopee_listing_variations` directly
- Same pattern as the variation scraper changes in Phase 3

### Step 8.4 — Update planning doc

Update this document with completion status and any changes made during implementation.

---

# PART C — EXECUTION CHECKLIST

| # | Phase | Step | Status | Owner |
|---|---|---|---|---|
| 0.1 | Prep | Back up tables | TODO | |
| 0.2 | Prep | Verify FK constraint | DONE | |
| 0.3 | Prep | Verify unique index | DONE | |
| 1.1 | Schema | ALTER on webapp_test | TODO | |
| 1.2 | Schema | ALTER on requestDatabase | TODO | |
| 1.3 | Schema | Verify DESCRIBE | TODO | |
| 2.1 | Migrate | Copy Shopee data to normalized | TODO | |
| 2.2 | Migrate | Copy 1688 desc images | TODO | |
| 2.3 | Migrate | Verify migration | TODO | |
| 2.4 | Migrate | Handle orphan items | TODO | |
| 3.1 | Scripts | Update 1688 variation scraper | TODO | |
| 3.2 | Scripts | Update Shopee API script | TODO | |
| 3.3 | Scripts | Test script execution order | TODO | |
| 4.1 | Backend | Update types.ts | TODO | |
| 4.2 | Backend | Update normalizers.ts | TODO | |
| 4.3 | Backend | Update generate.ts — detail | TODO | |
| 4.4 | Backend | Update generate.ts — webhook payload | TODO | |
| 4.5 | Backend | Verify summary (no change needed) | TODO | |
| 4.6 | Backend | Update frontend types | TODO | |
| 5.1 | Frontend | Add Shopee Existing accordion | TODO | |
| 5.2 | Frontend | Conditional rendering | TODO | |
| 5.3 | Frontend | Tier display component | TODO | |
| 6.1 | n8n | Update variation generate webhook | TODO | |
| 6.2 | n8n | Update AI prompt nodes | TODO | |
| 6.3 | n8n | Update variation regenerate webhook | TODO | |
| 6.4 | n8n | Verify webhook response format | TODO | |
| 7.1 | Test | 1688 variation scraper E2E | TODO | |
| 7.2 | Test | Shopee API script E2E | TODO | |
| 7.3 | Test | Frontend detail view | TODO | |
| 7.4 | Test | n8n generation E2E | TODO | |
| 7.5 | Test | Regression — New Product flow | TODO | |
| 8.1 | Cleanup | Verify no writes to old table | TODO | |
| 8.2 | Cleanup | Archive shopee_existing_listing | TODO | |
| 8.3 | Cleanup | (Optional) Update new product scraper | TODO | |
| 8.4 | Cleanup | Update this doc | TODO | |

---

# PART D — REFERENCE

## D1. File Structure (awesomeree-web-app)

### Route
```
app/inventory/shopee-listing/page.tsx → <ShopeeListingPage />
```

### Components
```
components/shopee-listing/
  page.tsx (72KB), FilterBar.tsx, ActivityPanel.tsx, ComparisonDialog.tsx,
  GenerateConfirmDialog.tsx, TemplateLibraryDialog.tsx, AuditHintTooltip.tsx,
  ErrorBoundary.tsx, sub-components.tsx, utils.ts
```

### Hooks
```
components/shopee-listing/hooks/
  useProductList.ts, useProductDetail.ts, useGenerateFlow.ts,
  useFilterState.ts, useActivityLog.ts, useActionAudit.ts, useDebounce.ts
```

### API Routes
```
app/api/shopee-listings/route.ts          — GET summary/detail
app/api/shopee-listings/generate/route.ts — POST trigger n8n
app/api/shopee-listings/staging/route.ts  — POST approve/reject
app/api/shopee-listings/templates/route.ts — GET/POST templates
```

### Service Layer
```
lib/services/shopee-listings/
  index.ts, generate.ts (45KB), db.ts, staging.ts,
  n8n-webhook.ts, job-tracker.ts, normalizers.ts (38KB), types.ts
```

## D2. n8n Webhooks

| Flow | URL |
|---|---|
| Generate (new_product) | `/webhook/generate-listing` |
| Regenerate (new_product) | `/webhook/regenerate-listing` |
| Generate (new_variation) | `/webhook/generate-variation-listing` |
| Regenerate (new_variation) | `/webhook/regenerate-variation-listing` |

## D3. Key Design Patterns

- **Single-job mutex**: Only one product generating at a time (FOR UPDATE locking)
- **Stale job recovery**: Jobs > 45 min auto-failed
- **Variation count fallback**: Falls back to `new_items.variation_list_en` when no variation rows
- **Regeneration staging**: Regen output goes to `shopee_listing_reviews`, requires approve/reject
- **Connection-per-query**: Each DB operation opens/closes its own connection
