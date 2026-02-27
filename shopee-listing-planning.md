# Shopee Listing Pipeline - Schema Redesign Plan

> **Last updated**: 2026-02-27
> **Status**: Phase 5 in progress (scrapers running). Additional fixes deployed (524 timeout, Has Binary?, staging consistency).
> **Author**: Eten (IT Team Lead) + Claude (Senior Dev)

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Investigation Findings](#investigation-findings)
3. [The Two Workflows (New Product vs New Variation)](#the-two-workflows)
4. [Why Current Schema Cannot Work](#why-current-schema-cannot-work)
5. [Solution: `new_item_id` as Unique Key](#solution-new_item_id-as-unique-key)
6. [Proof: Isolation Walkthrough](#proof-isolation-walkthrough)
7. [Current Database Schema](#current-database-schema)
8. [Migration SQL (Step-by-Step)](#migration-sql-step-by-step)
9. [Code Changes Required](#code-changes-required)
10. [Implementation Order](#implementation-order)
11. [Verification Checklist](#verification-checklist)

---

## Problem Statement

The same Shopee `product_id` can have multiple listing events in `new_items`:
- Multiple **New Product** events (re-submissions, different suppliers)
- Multiple **New Variation** events (adding different variations over time)
- Both **New Product** AND **New Variation** events for the same product

Current schema uses `UNIQUE(product_id)` on `shopee_listing_products`, so **only ONE row exists per product_id**. Whichever scraper runs last overwrites the other's data. This causes:
1. **Data corruption** - New Product 1688 data mixed with New Variation Shopee data
2. **Missing variations** - New variation's actual 1688 variations are overwritten by new product's variations
3. **Wrong display** - Frontend shows wrong data (e.g., 3 new_product variations when user clicks new_variation row)
4. **Impossible generation** - Cannot generate correct n8n output because input data is mixed

---

## Investigation Findings

### Database counts (as of 2026-02-25)

| Metric | Count |
|---|---|
| `new_items` total rows | **565** |
| `new_items` unique product_ids | **447** |
| `new_items` launch_type = New Product | **469** |
| `new_items` launch_type = New Variation | **94** |
| `new_items` launch_type = New Product (SG) | **2** |
| `shopee_listing_products` total rows | **331** |
| `shopee_listing_products` item_type = new_product | **304** |
| `shopee_listing_products` item_type = new_variation | **27** |
| `shopee_listing_variations` total rows | **1940** |

### Collision analysis

| Collision Type | Count | Impact |
|---|---|---|
| Product_ids with BOTH new_product + new_variation | **28** | Data overwritten between workflows |
| Product_ids with multiple new_variation events | **8** (18 total events) | New variation events overwrite each other |
| Product_ids with multiple new_product events | **48** | New product events overwrite each other |
| Product_ids with item_type mismatch in DB | **~20** | DB says new_variation but 1688 data is from new_product scraper (or vice versa) |

### The 8 product_ids with multiple new_variation events

| product_id | Number of New Variation events |
|---|---|
| 28079888416 | 3 |
| 22581507419 | 3 |
| 8390619505 | 2 |
| 18880804735 | 2 |
| 10059817794 | 2 |
| 22055995385 | 2 |
| 25507762456 | 2 |
| 27789585481 | 2 |

Each of these needs **separate isolated rows** for each new_variation event. `UNIQUE(product_id, item_type)` would NOT solve this.

### Case study: product_id 9193675690

**What's in `new_items`:**

| new_items.id | launch_type | product_name_en | date |
|---|---|---|---|
| 397 | New Product | Manual Glue Gun (NEW) | 2025-09-29 |
| 429 | New Product | Toilet Cleaner | 2025-10-06 |
| 485 | New Variation | Expanding Foam | 2025-10-22 |

**What's in `shopee_listing_products` (1 row only due to UNIQUE):**
- `id=3`, `item_type=new_variation`, `launch_type=New Product` (contradicts itself!)
- `1688_product_name` = "手动玻璃胶枪..." (Glue Gun from ni=397, NOT expanding foam)
- `1688_hero` = Glue gun image
- `shopee_product_name` = "Vira PU Foam Spray..." (Shopee API data for the actual product)
- `shopee_description` = Full PU Foam description (correct Shopee data)

**What's in `shopee_listing_variations` (3 rows):**
- `id=10`: "发泡胶枪塑料橙色一件40把" (foam gun - from new_product scraper ni=397)
- `id=11`: "蓝瓶" (blue bottle - from new_product scraper)
- `id=12`: "粉瓶" (pink bottle - from new_product scraper)

**What's MISSING:**
- The actual new variation "900g/750ml加强" is NOT in `shopee_listing_variations`
- No separate rows for ni=397 (Glue Gun) and ni=429 (Toilet Cleaner)
- 1688 data, Shopee data, and variations are all mixed into one row

---

## The Two Workflows

### New Product (generate a full new Shopee listing)

**Purpose**: Create a brand new Shopee product listing from scratch using a 1688 source.

**Input (1688 scraper → `shopee_listing_products` + `shopee_listing_variations`):**
- `1688_url`, `1688_product_name`, `1688_product_description_text`
- `1688_product_description_image`, `1688_hero`, `1688_supporting_image`
- Per variation: `1688_variation`, `1688_variation_image`

**Reference data**: Competitor data from `Shopee_Comp` table

**n8n Output (6 fields):**
| Output Field | Level | DB Column |
|---|---|---|
| `n8n_product_name` | Product | `products.n8n_product_name` |
| `n8n_product_description` | Product | `products.n8n_product_description` |
| `n8n_hero` | Product | `products.n8n_hero` |
| `n8n_supporting_image` | Product | `products.n8n_supporting_image` |
| `n8n_variation` | Per-variation | `variations.n8n_variation` |
| `n8n_variation_image` | Per-variation | `variations.n8n_variation_image` |

### New Variation (add variations to an EXISTING Shopee product)

**Purpose**: Add new variations to a product that already exists on Shopee.

**Input (1688 scraper + Shopee API → `shopee_listing_products` + `shopee_listing_variations`):**
- `1688_url`, `1688_product_name` (the new 1688 source for variations)
- Per variation: `1688_variation`, `1688_variation_image` (new variations from 1688)
- `shopee_product_name`, `shopee_description` (existing Shopee product data)
- `shopee_variation_images` (existing variation images on Shopee)
- `tier_name_1`, `t1_variation`, `tier_name_2`, `t2_variation` (existing tier structure)

**Reference data**: **NONE** (no competitors - uses own Shopee data + 1688 data only)

**n8n Output (3 fields):**
| Output Field | Level | DB Column |
|---|---|---|
| `n8n_variation` | Per-variation | `variations.n8n_variation` |
| `n8n_product_description` | Product | `products.n8n_product_description` |
| `n8n_variation_image` | Per-variation | `variations.n8n_variation_image` |

**NOT output by new_variation n8n**: `n8n_product_name`, `n8n_hero`, `n8n_supporting_image` (stay NULL)

### Summary: Why they MUST be separate rows

| Aspect | New Product | New Variation |
|---|---|---|
| 1688 data | Full product (hero, desc, supporting images) | Only variations from 1688 |
| Shopee data | None (doesn't exist on Shopee yet) | Existing product (name, desc, tier variations) |
| Competitor data | YES (from Shopee_Comp) | NO |
| n8n outputs | 6 fields | 3 fields |
| Can repeat? | Yes (different suppliers for same product) | Yes (add more variations later) |

If they share one row, the 1688 data from new_product would overwrite the Shopee data needed for new_variation (and vice versa). The n8n generation would receive garbage mixed input.

---

## Why Current Schema Cannot Work

### Problem 1: `UNIQUE(product_id)` allows only 1 row

product_id 9193675690 has 3 events but only 1 row in `shopee_listing_products`. The last scraper to run overwrites the others.

### Problem 2: `UNIQUE(product_id, item_type)` still collides

Even if we allowed 2 rows per product_id (one per type), the 8 product_ids with multiple new_variation events would still collide. Example: product_id 28079888416 has **3** New Variation events - they'd all fight for the same `(28079888416, 'new_variation')` row.

### Problem 3: Variations link by `product_id` only

`shopee_listing_variations` has `product_id` as the join key. All events for the same product_id share the same set of variations. There's no way to say "these 3 variations belong to new_product event #397" vs "this 1 variation belongs to new_variation event #485".

---

## Solution: `new_item_id` as Unique Key

### Core idea

Each `new_items.id` represents **one unique listing event**. The scraped data (1688 + Shopee API) and the n8n output should be linked to this specific event, not to the product_id.

### Schema change

```
shopee_listing_products:  UNIQUE(product_id)  →  UNIQUE(new_item_id)
shopee_listing_variations: FK(product_id)     →  INDEX(new_item_id)
```

Both tables get a new column `new_item_id BIGINT NOT NULL` that references `new_items.id`.

### What stays the same

- `product_id` column stays (for reference/display), but is no longer unique
- All existing columns stay (1688_*, shopee_*, n8n_*, etc.)
- The columns work for both workflows - the difference is which get populated

---

## Proof: Isolation Walkthrough

### After migration, product_id 9193675690 will have:

**`shopee_listing_products` (3 rows):**

| new_item_id | product_id | item_type | 1688_product_name | shopee_product_name | n8n_product_name |
|---|---|---|---|---|---|
| 397 | 9193675690 | new_product | 手动玻璃胶枪... (Glue Gun) | NULL | (from n8n) |
| 429 | 9193675690 | new_product | (Toilet Cleaner 1688 data) | NULL | (from n8n) |
| 485 | 9193675690 | new_variation | (Expanding Foam 1688 data) | Vira PU Foam Spray... | NULL (not generated) |

**`shopee_listing_variations`:**

| new_item_id | 1688_variation | n8n_variation |
|---|---|---|
| 397 | 发泡胶枪塑料橙色... | (from n8n) |
| 397 | 蓝瓶 | (from n8n) |
| 397 | 粉瓶 | (from n8n) |
| 429 | (Toilet Cleaner variations) | (from n8n) |
| 485 | 900g/750ml加强 | (from n8n) |

### Isolation proof:

1. **Click "New Product" row (ni=397, Glue Gun)** →
   - Fetch `shopee_listing_products WHERE new_item_id = 397` → Gets glue gun 1688 data
   - Fetch `shopee_listing_variations WHERE new_item_id = 397` → Gets 3 glue gun variations
   - Fetch competitors from Shopee_Comp → Shows competitor data
   - Generate → Sends 6 fields to n8n

2. **Click "New Product" row (ni=429, Toilet Cleaner)** →
   - Fetch `WHERE new_item_id = 429` → Gets toilet cleaner data (completely separate)
   - Different 1688 data, different variations

3. **Click "New Variation" row (ni=485, Expanding Foam)** →
   - Fetch `WHERE new_item_id = 485` → Gets expanding foam 1688 data + Shopee data
   - Fetch variations `WHERE new_item_id = 485` → Gets ONLY "900g/750ml加强" (1 variation)
   - NO competitor fetch (it's a new_variation)
   - Generate → Sends only 3 fields to n8n

### Multiple new_variation events (e.g., product_id 28079888416 with 3):

Each new_variation event gets its own row. Event #1 might add color variations, event #2 adds size variations, event #3 adds material variations. They are completely isolated - different 1688 sources, different variations, different n8n outputs.

---

## Current Database Schema

### `shopee_listing_products` (331 rows)

| Column | Type | Nullable | Key |
|---|---|---|---|
| id | bigint unsigned | NO | PK, auto_increment |
| product_id | bigint | NO | **UNIQUE (uk_product_id)** |
| launch_type | varchar(50) | NO | |
| region | varchar(10) | YES | INDEX |
| item_type | enum('new_product','new_variation') | YES | INDEX |
| item_date | date | YES | |
| status | varchar(50) | YES | |
| 1688_url | text | YES | |
| 1688_product_name | varchar(512) | YES | |
| 1688_product_description_text | longtext | YES | |
| 1688_product_description_image | json | YES | |
| 1688_hero | text | YES | |
| 1688_supporting_image | json | YES | |
| n8n_product_name | varchar(512) | YES | |
| n8n_product_description | longtext | YES | |
| n8n_hero | text | YES | |
| n8n_supporting_image | json | YES | |
| shopee_product_name | varchar(500) | YES | |
| shopee_description | longtext | YES | |
| shopee_variation_images | json | YES | |
| tier_name_1 | varchar(100) | YES | |
| t1_variation | json | YES | |
| tier_name_2 | varchar(100) | YES | |
| t2_variation | json | YES | |
| n8n_job_status | varchar(20) | YES | INDEX (idx_job_status, idx_job_queue) |
| n8n_job_type | varchar(20) | YES | |
| n8n_job_targets | json | YES | |
| n8n_requested_by | varchar(255) | YES | |
| n8n_requested_at | datetime | YES | INDEX (idx_job_queue) |
| n8n_started_at | datetime | YES | |
| n8n_completed_at | datetime | YES | |
| n8n_error | text | YES | |
| created_at | datetime | NO | DEFAULT CURRENT_TIMESTAMP |
| updated_at | datetime | NO | DEFAULT CURRENT_TIMESTAMP ON UPDATE |

**Indexes**: PRIMARY(id), uk_product_id(product_id), idx_item_type, idx_region, idx_job_status, idx_job_queue(n8n_job_status, n8n_requested_at)

### `shopee_listing_variations` (1940 rows)

| Column | Type | Nullable | Key |
|---|---|---|---|
| id | bigint unsigned | NO | PK, auto_increment |
| product_id | bigint | NO | FK → products.product_id, INDEX |
| sort_order | smallint unsigned | NO | |
| 1688_variation | varchar(255) | YES | |
| 1688_variation_image | text | YES | |
| n8n_variation | varchar(255) | YES | |
| n8n_variation_image | text | YES | |
| created_at | datetime | NO | DEFAULT CURRENT_TIMESTAMP |
| updated_at | datetime | NO | DEFAULT CURRENT_TIMESTAMP ON UPDATE |

**Indexes**: PRIMARY(id), idx_product_id(product_id)
**FK**: fk_variation_product → shopee_listing_products.product_id

---

## Migration SQL (Step-by-Step)

### Step 1: Add `new_item_id` column

```sql
-- 1a. Add new_item_id to products table
ALTER TABLE requestDatabase.shopee_listing_products
  ADD COLUMN new_item_id BIGINT NULL AFTER id;

-- 1b. Add new_item_id to variations table
ALTER TABLE requestDatabase.shopee_listing_variations
  ADD COLUMN new_item_id BIGINT NULL AFTER product_id;
```

### Step 2: Backfill `new_item_id` for existing rows

For each existing `shopee_listing_products` row, find the best matching `new_items` row by product_id + item_type, picking the most recent one.

```sql
-- 2a. Backfill products: match by product_id + item_type
UPDATE requestDatabase.shopee_listing_products p
SET p.new_item_id = (
  SELECT ni.id
  FROM requestDatabase.new_items ni
  WHERE CAST(ni.product_id AS CHAR) = CAST(p.product_id AS CHAR)
    AND (
      (p.item_type = 'new_product' AND ni.launch_type IN ('New Product', 'New Product (SG)'))
      OR (p.item_type = 'new_variation' AND ni.launch_type = 'New Variation')
    )
  ORDER BY ni.date DESC, ni.id DESC
  LIMIT 1
)
WHERE p.new_item_id IS NULL;

-- 2b. For rows where item_type doesn't have a matching launch_type,
--     just pick the most recent new_items row for that product_id
UPDATE requestDatabase.shopee_listing_products p
SET p.new_item_id = (
  SELECT ni.id
  FROM requestDatabase.new_items ni
  WHERE CAST(ni.product_id AS CHAR) = CAST(p.product_id AS CHAR)
  ORDER BY ni.date DESC, ni.id DESC
  LIMIT 1
)
WHERE p.new_item_id IS NULL;

-- 2c. Backfill variations: copy new_item_id from their parent product
UPDATE requestDatabase.shopee_listing_variations v
JOIN requestDatabase.shopee_listing_products p ON v.product_id = p.product_id
SET v.new_item_id = p.new_item_id
WHERE v.new_item_id IS NULL;
```

### Step 3: Verify backfill - check for orphans

```sql
-- Any products with no matching new_items?
SELECT p.id, p.product_id, p.item_type, p.new_item_id
FROM requestDatabase.shopee_listing_products p
WHERE p.new_item_id IS NULL;

-- Any variations with no new_item_id?
SELECT v.id, v.product_id, v.new_item_id
FROM requestDatabase.shopee_listing_variations v
WHERE v.new_item_id IS NULL;
```

If orphans exist: delete them (stale data with no source event).

### Step 4: Make `new_item_id` NOT NULL

```sql
ALTER TABLE requestDatabase.shopee_listing_products
  MODIFY COLUMN new_item_id BIGINT NOT NULL;

ALTER TABLE requestDatabase.shopee_listing_variations
  MODIFY COLUMN new_item_id BIGINT NOT NULL;
```

### Step 5: Switch constraints and indexes

```sql
-- 5a. Drop the old FK on variations (it references the old UNIQUE key on product_id)
ALTER TABLE requestDatabase.shopee_listing_variations
  DROP FOREIGN KEY fk_variation_product;

-- 5b. Drop old unique key on products, add new one + keep product_id as regular index
ALTER TABLE requestDatabase.shopee_listing_products
  DROP INDEX uk_product_id,
  ADD UNIQUE KEY uk_new_item (new_item_id),
  ADD INDEX idx_product_id (product_id);

-- 5c. Update variations index: add new_item_id index (keep product_id index too)
ALTER TABLE requestDatabase.shopee_listing_variations
  ADD INDEX idx_new_item (new_item_id);
```

**Note**: We intentionally do NOT add a new FK from variations to products on new_item_id, because the Python scripts do DELETE+INSERT on variations independently of the products UPSERT. A FK would complicate the write pattern. The index is sufficient for fast lookups.

### Step 6: Fix product_id 9193675690 (and similar conflicts)

After the migration, this product_id still has only 1 row (assigned to the most recent matching event). We need the scrapers to re-process the other events to create their rows.

```sql
-- Verify current state after migration
SELECT new_item_id, product_id, item_type, `1688_product_name`
FROM requestDatabase.shopee_listing_products
WHERE product_id = 9193675690;

-- The existing row will be assigned to one event.
-- The other 2 events (ni=397, 429, or 485) will get their rows
-- when the scrapers re-process them.
```

For now, the existing data stays with the best-matching event. The other events will have empty rows until re-scraped. This is correct behavior - we'd rather have no data than wrong/mixed data.

---

## Code Changes Required

### Python Scripts (1688 scrapers + Shopee API)

All 3 scripts already iterate over `new_items` rows, so they have `new_items.id` available. They just need to pass it through as the write key.

| Script | Current write key | New write key | Changes |
|---|---|---|---|
| `1688_web_scrape_new_product.py` | `product_id` | `new_item_id` | UPSERT products by `new_item_id`, DELETE+INSERT variations by `new_item_id` |
| `1688_web_scrape_new_variation.py` | `product_id` | `new_item_id` | UPSERT products by `new_item_id`, DELETE+INSERT variations by `new_item_id` |
| `shopee_api.py` | `product_id` | `new_item_id` | UPDATE products WHERE `new_item_id = ?` |

**Key changes in each script:**

1. **INSERT/UPSERT products**: Change `ON DUPLICATE KEY UPDATE` to use `new_item_id` (matches the new UNIQUE key)
2. **DELETE variations**: Change `DELETE FROM variations WHERE product_id = ?` to `WHERE new_item_id = ?`
3. **INSERT variations**: Include `new_item_id` in the INSERT columns
4. **SELECT checks**: Change any `WHERE product_id = ?` lookups to `WHERE new_item_id = ?`

### Webapp Backend (generate.ts)

| Function | Current | New |
|---|---|---|
| Summary builder | `productRowMap.get(productId)` | `productRowMap.get(newItemId)` - join products ON new_item_id |
| `fetchProduct()` | `WHERE product_id = ?` | `WHERE new_item_id = ?` |
| `fetchVariations()` | `WHERE product_id = ?` | `WHERE new_item_id = ?` |
| `buildGeneratePayload()` | fetch by product_id | fetch by new_item_id |
| `fetchShopeeListingDetail()` | fetch by product_id | fetch by new_item_id |

The summary already iterates over `new_items` rows (ni.id is available). The detail fetch currently uses `productId` - change to `newItemId`.

### Webapp Frontend (page.tsx + hooks)

| Component | Current | New |
|---|---|---|
| Summary row data | Has `productId` | Also include `newItemId` (from new_items.id) |
| Row click handler | `loadProductDetail(productId, itemType)` | `loadProductDetail(newItemId)` |
| Detail API call | `?productId=X&itemType=Y` | `?newItemId=X` |
| useProductDetail hook | `loadProductDetail(productId, itemType)` | `loadProductDetail(newItemId)` |

**Simplification**: Once we use `newItemId`, we no longer need the `itemType` parameter in the API call. The `new_item_id` uniquely identifies the event, and we can read `item_type` from the product row itself.

### API Route (route.ts)

```
GET /api/shopee-listings?newItemId=485
  → fetchShopeeListingDetail(newItemId=485)
  → Returns: product data + variations for this specific new_items event
```

---

## Implementation Order

### Phase 1: Database Migration ✅ COMPLETE (2026-02-25)
1. ~~Run Step 1-5 SQL above~~ — Done on both `requestDatabase` and `webapp_test`
2. ~~Verify with Step 3 queries~~ — Confirmed
3. ~~Confirm product_id 9193675690 has correct new_item_id assigned~~ — ni=397, 429, 485

### Phase 2: Python Scripts Update ✅ COMPLETE (2026-02-25)
1. ~~Update `1688_web_scrape_new_product.py` - UPSERT by new_item_id~~ — Done
2. ~~Update `1688_web_scrape_new_variation.py` - UPSERT by new_item_id~~ — Done
3. ~~Update `shopee_api.py` - UPDATE by new_item_id~~ — Done
4. ~~Push to `it-awesomeree/eten-workspace` main branch~~ — Pushed

### Phase 3: Webapp Backend Update ✅ COMPLETE (2026-02-25)
1. ~~Update summary builder in generate.ts - join products on new_item_id~~ — Done
2. ~~Update fetchShopeeListingDetail - query by new_item_id~~ — Done
3. ~~Update buildGeneratePayload - query by new_item_id~~ — Done
4. ~~Push to `it-awesomeree/awesomeree-web-app` test branch~~ — Pushed

### Phase 4: n8n Workflows Update ✅ COMPLETE (2026-02-25, fix 2026-02-26)
1. ~~Variation Generation (`_nYkX49YkTfTdwWTsDjM1`)~~ — Parse Webhook Data + Prepare MySQL Data updated to use new_item_id
2. ~~Product Generation (`6-RFpehM68nSiWt0uXbi8`)~~ — Parse Webhook Data + Prepare MySQL Data updated
3. ~~Variation Regeneration (`rKOMjD071lkvvZDe`)~~ — Prepare MySQL Data updated (regen → shopee_listing_reviews, normal → new_item_id)
4. ~~Product Regeneration (`M6wBk9TCuMohMByU`)~~ — Prepare MySQL Data updated (→ shopee_listing_reviews)
5. **Fix 2026-02-26**: Parse Webhook Data in Variation Generation was accidentally reverted; re-deployed via `fix-parse-webhook.mjs`

### Phase 4b: Webapp Frontend Update ✅ COMPLETE (2026-02-25)
1. ~~Include newItemId in summary row data~~ — Done
2. ~~Pass newItemId in row click handler~~ — Done
3. ~~Update useProductDetail hook to use newItemId~~ — Done
4. ~~Remove itemType parameter hack (no longer needed)~~ — Done
5. ~~Push to test branch~~ — Pushed

### Phase 5: Data Cleanup + Re-scrape 🔄 IN PROGRESS (2026-02-26)

**Step 1: Fix item_type mismatches** ✅ COMPLETE
- Ran UPDATE SQL on both `requestDatabase` and `webapp_test`
- Verified: 0 mismatches remaining

**Step 2: Delete corrupt collision data** ✅ COMPLETE
- Deleted product rows + variation rows for 63 collision product_ids
- Verified: 0 collision rows remaining
- Post-cleanup: 270 correct products (requestDatabase), 264 (webapp_test)

**Step 3: Re-run scrapers** 🔄 IN PROGRESS
- Scrapers already running (Phase 2 code active)
- Confirmed: product_id 9193675690 already has ni=429 (Toilet Cleaner, 2 vars) and ni=485 (Expanding Foam, 1 var) created correctly
- Awaiting: ni=397 (Glue Gun / New Product) + remaining ~283 events

**Step 4: Verification** ⏳ PENDING
- Run verification queries after scraper completion
- Expected: 0 missing events, 0 item_type mismatches, 555 total products

### Phase 5b: Additional Fixes (2026-02-27)

**Cloudflare 524 Gateway Timeout Fix** ✅ COMPLETE
- Webapp no longer marks job as FAILED when Cloudflare returns 524 (n8n still running behind proxy)
- Gateway timeout returns sentinel → job stays "processing" → auto-completion detects output on next page load
- Files: `n8n-webhook.ts`, `generate.ts`, `page.tsx`, `utils.ts` (on `test` branch)

**n8n Has Binary? Node Fix** ✅ COMPLETE
- `$binary` expression unreliable in Loop Over Items v3 + IF node v2 context
- Replaced with `$json.image_type !== "none"` — reliable across all node contexts
- Workflow: New Product Regen (`M6wBk9TCuMohMByU`)

**GCS Staging Consistency** ✅ COMPLETE
- New Variation Regen (`rKOMjD071lkvvZDe`) now uses `/staging/` prefix in regen mode (matching New Product Regen)
- Both regen workflows: `{productId}/staging/variations/...` for regen, `{productId}/variations/...` for normal

**Region Display Fix** ✅ COMPLETE
- Items with null `shop` column now default to "MY" region (matches New Items tab behavior)
- File: `generate.ts` — `deriveRegionFromShop` returns "MY" for null/undefined

### Phase 6: End-to-End Testing ⏳ PENDING
1. Verify product_id 9193675690: 3 separate rows, correct data isolation
2. Verify a multi-new-variation product (e.g., 28079888416): 3 isolated new_variation rows
3. Test n8n generate for new_product → 6 output fields
4. Test n8n generate for new_variation → 3 output fields
5. Verify no competitor data shown for new_variation events

---

## Verification Checklist

After full implementation, verify:

- [ ] `shopee_listing_products` has UNIQUE on `new_item_id` (not product_id)
- [ ] product_id 9193675690 has 3 separate rows (ni=397, 429, 485)
- [ ] ni=397 row: item_type=new_product, 1688 data = Glue Gun, no Shopee data
- [ ] ni=429 row: item_type=new_product, 1688 data = Toilet Cleaner, no Shopee data
- [ ] ni=485 row: item_type=new_variation, 1688 data = Expanding Foam, Shopee data present, 1 variation "900g/750ml加强"
- [ ] Clicking ni=397 row: shows competitors, shows 3 glue gun variations
- [ ] Clicking ni=485 row: shows Shopee data card (no competitors), shows 1 variation
- [ ] n8n generate for ni=397: sends product_name + desc + hero + supporting + variations (6 fields)
- [ ] n8n generate for ni=485: sends only desc + variations (3 fields, no product_name/hero/supporting)
- [ ] product_id 28079888416: 3 separate new_variation rows, each with own variations
- [ ] Multiple new_variation events for same product_id are fully isolated
- [ ] Python scrapers write to correct new_item_id (no product_id collision)
