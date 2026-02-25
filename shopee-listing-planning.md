# PROGRESS TRACKER — new_item_id Migration

> Last updated: 25 Feb 2026 (Session 2)

## The Problem

`shopee_listing_products` had `UNIQUE(product_id)`, causing data collisions when the same `product_id` appears in multiple `new_items` events (e.g., New Product + New Variation, or multiple New Variations for the same product). The `ON DUPLICATE KEY UPDATE` in the 1688 scraper would overwrite data from one event with another.

## The Solution

Add `new_item_id` column (references `new_items.id`) as the new unique key. Each `new_items` row gets its own `shopee_listing_products` row, identified by `new_item_id`.

---

## Phase 1: Schema Migration — DONE

### Migration 1: Add new_item_id column
- **File**: `migrations/request/20260225000001_add_new_item_id.sql`
- **Status**: Deployed to both `webapp_test` and `requestDatabase`
- Adds `new_item_id BIGINT NULL` to `shopee_listing_products` and `shopee_listing_variations`

### Migration 2: Switch unique constraint
- **File**: `migrations/request/20260225000002_switch_unique_to_new_item_id.sql`
- **Status**: Deployed to both `webapp_test` and `requestDatabase`
- Drops `fk_variation_product` and `fk_review_product` foreign keys
- Drops `UNIQUE(product_id)` → adds `INDEX(product_id)` (non-unique)
- Adds `UNIQUE(new_item_id)` on `shopee_listing_products`
- Adds `INDEX(new_item_id)` on `shopee_listing_variations`

### CI Pipeline Fix
- **File**: `.github/workflows/db-deploy.yml` (test branch only)
- Added **DATABASE 1c** step: applies `migrations/request` to `webapp_test` on test branch pushes
- Previously, `migrations/request` was only applied to `requestDatabase` on main branch pushes
- **TODO**: Merge this fix to main branch

### Backfill
- **Status**: Completed on both databases
- `requestDatabase`: 331 products, 1940 variations backfilled
- `webapp_test`: 323 products, 1940 variations backfilled
- Used `MAX(new_items.id)` per product_id to assign the most recent new_item event
- Zero NULLs remaining in `new_item_id` column

---

## Phase 2: Python Scripts (1688 scraper + Shopee API) — DONE

All 3 scripts updated and pushed to `main` branch in `it-awesomeree/eten-workspace`:

### `my_script/shopee_api.py`
- **Commit**: [6f1a315](https://github.com/it-awesomeree/eten-workspace/commit/6f1a3156f97892969b79f920072877cea8d9b876)
- `save_to_db()` now takes `new_item_id` parameter, uses `WHERE new_item_id = %s`
- `main()` builds `pid_to_items` mapping to handle multiple rows per product_id
- Uses `unique_product_ids` for Shopee API batches (avoids duplicate API calls)
- Save loop iterates matching items, passing `orig_item["row_id"]` (= `new_items.id`) as `new_item_id`

### `my_script/1688_web_scrape_new_product.py`
- **Commit**: [92d0f61](https://github.com/it-awesomeree/eten-workspace/commit/92d0f611fe353eced129d1d7e2567d638175989e)
- `get_product_names_from_db()` selects `ni.id`, dedup uses `ni.id NOT IN (SELECT new_item_id ...)`
- `insert_shopee_listings()` includes `new_item_id` in INSERT columns
- DELETE/INSERT on variations uses `WHERE new_item_id = %s`
- Call site unpacks and passes `new_item_id` from `ni.id`

### `my_script/1688_web_scrape_new_variation.py`
- **Commit**: [eb40b78](https://github.com/it-awesomeree/eten-workspace/commit/eb40b7891c9da3f70874ee9e83f3bca1f409301e)
- Dedup check queries `(new_item_id, 1688_url)` pairs instead of `(product_id, 1688_url)`
- `update_existing_listing()` takes `new_item_id` parameter
- INSERT/DELETE on both tables uses `new_item_id`
- Call site passes `ni_id` from `new_items.id`

### Deploy to VM
- **TODO**: Pull updated scripts on the VM where they run

---

## Phase 3: Webapp Backend — TODO (next session)

### Repo: `it-awesomeree/awesomeree-web-app` → `test` branch

The webapp currently uses `product_id` everywhere as the unique key to look up rows. Since `product_id` is no longer unique, ALL lookups must change to `new_item_id`.

### Research completed — here's what needs to change:

#### `lib/services/shopee-listings/types.ts`
- Add `new_item_id?: number | string | null` to `ProductRow` interface
- Add `new_item_id?: number | string | null` to `VariationRow` interface

#### `lib/services/shopee-listings/generate.ts` (48KB, 1454 lines — the big one)

| Function | Current SQL | Change to |
|----------|-------------|-----------|
| `fetchProduct(productId)` | `WHERE product_id = ?` | `WHERE new_item_id = ?` |
| `fetchVariations(productId)` | `WHERE product_id = ?` | `WHERE new_item_id = ?` |
| `fetchShopeeListingSummary()` | Product map keyed by `product_id` | Key by `new_item_id`. Lookup by `ni.id` instead of `ni.product_id` |
| `fetchShopeeListingDetail(productId)` | `WHERE product_id = ?` | `WHERE new_item_id = ?` |
| `applyGeneratedFields` | `UPDATE ... WHERE product_id = ?` | `UPDATE ... WHERE new_item_id = ?` |
| `buildGeneratePayload` | `SELECT shop FROM new_items WHERE product_id = ?` | `SELECT shop FROM new_items WHERE id = ?` |
| `fetchLatestPendingReviewRow` | `WHERE product_id = ?` | `WHERE new_item_id = ?` |
| `fetchPendingReviewRowsForProducts` | `WHERE product_id IN (...)` | `WHERE new_item_id IN (...)` |
| `fetchAllProducts` | ORDER BY product_id | Keep (no change needed) |
| `fetchAllVariations` | ORDER BY product_id | Keep (no change needed) |
| Competitor queries | `our_item_id` = Shopee product_id | Keep (competitors are per Shopee product, not per listing event) |

**Summary view map building** (critical change):
```
// OLD: Map<product_id, ProductRow>
productMap.set(String(p.product_id), p)
// NEW: Map<new_item_id, ProductRow>
productMap.set(String(p.new_item_id), p)

// OLD: lookup
productMap.get(String(ni.product_id))
// NEW: lookup by new_items.id
productMap.get(String(ni.id))
```

Same change for variation map.

**n8n payload**: Keep `product_id` in the payload (n8n uses it for Shopee API calls). Read it from the product row. Also add `new_item_id` to payload so n8n can reference back.

#### `lib/services/shopee-listings/job-tracker.ts`

| Query | Current | Change to |
|-------|---------|-----------|
| `markProductJobStatus` UPDATE | `WHERE product_id = ?` | `WHERE new_item_id = ?` |
| `claimProductForProcessing` SELECT FOR UPDATE | `WHERE product_id = ?` | `WHERE new_item_id = ?` |
| `claimProductForProcessing` variations SELECT | `WHERE product_id = ?` | `WHERE new_item_id = ?` |
| Global mutex check | `product_id <> ?` | `new_item_id <> ?` |
| Claim UPDATE | `WHERE product_id = ?` | `WHERE new_item_id = ?` |
| Stale job sweep | No product_id filter | No change needed |

#### `app/api/shopee-listings/generate/route.ts`
- Accept `new_item_id` / `newItemId` instead of `product_id`
- Pass `newItemId` to `generateShopeeListingForProduct()`

#### `app/api/shopee-listings/route.ts` (GET handler for detail)
- Accept `newItemId` query param instead of `productId`
- Pass to `fetchShopeeListingDetail()`

#### `app/api/shopee-listings/staging/route.ts`
- Accept `new_item_id` instead of `product_id`

#### `lib/services/shopee-listings/n8n-webhook.ts`
- No SQL changes (just sends payload as-is)
- Payload still includes `product_id` for n8n (from the product row)

### Frontend changes needed:

#### `components/shopee-listing/hooks/useGenerateFlow.ts`
- Send `new_item_id` instead of `product_id` in POST body to `/api/shopee-listings/generate`
- Send `new_item_id` instead of `product_id` to `/api/shopee-listings/staging`

#### `components/shopee-listing/hooks/useProductDetail.ts`
- `selectedProductId` currently holds `product_id` (the Shopee item ID)
- Needs to hold `new_item_id` instead (the unique listing event identifier)
- `loadProductDetail()` sends `?productId=...` → change to `?newItemId=...`
- Guard effect validates against `product.productId` → validate against `product.newItemId`

#### `components/shopee-listing/page.tsx` (76KB)
- Row click handler: `setSelectedProductId(product.productId)` → `setSelectedProductId(product.newItemId)`
- Summary table may need to show `new_item_id` or both IDs

#### `types/shopee-listing.ts` (frontend types)
- `ListingProductSummary`: add `newItemId: string` field
- `ListingProductDetail`: change `id` to be `new_item_id` value (or add `newItemId` field)

---

## Phase 4: Deploy & Test — TODO

1. Push all webapp changes to `test` branch
2. Test the full flow on staging:
   - Summary view loads correctly (each new_items row shows its own product data)
   - Click Generate → correct row is processed
   - n8n webhook receives correct payload
   - Generated output applies to correct row
3. Test with duplicate product_id scenario (two new_items with same product_id)
4. Push to `main` when verified
5. Merge `db-deploy.yml` DATABASE 1c fix from test to main

---

## Phase 5: Deploy Python Scripts to VM — TODO

1. Pull updated scripts on the VM
2. Test 1688 scraper manually (user runs it to pre-collect data)
3. Test Shopee API script manually
4. Verify data lands in correct rows with correct `new_item_id`

---

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
| **8** | **`UNIQUE(product_id)` causes data collisions between new_product and new_variation events** | **Same product_id overwrites — see PART E** |
| **9** | **Multiple new_variation events per product_id collide** | **8 product_ids have 2-3 new_variation events that overwrite each other — see PART E** |

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

## Migration File Deployment Process

> **CRITICAL**: All database schema changes MUST be deployed via migration files pushed to the `awesomeree-web-app` repository under `migrations/request/`. Direct ALTER TABLE statements on production are NOT allowed.

### How it works

1. **Create migration SQL file** following the naming convention: `YYYYMMDDNNNNNN_description.sql`
2. **Push to `test` branch** → triggers deployment to staging (`webapp_test` database)
3. **Validate on staging** → verify columns exist, no errors, frontend still works
4. **Push to `main` branch** → triggers deployment to production (`requestDatabase`)
5. **Update `atlas.sum`** → add the new migration file entry with `h1:placeholder`

### Naming convention

```
YYYYMMDDNNNNNN_description.sql
│       │      │
│       │      └─ Descriptive name using snake_case
│       └──────── Sequence number (000000, 000001, ...)
└──────────────── Date in YYYYMMDD format
```

Latest existing migration: `20260224000006_create_compat_view.sql`

### Migration SQL style (idempotent pattern)

All migrations use the **idempotent check-then-alter** pattern to be safely re-runnable:

```sql
-- Check if column exists before adding
SET @col = (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'target_table'
  AND COLUMN_NAME = 'new_column');
SET @sql = IF(@col = 0,
  'ALTER TABLE `target_table` ADD COLUMN `new_column` VARCHAR(500) NULL AFTER `existing_column`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
```

### Files involved per migration

| File | Action |
|---|---|
| `migrations/request/YYYYMMDDNNNNNN_description.sql` | New migration file |
| `migrations/request/atlas.sum` | Append new entry with `h1:placeholder` |

### Repository config

- **atlas.hcl**: `env "request" { url = getenv("REQUEST_DB_URL"); migration { dir = "file://migrations/request" } }`
- **atlas.sum**: List of all migration files with placeholder hashes

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

## Phase 1: Create & Deploy Migration Files (Shopee Columns)

> **STATUS: DONE** — 7 Shopee columns already exist on `requestDatabase.shopee_listing_products`.

**Objective**: Create migration SQL files for schema changes and deploy through the proper migration pipeline (test → staging validation → main → production).

### Step 1.1 — Create migration file: `20260225000000_add_shopee_columns_to_listing_products.sql`

**File location**: `migrations/request/20260225000000_add_shopee_columns_to_listing_products.sql`

```sql
-- 20260225000000_add_shopee_columns_to_listing_products.sql
-- Adds Shopee existing listing data columns to shopee_listing_products
-- for the New Variation generation workflow. (idempotent)

-- shopee_product_name: Existing Shopee listing name (from Shopee API)
SET @col = (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_products'
  AND COLUMN_NAME = 'shopee_product_name');
SET @sql = IF(@col = 0,
  'ALTER TABLE `shopee_listing_products` ADD COLUMN `shopee_product_name` VARCHAR(500) NULL COMMENT ''Existing Shopee listing name (from Shopee API)'' AFTER `n8n_supporting_image`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- shopee_description: Existing Shopee listing description (from Shopee API)
SET @col = (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_products'
  AND COLUMN_NAME = 'shopee_description');
SET @sql = IF(@col = 0,
  'ALTER TABLE `shopee_listing_products` ADD COLUMN `shopee_description` LONGTEXT NULL COMMENT ''Existing Shopee listing description (from Shopee API)'' AFTER `shopee_product_name`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- shopee_variation_images: Existing Shopee tier-1 variation images (from Shopee API)
SET @col = (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_products'
  AND COLUMN_NAME = 'shopee_variation_images');
SET @sql = IF(@col = 0,
  'ALTER TABLE `shopee_listing_products` ADD COLUMN `shopee_variation_images` JSON NULL COMMENT ''Existing Shopee tier-1 variation images (from Shopee API)'' AFTER `shopee_description`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- tier_name_1: Existing Shopee tier 1 name e.g. Colour (from Shopee API)
SET @col = (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_products'
  AND COLUMN_NAME = 'tier_name_1');
SET @sql = IF(@col = 0,
  'ALTER TABLE `shopee_listing_products` ADD COLUMN `tier_name_1` VARCHAR(100) NULL COMMENT ''Existing Shopee tier 1 name e.g. Colour (from Shopee API)'' AFTER `shopee_variation_images`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- t1_variation: Existing Shopee tier 1 options e.g. ["Red","Blue"] (from Shopee API)
SET @col = (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_products'
  AND COLUMN_NAME = 't1_variation');
SET @sql = IF(@col = 0,
  'ALTER TABLE `shopee_listing_products` ADD COLUMN `t1_variation` JSON NULL COMMENT ''Existing Shopee tier 1 options e.g. ["Red","Blue"] (from Shopee API)'' AFTER `tier_name_1`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- tier_name_2: Existing Shopee tier 2 name e.g. Size (from Shopee API)
SET @col = (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_products'
  AND COLUMN_NAME = 'tier_name_2');
SET @sql = IF(@col = 0,
  'ALTER TABLE `shopee_listing_products` ADD COLUMN `tier_name_2` VARCHAR(100) NULL COMMENT ''Existing Shopee tier 2 name e.g. Size (from Shopee API)'' AFTER `t1_variation`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- t2_variation: Existing Shopee tier 2 options e.g. ["S","M","L"] (from Shopee API)
SET @col = (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_products'
  AND COLUMN_NAME = 't2_variation');
SET @sql = IF(@col = 0,
  'ALTER TABLE `shopee_listing_products` ADD COLUMN `t2_variation` JSON NULL COMMENT ''Existing Shopee tier 2 options e.g. ["S","M","L"] (from Shopee API)'' AFTER `tier_name_2`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
```

### Step 1.2 — Update `atlas.sum`

Append to the end of `migrations/request/atlas.sum`:
```
20260225000000_add_shopee_columns_to_listing_products.sql h1:placeholder
```

### Step 1.3 — Push to `test` branch (staging deployment)

```bash
# In awesomeree-web-app repo
git checkout test
git pull origin test
# Add the migration file + updated atlas.sum
git add migrations/request/20260225000000_add_shopee_columns_to_listing_products.sql
git add migrations/request/atlas.sum
git commit -m "migration: add shopee columns to shopee_listing_products for new variation flow"
git push origin test
```

### Step 1.4 — Validate on staging (`webapp_test`)

```sql
-- Verify columns were added on staging
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'webapp_test'
  AND TABLE_NAME = 'shopee_listing_products'
  AND COLUMN_NAME IN ('shopee_product_name', 'shopee_description', 'shopee_variation_images',
                       'tier_name_1', 't1_variation', 'tier_name_2', 't2_variation');
-- Should return 7 rows
```

Also verify frontend still loads (new columns are all NULL — no breaking change).

### Step 1.5 — Push to `main` branch (production deployment)

```bash
# After staging validation passes
git checkout main
git pull origin main
git merge test  # or cherry-pick the migration commit
git push origin main
```

### Step 1.6 — Verify on production (`requestDatabase`)

```sql
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'requestDatabase'
  AND TABLE_NAME = 'shopee_listing_products'
  AND COLUMN_NAME IN ('shopee_product_name', 'shopee_description', 'shopee_variation_images',
                       'tier_name_1', 't1_variation', 'tier_name_2', 't2_variation');
-- Should return 7 rows
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

**Acceptance**: `DESCRIBE` shows all 7 new columns on both staging and production. No data loss. Frontend still works (columns are NULL, no breaking change).

**Dependencies**: Phase 0 (backups must exist first).

---

## Phase 2: Migrate Existing Data

**Objective**: Copy the 12 rows of valid data from `shopee_existing_listing` into the normalized tables so nothing is lost.

> **Note**: Data migration is run manually (not via migration file) because it involves cross-table data copy that is a one-time operation. Similar to how `20260224000005_migrate_data.js` was handled separately.

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

**Dependencies**: Phase 1 (columns must exist on production).

---

## Phase 3: Update Python Scripts

> **STATUS: DONE** — All 3 scripts updated and pushed to `it-awesomeree/eten-workspace` main branch.
> **NOTE**: These scripts currently write by `product_id`. They need to be updated AGAIN in Part E (Phase E3) to write by `new_item_id` instead.

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

**Dependencies**: Phase 1 (schema deployed to production).

---

## Phase 4: Update Backend Service Layer

> **STATUS: PARTIALLY DONE** — Changes pushed to `test` branch but need rework for `new_item_id` (Part E).

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

**Dependencies**: Phase 1 (schema deployed to production).

---

## Phase 5: Update Frontend

> **STATUS: PARTIALLY DONE** — Changes pushed to `test` branch but need rework for `new_item_id` (Part E).

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
| 1.1 | Migration | Create `20260225000000_add_shopee_columns_to_listing_products.sql` | DONE | |
| 1.2 | Migration | Update `atlas.sum` | DONE | |
| 1.3 | Migration | Push to `test` branch (staging) | DONE | |
| 1.4 | Migration | Validate 7 new columns on staging (`webapp_test`) | DONE | |
| 1.5 | Migration | Push to `main` branch (production) | DONE | |
| 1.6 | Migration | Verify 7 new columns on production (`requestDatabase`) | DONE | |
| 2.1 | Data Migration | Copy Shopee data to normalized | DONE | |
| 2.2 | Data Migration | Copy 1688 desc images | DONE | |
| 2.3 | Data Migration | Verify migration | DONE | |
| 2.4 | Data Migration | Handle orphan items | TODO | |
| 3.1 | Scripts | Update 1688 variation scraper | DONE (needs rework for new_item_id) | |
| 3.2 | Scripts | Update Shopee API script | DONE (needs rework for new_item_id) | |
| 3.3 | Scripts | Test script execution order | TODO | |
| 4.1 | Backend | Update types.ts | DONE (on test branch, needs rework) | |
| 4.2 | Backend | Update normalizers.ts | TODO | |
| 4.3 | Backend | Update generate.ts — detail | DONE (on test branch, needs rework) | |
| 4.4 | Backend | Update generate.ts — webhook payload | DONE (on test branch, needs rework) | |
| 4.5 | Backend | Verify summary (no change needed) | DONE | |
| 4.6 | Backend | Update frontend types | DONE (on test branch, needs rework) | |
| 5.1 | Frontend | Add Shopee Existing / hide competitors | DONE (on test branch, needs rework) | |
| 5.2 | Frontend | Conditional rendering | DONE (on test branch, needs rework) | |
| 5.3 | Frontend | Tier display component | DONE (on test branch, needs rework) | |
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

### Migrations
```
migrations/request/
  atlas.hcl                          — Atlas config (env "request", dir = "file://migrations/request")
  atlas.sum                          — Migration checksum file (placeholder hashes)
  20260224000001_create_shopee_listing_products.sql
  20260224000002_create_shopee_listing_variations.sql
  20260224000003_create_shopee_listing_reviews.sql
  20260224000004_formalize_hero_templates.sql
  20260224000005_migrate_data.js     — Data migration script (JS, not SQL)
  20260224000006_create_compat_view.sql
  20260225000000_add_shopee_columns_to_listing_products.sql
  20260225000001_add_new_item_id.sql  ← NEW (Part E migration)
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

## D4. Migration Deployment Flow

```
Create SQL file → Push to test branch → Staging validates → Push to main branch → Production applies
                  (webapp_test DB)                          (requestDatabase)
```

- **Naming**: `YYYYMMDDNNNNNN_description.sql`
- **Style**: Idempotent (check column exists before ALTER)
- **Checksum**: `atlas.sum` with `h1:placeholder` entries
- **Branch flow**: `test` → staging validation → `main` → production

---

# PART E — CRITICAL SCHEMA REDESIGN: `new_item_id`

> **Added**: 25 Feb 2026
> **Status**: READY FOR REVIEW — Must be executed before Phase 4-5 rework
> **Priority**: BLOCKING — This supersedes the `product_id`-based approach in Phases 3-5

## E1. Problem Discovery

During testing of Phase 4-5 changes (backend + frontend on `test` branch), two critical issues were found:

### Issue 1: Data collision between new_product and new_variation

The same `product_id` can appear in `new_items` as **both** New Product and New Variation. Since `shopee_listing_products` has `UNIQUE(product_id)`, only ONE row exists. Whichever scraper runs last overwrites the other's data.

**Result**: 1688 data from new_product (e.g., glue gun hero image) gets mixed with Shopee API data from new_variation (e.g., Expanding Foam description). The frontend shows garbage mixed data.

### Issue 2: Some new_variation items display competitor data incorrectly

Because the single DB row has `item_type` from whichever scraper ran last, clicking a "New Variation" row in the frontend sometimes gets `item_type = 'new_product'` from the DB, causing competitor data to display when it shouldn't.

### Issue 3: Missing variation data

For product_id 9193675690, the actual new variation "900g/750ml加强" is NOT in `shopee_listing_variations`. The 3 variations shown are from the new_product scraper (glue gun variations). The new_variation's 1688 data was overwritten.

## E2. Investigation Findings (25 Feb 2026)

### Database counts

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
| Product_ids with item_type mismatch in DB | **~20** | DB says new_variation but 1688 data is actually from new_product scraper |

### The 8 product_ids with multiple new_variation events

These are the reason `UNIQUE(product_id, item_type)` would NOT work either:

| product_id | # of New Variation events |
|---|---|
| 28079888416 | 3 |
| 22581507419 | 3 |
| 8390619505 | 2 |
| 18880804735 | 2 |
| 10059817794 | 2 |
| 22055995385 | 2 |
| 25507762456 | 2 |
| 27789585481 | 2 |

### Case study: product_id 9193675690

**What's in `new_items` (3 events):**

| new_items.id | launch_type | product_name_en | date |
|---|---|---|---|
| 397 | New Product | Manual Glue Gun (NEW) | 2025-09-29 |
| 429 | New Product | Toilet Cleaner | 2025-10-06 |
| 485 | New Variation | Expanding Foam | 2025-10-22 |

**What's in `shopee_listing_products` (only 1 row due to UNIQUE):**
- `id=3`, `item_type=new_variation`, but `launch_type=New Product` (contradicts itself!)
- `1688_product_name` = "手动玻璃胶枪..." (Glue Gun — from ni=397, wrong!)
- `1688_hero` = Glue gun hero image (wrong for new_variation!)
- `shopee_product_name` = "Vira PU Foam Spray..." (correct Shopee API data)
- Has 15 Shopee tier variations (Vira Foam 750ML, etc.)

**What's in `shopee_listing_variations` (3 rows — all wrong for new_variation):**
- `id=10`: "发泡胶枪塑料橙色一件40把" (foam gun — from new_product scraper)
- `id=11`: "蓝瓶" (blue bottle — from new_product scraper)
- `id=12`: "粉瓶" (pink bottle — from new_product scraper)

**What's MISSING:**
- The actual new variation "900g/750ml加强" is NOT anywhere in `shopee_listing_variations`
- No separate rows for ni=397 (Glue Gun new_product) and ni=429 (Toilet Cleaner new_product)

## E3. Why Current Approaches Fail

### Approach 1: `UNIQUE(product_id)` — Current (FAILS)

Only 1 row per product. 3 events for product_id 9193675690 all fight for the same row. Last writer wins.

### Approach 2: `UNIQUE(product_id, item_type)` — Considered (ALSO FAILS)

Would allow 2 rows per product (one new_product, one new_variation). But:
- **8 product_ids have MULTIPLE new_variation events** (e.g., 28079888416 has 3)
- All 3 new_variation events would fight for `(28079888416, 'new_variation')` — same collision
- **48 product_ids have multiple new_product events** — same problem on new_product side

### Approach 3: `UNIQUE(new_item_id)` — Proposed (WORKS)

Each `new_items.id` is globally unique. Using it as the unique key means:
- Every event gets its own completely isolated row
- No collisions regardless of how many events share a product_id
- Works for unlimited future new_variation additions

## E4. Solution: `new_item_id` Column

### Core change

Add `new_item_id BIGINT NOT NULL` to both tables. This references `new_items.id` and becomes the new unique key.

```
BEFORE:  shopee_listing_products   UNIQUE(product_id)
AFTER:   shopee_listing_products   UNIQUE(new_item_id), INDEX(product_id)

BEFORE:  shopee_listing_variations  FK(product_id) → products.product_id
AFTER:   shopee_listing_variations  INDEX(new_item_id), INDEX(product_id)
```

### What stays the same

- `product_id` column stays (for reference, display, grouping) — just no longer unique
- All existing data columns stay (1688_*, shopee_*, n8n_*)
- The column meanings are identical — the difference is each event populates its own row

### New data model

```
new_items (id=397, product_id=9193675690, "New Product", "Glue Gun")
    → shopee_listing_products  (new_item_id=397, item_type='new_product')
    → shopee_listing_variations (new_item_id=397, 3 glue gun variations)

new_items (id=429, product_id=9193675690, "New Product", "Toilet Cleaner")
    → shopee_listing_products  (new_item_id=429, item_type='new_product')
    → shopee_listing_variations (new_item_id=429, toilet cleaner variations)

new_items (id=485, product_id=9193675690, "New Variation", "Expanding Foam")
    → shopee_listing_products  (new_item_id=485, item_type='new_variation')
    → shopee_listing_variations (new_item_id=485, 1 variation: "900g/750ml加强")
```

Each event is **completely isolated**. No overwriting. No conflicts.

## E5. Proof: Isolation Walkthrough

### After migration, product_id 9193675690 will have:

**`shopee_listing_products` (3 rows):**

| new_item_id | product_id | item_type | 1688_product_name | shopee_product_name | n8n_product_name |
|---|---|---|---|---|---|
| 397 | 9193675690 | new_product | 手动玻璃胶枪... (Glue Gun) | NULL | (from n8n) |
| 429 | 9193675690 | new_product | (Toilet Cleaner 1688 data) | NULL | (from n8n) |
| 485 | 9193675690 | new_variation | (Expanding Foam 1688 data) | Vira PU Foam Spray... | NULL (not output) |

**`shopee_listing_variations`:**

| new_item_id | 1688_variation | n8n_variation |
|---|---|---|
| 397 | 发泡胶枪塑料橙色... | (from n8n) |
| 397 | 蓝瓶 | (from n8n) |
| 397 | 粉瓶 | (from n8n) |
| 429 | (Toilet Cleaner vars) | (from n8n) |
| 485 | 900g/750ml加强 | (from n8n) |

### Click behavior:

1. **Click "New Product" row (ni=397, Glue Gun)**
   - `SELECT * FROM shopee_listing_products WHERE new_item_id = 397` → Glue gun 1688 data
   - `SELECT * FROM shopee_listing_variations WHERE new_item_id = 397` → 3 glue gun variations
   - Fetch competitors from Shopee_Comp → Shows competitor cards
   - Generate → Sends **6 fields** to n8n: product_name + desc + hero + supporting + variations

2. **Click "New Product" row (ni=429, Toilet Cleaner)**
   - Completely separate data. Different 1688 source, different variations.

3. **Click "New Variation" row (ni=485, Expanding Foam)**
   - `SELECT * FROM shopee_listing_products WHERE new_item_id = 485` → Expanding foam 1688 + Shopee data
   - `SELECT * FROM shopee_listing_variations WHERE new_item_id = 485` → **ONLY** "900g/750ml加强"
   - **NO competitor fetch** (it's new_variation)
   - Generate → Sends **3 fields** to n8n: desc + variations only (no product_name/hero/supporting)

### Multiple new_variation proof (product_id 28079888416 with 3 events):

Each new_variation event gets its own row:
- Event #1: Adds color variations → new_item_id=X, own 1688 data, own variations
- Event #2: Adds size variations → new_item_id=Y, own 1688 data, own variations
- Event #3: Adds material variations → new_item_id=Z, own 1688 data, own variations

Completely isolated. Can generate each independently.

## E6. n8n Output Differences (Why Isolation Matters)

| n8n Output Field | DB Column | New Product | New Variation |
|---|---|---|---|
| n8n_product_name | products.n8n_product_name | **YES** | NO (stays NULL) |
| n8n_product_description | products.n8n_product_description | **YES** | **YES** |
| n8n_hero | products.n8n_hero | **YES** | NO (stays NULL) |
| n8n_supporting_image | products.n8n_supporting_image | **YES** | NO (stays NULL) |
| n8n_variation | variations.n8n_variation | **YES** | **YES** |
| n8n_variation_image | variations.n8n_variation_image | **YES** | **YES** |

If they share one row, you can't tell which output belongs to which workflow. With `new_item_id`, each row knows exactly what it is.

## E7. Migration SQL

### Migration file: `20260225000001_add_new_item_id.sql`

> Deploy via the migration pipeline: `test` branch → staging validation → `main` branch → production

```sql
-- 20260225000001_add_new_item_id.sql
-- Adds new_item_id column to shopee_listing_products and shopee_listing_variations
-- to support multiple events per product_id (idempotent)

-- ============================================================
-- STEP 1: Add new_item_id column to products table
-- ============================================================
SET @col = (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_products'
  AND COLUMN_NAME = 'new_item_id');
SET @sql = IF(@col = 0,
  'ALTER TABLE `shopee_listing_products` ADD COLUMN `new_item_id` BIGINT NULL AFTER `id`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ============================================================
-- STEP 2: Add new_item_id column to variations table
-- ============================================================
SET @col = (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_variations'
  AND COLUMN_NAME = 'new_item_id');
SET @sql = IF(@col = 0,
  'ALTER TABLE `shopee_listing_variations` ADD COLUMN `new_item_id` BIGINT NULL AFTER `product_id`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
```

### Post-migration data script (run manually after migration deploys)

> Similar to `20260224000005_migrate_data.js` — run as a one-time manual operation.

```sql
-- ============================================================
-- STEP 3: Backfill new_item_id for existing products
-- Match by product_id + item_type, pick most recent new_items row
-- ============================================================
UPDATE shopee_listing_products p
SET p.new_item_id = (
  SELECT ni.id
  FROM new_items ni
  WHERE CAST(ni.product_id AS CHAR) = CAST(p.product_id AS CHAR)
    AND (
      (p.item_type = 'new_product' AND ni.launch_type IN ('New Product', 'New Product (SG)'))
      OR (p.item_type = 'new_variation' AND ni.launch_type = 'New Variation')
    )
  ORDER BY ni.date DESC, ni.id DESC
  LIMIT 1
)
WHERE p.new_item_id IS NULL;

-- For rows where item_type doesn't match any new_items launch_type,
-- fall back to most recent new_items row for that product_id
UPDATE shopee_listing_products p
SET p.new_item_id = (
  SELECT ni.id
  FROM new_items ni
  WHERE CAST(ni.product_id AS CHAR) = CAST(p.product_id AS CHAR)
  ORDER BY ni.date DESC, ni.id DESC
  LIMIT 1
)
WHERE p.new_item_id IS NULL;

-- ============================================================
-- STEP 4: Backfill new_item_id for existing variations
-- Copy from parent product row
-- ============================================================
UPDATE shopee_listing_variations v
JOIN shopee_listing_products p ON v.product_id = p.product_id
SET v.new_item_id = p.new_item_id
WHERE v.new_item_id IS NULL;

-- ============================================================
-- STEP 5: Verify — check for orphans
-- ============================================================
-- Any products still NULL?
SELECT p.id, p.product_id, p.item_type, p.new_item_id
FROM shopee_listing_products p
WHERE p.new_item_id IS NULL;
-- → Delete if any (stale data with no source event)

-- Any variations still NULL?
SELECT v.id, v.product_id, v.new_item_id
FROM shopee_listing_variations v
WHERE v.new_item_id IS NULL;
-- → Delete if any
```

### Constraint switch migration: `20260225000002_switch_unique_to_new_item_id.sql`

> Deploy AFTER backfill is complete and verified (no NULL new_item_id rows remain).

```sql
-- 20260225000002_switch_unique_to_new_item_id.sql
-- Switches unique key from product_id to new_item_id (idempotent)

-- ============================================================
-- STEP 1: Make new_item_id NOT NULL
-- ============================================================
SET @col = (SELECT IS_NULLABLE FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_products'
  AND COLUMN_NAME = 'new_item_id');
SET @sql = IF(@col = 'YES',
  'ALTER TABLE `shopee_listing_products` MODIFY COLUMN `new_item_id` BIGINT NOT NULL',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col = (SELECT IS_NULLABLE FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_variations'
  AND COLUMN_NAME = 'new_item_id');
SET @sql = IF(@col = 'YES',
  'ALTER TABLE `shopee_listing_variations` MODIFY COLUMN `new_item_id` BIGINT NOT NULL',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ============================================================
-- STEP 2: Drop old FK on variations (references old UNIQUE on product_id)
-- ============================================================
SET @fk = (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_variations'
  AND CONSTRAINT_NAME = 'fk_variation_product');
SET @sql = IF(@fk > 0,
  'ALTER TABLE `shopee_listing_variations` DROP FOREIGN KEY `fk_variation_product`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ============================================================
-- STEP 3: Drop old UNIQUE on product_id, add new UNIQUE on new_item_id
-- ============================================================
SET @idx = (SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_products'
  AND INDEX_NAME = 'uk_product_id');
SET @sql = IF(@idx > 0,
  'ALTER TABLE `shopee_listing_products` DROP INDEX `uk_product_id`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx = (SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_products'
  AND INDEX_NAME = 'uk_new_item');
SET @sql = IF(@idx = 0,
  'ALTER TABLE `shopee_listing_products` ADD UNIQUE KEY `uk_new_item` (`new_item_id`)',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ============================================================
-- STEP 4: Add regular INDEX on product_id (for lookups/grouping)
-- ============================================================
SET @idx = (SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_products'
  AND INDEX_NAME = 'idx_product_id');
SET @sql = IF(@idx = 0,
  'ALTER TABLE `shopee_listing_products` ADD INDEX `idx_product_id` (`product_id`)',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ============================================================
-- STEP 5: Add INDEX on new_item_id for variations table
-- ============================================================
SET @idx = (SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'shopee_listing_variations'
  AND INDEX_NAME = 'idx_new_item');
SET @sql = IF(@idx = 0,
  'ALTER TABLE `shopee_listing_variations` ADD INDEX `idx_new_item` (`new_item_id`)',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
```

## E8. Code Changes Required (After Schema Migration)

### Python Scripts (Phase E3 — rework of Phase 3)

All 3 scripts already iterate over `new_items` rows, so they have `new_items.id`. They need to:

| Script | Current write key | New write key | Changes |
|---|---|---|---|
| `1688_web_scrape_new_product.py` | `product_id` | `new_item_id` | UPSERT products ON DUPLICATE KEY (new_item_id), DELETE+INSERT variations WHERE new_item_id |
| `1688_web_scrape_new_variation.py` | `product_id` | `new_item_id` | Same pattern |
| `shopee_api.py` | `product_id` | `new_item_id` | UPDATE WHERE new_item_id = ? |

**Key change in each script:**
1. Pass `new_items.id` (already available in the loop) as `new_item_id`
2. `INSERT INTO shopee_listing_products (new_item_id, product_id, ...) ON DUPLICATE KEY UPDATE ...`
3. `DELETE FROM shopee_listing_variations WHERE new_item_id = ?` (not product_id)
4. `INSERT INTO shopee_listing_variations (new_item_id, product_id, ...) VALUES ...`

### Webapp Backend (Phase E4 — rework of Phase 4)

| Function | Current | New |
|---|---|---|
| Summary builder | `productRowMap.get(productId)` | `productRowMap.get(newItemId)` — join products ON new_item_id |
| `fetchProduct()` | `WHERE product_id = ?` | `WHERE new_item_id = ?` |
| `fetchVariations()` | `WHERE product_id = ?` | `WHERE new_item_id = ?` |
| `buildGeneratePayload()` | fetch by product_id | fetch by new_item_id |
| `fetchShopeeListingDetail()` | fetch by product_id | fetch by new_item_id |

**Simplification**: The `itemType` parameter hack (passing itemType from frontend to override DB value) is no longer needed. Each `new_item_id` uniquely identifies the event AND its correct item_type.

### Webapp Frontend (Phase E5 — rework of Phase 5)

| Component | Current | New |
|---|---|---|
| Summary row data | Has `productId` + `itemType` | Also include `newItemId` (from new_items.id) |
| Row click handler | `loadProductDetail(productId, itemType)` | `loadProductDetail(newItemId)` — simpler! |
| Detail API call | `?productId=X&itemType=Y` | `?newItemId=X` — single param |
| useProductDetail hook | `loadProductDetail(productId, itemType)` | `loadProductDetail(newItemId)` |

### API Route

```
GET /api/shopee-listings?newItemId=485
  → fetchShopeeListingDetail(newItemId=485)
  → Returns: product data + variations for this specific event
```

## E9. Implementation Order

| Step | What | Depends On | Status |
|---|---|---|---|
| E1 | Create migration `20260225000001_add_new_item_id.sql` | — | TODO |
| E2 | Push to `test` → validate on staging | E1 | TODO |
| E3 | Push to `main` → deploy to production | E2 | TODO |
| E4 | Run backfill script (Step 3-4-5 from E7) | E3 | TODO |
| E5 | Verify no NULL new_item_id rows remain | E4 | TODO |
| E6 | Create migration `20260225000002_switch_unique_to_new_item_id.sql` | E5 | TODO |
| E7 | Push constraint switch to `test` → validate | E6 | TODO |
| E8 | Push constraint switch to `main` → deploy | E7 | TODO |
| E9 | Update Python scripts to write by new_item_id | E8 | TODO |
| E10 | Update webapp backend (generate.ts) | E8 | TODO |
| E11 | Update webapp frontend (page.tsx, hooks) | E10 | TODO |
| E12 | Re-trigger scrapers for events with missing data | E9 | TODO |
| E13 | Verify using checklist below | E12 | TODO |

## E10. Verification Checklist

After full implementation, verify:

- [ ] `shopee_listing_products` has UNIQUE on `new_item_id` (not product_id)
- [ ] `shopee_listing_products.product_id` is a regular INDEX (not unique)
- [ ] product_id 9193675690 has 3 separate rows (ni=397, 429, 485)
- [ ] ni=397 row: item_type=new_product, 1688 data = Glue Gun, no Shopee data
- [ ] ni=429 row: item_type=new_product, 1688 data = Toilet Cleaner, no Shopee data
- [ ] ni=485 row: item_type=new_variation, 1688 data = Expanding Foam, Shopee data present
- [ ] ni=485 variations: ONLY "900g/750ml加强" (1 row, not 3)
- [ ] Clicking ni=397 row: shows competitors, shows 3 glue gun variations
- [ ] Clicking ni=485 row: shows Shopee data card (no competitors), shows 1 variation
- [ ] n8n generate for ni=397: sends product_name + desc + hero + supporting + variations (6 fields)
- [ ] n8n generate for ni=485: sends only desc + variations (3 fields, no product_name/hero/supporting)
- [ ] product_id 28079888416: 3 separate new_variation rows, each with own 1688 data + variations
- [ ] Multiple new_variation events for same product_id are fully isolated
- [ ] Python scrapers write by new_item_id (no product_id collision)
- [ ] Frontend uses `?newItemId=X` (not `?productId=X&itemType=Y`)
