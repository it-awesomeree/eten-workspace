# Shopee Listing Page - Deep Analysis

> Reference doc for all shopee-listing work. Created 25 Feb 2026 from codebase analysis of `it-awesomeree/awesomeree-web-app` (main branch).

---

## 1. Database Tables

### requestDatabase (main DB for shopee-listing)

| Table | Role |
|---|---|
| `new_items` | Source of truth. One row per product event. Has `product_id`, `product_name_en`, `variation_list_en` (JSON array), `variation_list_cn`, `shop`, `launch_type`, `date` |
| `shopee_listing_products` | Product-level listing data. Stores 1688 supplier columns (`1688_*`) and n8n AI output columns (`n8n_*`). Also tracks job state (`n8n_job_status`, `n8n_job_type`, `n8n_job_targets`, `n8n_requested_at`, `n8n_started_at`, `n8n_completed_at`, `n8n_error`) |
| `shopee_listing_variations` | One row per variation per product. Has `1688_variation`, `1688_variation_image`, `n8n_variation`, `n8n_variation_image`, `sort_order` |
| `shopee_listing_reviews` | Staging table for regenerated content. Status: `pending_review` / `approved` / `rejected`. Holds regenerated field values for selective approval |
| `hero_templates` | Hero image templates per shop. `shop_name` + `template_url` (GCS URL) |

### allbots DB

| Table | Role |
|---|---|
| `Shopee_Comp` | Competitor data. Linked by `our_item_id`. Has `comp_product`, `comp_price`, `comp_rating`, `comp_monthly_sales`, `comp_shop`, `comp_variation`, `comp_link`, etc. |

---

## 2. File Structure (awesomeree-web-app repo)

### Route
```
app/inventory/shopee-listing/page.tsx
  -> Just wraps <ShopeeListingPage /> with Suspense
```

### Frontend Components
```
components/shopee-listing/
  page.tsx                     # 72KB - Main orchestrating component (the whole page UI)
  FilterBar.tsx                # Region (MY/SG) + Type (new_product/new_variation) toggle buttons
  ActivityPanel.tsx            # Side sheet showing global activity log
  ComparisonDialog.tsx         # Side-by-side current vs regenerated comparison dialog
  GenerateConfirmDialog.tsx    # Confirmation dialog before generate/regenerate
  TemplateLibraryDialog.tsx    # Hero template browse/upload dialog
  AuditHintTooltip.tsx         # Tooltip showing last audit entry on action buttons
  ErrorBoundary.tsx            # React error boundary wrapper
  sub-components.tsx           # StatusDot, ImageGallery, DescriptionBlock
  utils.ts                    # Constants, helpers, type re-exports
```

### Frontend Hooks
```
components/shopee-listing/hooks/
  useProductList.ts            # Product list fetch, client-side search/sort/pagination
  useProductDetail.ts          # Selected product detail fetch, variation selection
  useGenerateFlow.ts           # Generate/regenerate/staging review state machine (17KB)
  useFilterState.ts            # URL-synced region/type filters via useSearchParams
  useActivityLog.ts            # Activity log fetch with filters
  useActionAudit.ts            # Per-product audit trail with hints
  useDebounce.ts               # Generic debounce hook (300ms default)
```

### API Routes
```
app/api/shopee-listings/
  route.ts                     # GET - summary list or single product detail
  generate/route.ts            # POST - trigger n8n generation/regeneration
  staging/route.ts             # POST - approve/reject regenerated content
  templates/route.ts           # GET + POST - hero template management
```

### Backend Service Layer
```
lib/services/shopee-listings/
  index.ts                     # Barrel re-exports
  generate.ts                  # 45KB - Main orchestration (summary, detail, generate logic)
  db.ts                        # MySQL connections, table constants, query executors
  staging.ts                   # Approve/reject transactional logic
  n8n-webhook.ts               # n8n webhook caller + response parser
  job-tracker.ts               # Mutex/locking, job state management
  normalizers.ts               # 38KB - All data normalization (images, strings, categories)
  types.ts                     # Backend TypeScript types
```

---

## 3. API Endpoints

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/api/shopee-listings` | GET | None | Fetch product list (summary) or single product detail |
| `/api/shopee-listings/generate` | POST | None | Trigger n8n AI generate/regenerate |
| `/api/shopee-listings/staging` | POST | None | Approve/reject regenerated content |
| `/api/shopee-listings/templates` | GET | None | List hero templates |
| `/api/shopee-listings/templates` | POST | Firebase session | Upload hero template image to GCS |

### GET /api/shopee-listings (Summary Mode)
- Params: `?region=MY|SG&type=new_product|new_variation`
- Returns: `{ products: ListingProductSummary[], missingListingTable, missingCompTable }`

### GET /api/shopee-listings (Detail Mode)
- Params: `?productId=XXX` (or `product_id`)
- Returns: `{ product: ListingProductDetail, missingListingTable, missingCompTable, missingStagingTable }`

### POST /api/shopee-listings/generate
- Body: `{ product_id, targets: ["all"|"name"|"variation"|"description"|"hero"|"supporting_images"|"variation_images"] }`
- Returns: `{ traceId, successCount, failedCount, results: [...] }`
- Status codes: 200 (success), 207 (partial), 409 (n8n busy), 400/500 (error)

### POST /api/shopee-listings/staging
- Body: `{ product_id, action: "approve"|"reject"|"replace"|"discard", selected_fields?: [...] }`
- "replace" maps to "approve", "discard" maps to "reject"
- Returns: `{ success: true, ok, productId, action, stagingId, updatedRows }`

---

## 4. Frontend Data Flow

### Page Load
```
1. Mount -> useFilterState reads URL params (region, type)
2. useProductList.loadSummary() -> GET /api/shopee-listings?region=&type=
3. Backend: shopee_listing_products JOIN new_items, count variations, count competitors
4. Frontend: search filter (debounced 300ms) -> sort -> paginate (10/page) -> render table
```

### Product Detail
```
1. Click table row -> setSelectedProductId(pid)
2. loadProductDetail(pid) -> GET /api/shopee-listings?productId=pid
3. Backend fetches: product + variations + competitors + pending reviews + hero template
4. Frontend renders 3 accordion sections per variation:
   - Supplier Data (1688 originals)
   - Optimized / AI Output (n8n-generated, with current/regenerated toggle)
   - Competitors (from Shopee_Comp)
```

### AI Generation
```
1. User clicks "Generate All" -> confirmation dialog
2. POST /api/shopee-listings/generate { product_id, targets: ["all"] }
3. Backend: claimProductForProcessing() (mutex via FOR UPDATE, single-job-at-a-time)
4. Build payload from 1688 data + competitors + hero template
5. callN8nListingWebhook() -> POST to n8n (120s timeout)
6. Fresh gen: results written directly to products + variations tables
7. Regen: results written to reviews table with status=pending_review
8. Frontend polls every 30s while status is "processing"
```

### Regeneration Review
```
1. Pending regen data appears in detail panel
2. User opens ComparisonDialog (side-by-side current vs regenerated)
3. User selects which fields to keep (checkboxes)
4. POST /api/shopee-listings/staging { product_id, action: "replace", selected_fields }
5. Backend: transaction locks product + variations, copies approved fields, marks review approved
```

---

## 5. n8n Integration

### Webhook Endpoints
| Flow | URL | Item Type |
|---|---|---|
| Generate | `https://n8n.barndoguru.com/webhook/generate-listing` | new_product |
| Regenerate | `https://n8n.barndoguru.com/webhook/regenerate-listing` | new_product |
| Variation Generate | `https://n8n.barndoguru.com/webhook/generate-variation-listing` | new_variation |
| Variation Regenerate | `https://n8n.barndoguru.com/webhook/regenerate-variation-listing` | new_variation |

### Payload Sent to n8n
```json
{
  "product_id": "123456",
  "product_name_1688": "Original Chinese product name",
  "description_1688": "Original description text",
  "hero_images": ["https://..."],
  "variation_images": ["https://..."],
  "description_images": ["https://..."],
  "supporting_images": ["https://..."],
  "variations_1688": ["Color A", "Color B"],
  "competitors": [{ "product_name": "...", "description": "...", "variations": [...] }],
  "shop_name": "MyShop",
  "hero_template_url": "https://storage.googleapis.com/...",
  "targets": ["all"]
}
```

For regeneration, adds: `regenerate: [field_list]` and `current_outputs: { current n8n values }`.

### Response Parsing
`normalizeWebhookOutput()` handles many response shapes from n8n and searches for these field aliases:
- productName: `n8n_product_name`, `product_name`, `optimized_product_name`
- variationNames: `n8n_variation`, `variation_names`, `variations`
- description: `n8n_product_description`, `product_description`, `description`
- heroImage: `n8n_hero`, `hero_image`, `hero`, `cover_image`
- supportingImages: `n8n_supporting_image`, `supporting_images`, `item_images`
- variationImages: `n8n_variation_image`, `variation_images`

---

## 6. Key Frontend Types

```typescript
ListingProductSummary {
  id, productId, productName, heroImage,
  region, itemType, category, itemDate,
  variationCount, readyVariationCount,
  hasOptimizedContent, n8nJob: ListingJobState,
  competitorCount, ourShopName
}

ListingProductDetail extends ListingProductSummary {
  variations: ListingVariation[],
  competitors: Competitor[],
  heroTemplateUrl,
  regeneratedData?: ListingRegeneratedData
}

ListingVariation {
  id, name, n8nStatus: "ready"|"pending"|"generating",
  supplier: ListingContent,       // 1688 data
  optimized?: ListingContent,     // n8n output
  competitors: Competitor[]
}

ListingContent {
  productName, variation, price?,
  description?, descriptionImages?,
  heroImage?, supportingImages?,
  variationImages?, url?
}
```

---

## 7. Key Design Patterns

- **Single-job mutex**: Only one product can be generating at a time globally (enforced via `FOR UPDATE` row locking in `claimProductForProcessing()`)
- **Stale job recovery**: Jobs stuck in "processing" > 45 minutes are auto-failed on next request
- **Variation count fallback** (PR #334): When `shopee_listing_variations` has no rows (pre-n8n processing), falls back to parsing `new_items.variation_list_en`
- **Null product ID guard** (PR #335): Products without `product_id` are dimmed and unclickable
- **Selected row highlight** (PR #336): Clicked row gets `bg-muted/60`
- **Connection-per-query**: Each DB operation opens/closes its own MySQL connection
- **Regeneration staging**: Regen results go to `shopee_listing_reviews` first, not directly applied. Requires explicit approve/reject with field-level selection.

---

## 8. UI Structure (Master-Detail Pattern)

### Left Panel (Product List)
- Header: "Shopee Listing" title + stats badges
- FilterBar: Region (ALL/MY/SG), Type (ALL/New Product/New Variation)
- Search input (debounced 300ms, client-side filter on name/id)
- Toolbar: History button (ActivityPanel), Library button (TemplateLibraryDialog)
- Table with sortable columns: Product, Variations (ready/total), n8n Coverage (%), Competitors, Date
- Pagination: 10 per page, prev/next buttons

### Right Panel (Product Detail - shown on row click)
- Header: back button, product name, "Generate All" button
- n8n status banner (processing spinner / failed error / completed)
- Variation sidebar: search + list with StatusDot (green=ready, blue=generating, amber=pending)
- Per-variation content (3 accordions):
  - Supplier Data (amber) - 1688 originals
  - Optimized / AI Output (indigo) - n8n output with current/regenerated toggle
  - Competitors (rose) - competitor listings
- Regenerate panel: checkboxes per field + regenerate button
- Staging review banner when pending regenerated data exists

### Dialogs
- GenerateConfirmDialog - confirmation before generate/regenerate
- ComparisonDialog - side-by-side current vs regenerated
- TemplateLibraryDialog - hero template browse/upload
- ActivityPanel - side sheet with filtered activity log
