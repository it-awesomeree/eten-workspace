---
description: MySQL database schema - 5 databases, 220 tables with column structures, relationships, and common queries
argument-hint: [database, table, column, or what you're querying]
---

# MySQL Database Schema

**Tool**: `mcp__mysql__mysql_query` (READ-ONLY, multi-DB)
**Write access**: `mycli` CLI at `/Users/user/.local/mycli-venv/bin/mycli -h 34.142.159.230 -P 3306 -u root -p 'd(Qsbh~$.2FOpNl'`
**Syntax**: Single SQL per call. Use `database.table`. Backtick columns with spaces: `` `Order ID` ``
**SKU is the universal join key** (but column name varies: `SKU`, `Sku`, `sku`, `isku`, `product_sku`)

---

## Database Overview

| Database | Purpose | Tables | Largest Table |
|----------|---------|--------|---------------|
| **AllBots** | Competitor analysis, bots, shop health, SKU mgmt | 49 | Shopee_Comp (45K), history_logs (101K), Shopee_VariationSalesDaily (80K) |
| **requestDatabase** | Core ops: inventory, orders, returns, claims, costing | 89 | Sales60 (282K), products (39K), New1688Orders (21K) |
| **TiktokDatabase** | TikTok Shop ops (sales, ratings, health) | 13 | Sales (79K), Sales30 (75K) |
| **ShopeeDatabase** | Legacy — only CS_EMPLOYEE remains | 1 | CS_EMPLOYEE (3) |
| **webapp_test** | Test mirror — schemas only, all data truncated | 68 | All empty (truncated 2026-02-17) |

**Removed databases**: `nocodb_meta` (dropped 2026-02-17 — abandoned NocoDB trial)

---

## Key Tables by Domain

### A. Competitor Analysis

| Table | DB | Rows | Key Columns |
|-------|-----|------|-------------|
| **Shopee_Comp** | AllBots | 45K | product_name, sku, our_price/sales/stock, comp_price/sales/stock, ads_spend/roas (7d-90d), product_similarity_score, status |
| **Shopee_Comp_Group_Summary** | AllBots | 3.1K | PK: (status, product_name). Aggregated sales totals |
| **Shopee_Comp_Remarks** | AllBots | 45K | comp_id -> Shopee_Comp.id, remark, source (user/auto) |
| **Tiktok_Comp** | AllBots | 202 | own/comp URLs, prices, sold_count, matched variations |

### B. Inventory & Stock

| Table | DB | Rows | Key Columns |
|-------|-----|------|-------------|
| **Inventory** | requestDatabase | 14K | PK: id, UNIQUE: SKU. Stock, Cost, product_name, shopee_stores (JSON), label |
| **inventory_parent_labels** | requestDatabase | 23 | PK: parent_sku. label, date range |
| **fbs_stock** | requestDatabase | 878 | FBS stock: shop, variation, isku, total_sellable, cost_per_unit |
| **costing_excel** | requestDatabase | 13K | yuan, china_shipping, local, selling_price, cbm, container |
| **Shopee_VariationSalesDaily** | AllBots | 80K | PK: (shop_id, model_id, sale_date). units_sold, orders_count |

### C. Order Management

| Table | DB | Rows | Key Columns |
|-------|-----|------|-------------|
| **New1688Orders** | requestDatabase | 21K | Order_Date, Product, Sku, Quantity, Total_Cost, Order_Status, Container, Stock_Arrival |
| **order_management_sg** | requestDatabase | 1.3K | Same schema as New1688Orders (SG region) |
| **SB_Variation** | requestDatabase | 1.3K | Ship-By variation issues: Order_ID, SKU (JSON), Case_Type (JSON), Buyer_Decision (JSON) |

### D. Sales Data

| Table | DB | Rows | Key Columns |
|-------|-----|------|-------------|
| **Sales60** | requestDatabase | 282K | Combined 60-day sales: status, sku, quantity, date |
| **Sales** | TiktokDatabase | 79K | TikTok full sales with customer data |
| **Sales30** | TiktokDatabase | 75K | TikTok 30-day trimmed |

### E. Customer Service & Returns

| Table | DB | Rows | Key Columns |
|-------|-----|------|-------------|
| **CS_EMPLOYEE** | ShopeeDatabase | 3 | Employee_Name — used by parcel claim pages (MY, SG, TikTok) |
| **Return_Request** | requestDatabase | 9.5K | platform, shop_name, return_type, product (JSON), category/sub_category |
| **Repair_Request** | requestDatabase | 207 | repair_date, purpose, issue, repaired_part, media (JSON) |
| **replacement_review** | requestDatabase | 965 | stage (JSON), review_status, tracking_status |
| **NEWParcelclaim** | requestDatabase | 1.7K | UNIQUE: order_id. dispute_status, compensation_amount |
| **NEWParcelclaim_sg** | requestDatabase | 380 | Same schema (SG) |
| **NEWParcelclaim_tiktok** | requestDatabase | 624 | Same schema (TikTok) |
| **Evidence_Request** | requestDatabase | 261 | UNIQUE: evidence_id. damage_type, media, status |
| **ParcelSplit** | requestDatabase | 1.7K | Split shipments: order_id, shipped_item, tracking_number |
| **tracking_list** | requestDatabase | 1.9K | CS case tracking: case_type, status, log (JSON) |

### F. Account Health

| Table | DB | Rows | Key Columns |
|-------|-----|------|-------------|
| **account_health_shopeemy** | requestDatabase | 1.4K | Daily: late_shipment_rate, response_rate, shop_rating, penalty_points |
| **account_health_shopeesg** | requestDatabase | 256 | Same (SG) |
| **account_health_tiktok** | requestDatabase | 323 | Extra: response_rate_12h, chat_satisfaction_rate |

### G. Products & SKU Reference

| Table | DB | Rows | Key Columns |
|-------|-----|------|-------------|
| **products** | requestDatabase | 39K | Master catalog: product_name, variation_name, sku |
| **product_reference** | requestDatabase | 1.9K | Chinese-to-English product name mapping |
| **product_variation_reference** | requestDatabase | 12.8K | product, variation, sku, shopee_variation |
| **sku_management** | AllBots | 26K | SKU-to-shop mapping: Product_Name, SKU, Shop |
| **new_items** | requestDatabase | 438 | New product pipeline: status, product_name, parent_sku, variation lists (JSON) |
| **shopee_listings** | requestDatabase | 923 | Listing pipeline: 1688 data + n8n pipeline columns (n8n_variation, n8n_description) |

### H. Pricing & Exchange

| Table | DB | Rows | Key Columns |
|-------|-----|------|-------------|
| **PriceOptimize** | requestDatabase | 1.6K | price, comp_price, adjustment, reason, status |
| **shop_vouchers** | AllBots | 18 | voucher_name, discount_type/value, is_active |
| **ui_rate** | requestDatabase | 2 | CNY-to-MYR exchange rate |

### I. Containers (China-to-Malaysia Shipping)

| Table | DB | Rows | Key Columns |
|-------|-----|------|-------------|
| **containers** | requestDatabase | 78 | container_code, china_warehouse, status |
| **container_items** | requestDatabase | 12.6K | FK: container_id -> containers.id. order_id, product_name, units |

### J. Chatbot Data (AllBots)

| Table | DB | Rows | Key Columns |
|-------|-----|------|-------------|
| **chatbot_conversations** | AllBots | -- | Chatbot conversation tracking |
| **chatbot_messages** | AllBots | -- | Chatbot message storage |

### K. TikTok Health & Ratings

| Table | DB | Rows | Key Columns |
|-------|-----|------|-------------|
| **tiktok_health_metrics** | AllBots | -- | TikTok health metric snapshots |
| **LowRatings** | TiktokDatabase | 590 | Active low ratings (written by Tiktok_LR.py on VM TT) |
| **LowRatingsExpire** | TiktokDatabase | 184 | Expired/archived low ratings |
| **LowRatingsChanged** | TiktokDatabase | 0 | Improved ratings staging |
| **TikTokComp** | TiktokDatabase | 1.1K | TikTok competitor data |
| **Claculation** | TiktokDatabase | 11K | TikTok fee calculations |
| **SKU_Input** | TiktokDatabase | 11K | TikTok SKU input data |

### L. Shopee Automation

| Table | DB | Rows | Key Columns |
|-------|-----|------|-------------|
| **ShopeeAutomationLoop** | requestDatabase | 1 | Loop state: status, next_run_time, interval_minutes |
| **ShopeeAutomationLoopStats** | requestDatabase | 1 | Cycle stats: total_cycles, successful/failed |
| **ShopeeAutomationRuns** | requestDatabase | 3 | Run history: run_id, status, total_shops, triggered_by |
| **ShopeeAutomationShops** | requestDatabase | 65 | Per-shop run details: FK run_id, shop_id, records_processed |
| **ShopeeAutomationLogs** | requestDatabase | 2 | Automation log entries |

### M. System & Audit

| Table | DB | Rows | Key Columns |
|-------|-----|------|-------------|
| **ShopeeTokens** | requestDatabase | 34 | UNIQUE: shop_id. access_token, refresh_token, expires_at, region |
| **audit_log** | requestDatabase | 0 | table_name, operation_type, old/new_values (JSON) — truncated 2026-02-17 |
| **history_logs** | AllBots | 101K | model_name, action, previous/new_data (JSON), firebase_email |
| **edit_logs** | requestDatabase | 20K | Field-level: table_edited, field_name, old/new_value, edited_by |
| **user_profiles** | AllBots | 45 | Firebase accounts: firebase_uid, email, role, department |

---

## Key Relationships

### Explicit Foreign Keys
```
container_items.container_id -> containers.id
ShopeeAutomationShops.run_id -> ShopeeAutomationRuns.run_id
price_audit_log.price_optimize_id -> PriceOptimize.id
```

### Critical Logical Joins (by SKU)
```
Inventory.SKU = New1688Orders.Sku = costing_excel.sku = Sales60.sku
             = products.sku = Shopee_Comp.sku = sku_management.SKU

shop_id: ShopeeTokens.shop_id = Shopee_Comp.our_shop_id = account_health_shopeemy.shop_id

product_name: Shopee_Comp.product_name = Shopee_Comp_Group_Summary.product_name = Inventory.product_name

parent_sku: Inventory.parent_sku = inventory_parent_labels.parent_sku = New1688Orders.parent_sku

new_items pipeline: new_items.id = shopee_listings.product_id
```

---

## Common Query Patterns

### Inventory + Costing
```sql
SELECT i.SKU, i.product_name, i.Stock, i.Cost, c.yuan, c.selling_price, c.cbm
FROM requestDatabase.Inventory i
LEFT JOIN requestDatabase.costing_excel c ON i.SKU = c.sku
WHERE i.Stock > 0
```

### Competitor with Remarks
```sql
SELECT sc.id, sc.product_name, sc.sku, sc.our_price, sc.comp_price,
       sc.our_sales_30d, GROUP_CONCAT(scr.remark) AS remarks
FROM AllBots.Shopee_Comp sc
LEFT JOIN AllBots.Shopee_Comp_Remarks scr ON sc.id = scr.comp_id
WHERE sc.status = 'Active' GROUP BY sc.id
```

### Sales by SKU
```sql
SELECT sku, SUM(quantity) AS total_sold
FROM requestDatabase.Sales60
WHERE date >= '2026-01-15' GROUP BY sku ORDER BY total_sold DESC
```

### Account Health Trend
```sql
SELECT metric_date, shop_name, late_shipment_rate, response_rate, shop_rating
FROM requestDatabase.account_health_shopeemy
WHERE metric_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY shop_name, metric_date
```

### 1688 Orders with Container
```sql
SELECT o.Order_Date, o.Product, o.Sku, o.Quantity, o.Total_Cost,
       o.Container, c.status AS container_status
FROM requestDatabase.New1688Orders o
LEFT JOIN requestDatabase.containers c ON o.Container = c.container_code
WHERE o.archived = 0
```

### Token Validity Check
```sql
SELECT shop_name, region, FROM_UNIXTIME(expires_at) AS token_expires
FROM requestDatabase.ShopeeTokens WHERE expires_at < UNIX_TIMESTAMP()
```

### Exchange Rate
```sql
SELECT rate FROM requestDatabase.ui_rate WHERE id = 1
```

---

## Important Notes

- **webapp_test** is a test mirror — all data truncated 2026-02-17. Schemas preserved for dev testing. Should use seed data, not production copies.
- **ShopeeDatabase** is legacy — only `CS_EMPLOYEE` (3 rows) remains. Used by parcel claim pages. All other tables dropped 2026-02-17.
- **Column naming is inconsistent**: snake_case, PascalCase, and spaces in column names
- **Do NOT create backup tables inside the database** — use `mysqldump` to `.sql` file in GCS instead
- **34 Shopee shops** registered (27 MY + 7 SG) in ShopeeTokens
- **JSON columns** used extensively: SB_Variation, new_items, Return_Request, installation_roster
- **installation_roster** stores base64 photos in JSON (~600 KB/row) — backlog item to migrate to GCS
- **testShopee_* tables** (7 tables, 21 MB) in requestDatabase — kept under 90-day rule, review by 2026-05-16
- **Audit performed**: 2026-02-17. Dropped 108 tables, truncated 61, removed nocodb_meta database. ~1.5 GB freed.
