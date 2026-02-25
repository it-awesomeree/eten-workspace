# -*- coding: utf-8 -*-

"""
Fetch Shopee product details (description, variation names, variation images)
for products from requestDatabase.new_items where launch_type = 'New Variation'.

DRY RUN MODE - Only prints output, does not store to database.
"""

import sys
import io
import time
import os

# Fix Windows console encoding for Unicode characters in API responses
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import hmac
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import mysql.connector
from mysql.connector import Error as MySQLError


# =========================
# CONFIGURATION
# =========================

HOST = "https://partner.shopeemobile.com"

PARTNER_ID = 2012161
_TMP_KEY = os.environ["SHOPEE_PARTNER_KEY"]
PARTNER_KEY = _TMP_KEY.encode()

# API paths
PATH_ITEM_BASE_INFO = "/api/v2/product/get_item_base_info"
PATH_GET_MODEL_LIST = "/api/v2/product/get_model_list"

# Database config
DB_CFG = dict(
    host=os.environ.get("DB_HOST", "localhost"),
    user="root",
    password=os.environ["DB_PASSWORD"],
    database="requestDatabase",
)

# DRY RUN - no database writes
DRY_RUN = False


# =========================
# SHOPEE SIGNING & API
# =========================

def _sign(path: str, token: str, shop_id: int, timestamp: int) -> str:
    """Generate Shopee API signature."""
    base_string = f"{PARTNER_ID}{path}{timestamp}{token}{shop_id}".encode()
    return hmac.new(PARTNER_KEY, base_string, hashlib.sha256).hexdigest()


def fetch_item_base_info(shop_id: int, access_token: str, item_ids: List[int]) -> Dict[str, Any]:
    """
    Fetch product base info from Shopee API.
    Can fetch up to 50 items at once.
    """
    ts = int(time.time())
    sign = _sign(PATH_ITEM_BASE_INFO, access_token, shop_id, ts)

    # Convert item_ids list to comma-separated string
    item_id_str = ",".join(str(i) for i in item_ids)

    # Request specific fields so the API returns description & variation data
    fields = "item_id,item_name,description,image,tier_variation"

    url = (
        f"{HOST}{PATH_ITEM_BASE_INFO}"
        f"?sign={sign}"
        f"&shop_id={shop_id}"
        f"&partner_id={PARTNER_ID}"
        f"&access_token={access_token}"
        f"&timestamp={ts}"
        f"&item_id_list={item_id_str}"
        f"&need_tax_info=false"
        f"&need_complaint_policy=false"
        f"&fields={fields}"
    )

    print(f"[DEBUG] Calling Shopee API for {len(item_ids)} item(s)...")

    resp = requests.get(url, headers={"Accept": "application/json"}, timeout=30)

    try:
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Shopee HTTP {resp.status_code}: {e} {resp.text}")

    data = resp.json()

    # Check for API errors
    error = data.get("error")
    if error and error != "" and error != 0:
        raise RuntimeError(f"Shopee API error: {error} - {data.get('message')}")

    return data.get("response") or {}


def fetch_model_list(shop_id: int, access_token: str, item_id: int) -> Dict[str, Any]:
    """
    Fetch model/variation list for a single item from Shopee API.
    Returns tier_variation (names + images) and model list.
    """
    ts = int(time.time())
    sign = _sign(PATH_GET_MODEL_LIST, access_token, shop_id, ts)

    url = (
        f"{HOST}{PATH_GET_MODEL_LIST}"
        f"?sign={sign}"
        f"&shop_id={shop_id}"
        f"&partner_id={PARTNER_ID}"
        f"&access_token={access_token}"
        f"&timestamp={ts}"
        f"&item_id={item_id}"
    )

    resp = requests.get(url, headers={"Accept": "application/json"}, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    error = data.get("error")
    if error and error != "" and error != 0:
        raise RuntimeError(f"Shopee API error: {error} - {data.get('message')}")

    return data.get("response") or {}


def parse_product_details(item: Dict[str, Any], model_response: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Parse item response to extract description, variation names, and variation images.
    Description comes from description_info.extended_description.
    Variations come from the get_model_list response.
    """
    item_id = item.get("item_id")
    item_name = item.get("item_name", "")

    # Extract description from extended_description field_list
    description = ""
    desc_info = item.get("description_info") or {}
    ext_desc = desc_info.get("extended_description") or {}
    field_list = ext_desc.get("field_list") or []
    text_parts = [f.get("text", "") for f in field_list if f.get("field_type") == "text"]
    if text_parts:
        description = "\n".join(text_parts)
    else:
        # Fallback to plain description field
        description = item.get("description", "")

    # Variations from get_model_list response
    tier_variations = (model_response or {}).get("tier_variation") or []

    result = {
        "item_id": item_id,
        "item_name": item_name,
        "description": description,
        "variations": []
    }

    for tier in tier_variations:
        tier_name = tier.get("name", "")  # e.g., "Color", "Size"
        options = tier.get("option_list") or []

        variation_data = {
            "tier_name": tier_name,
            "options": []
        }

        for opt in options:
            option_info = {
                "option_name": opt.get("option", ""),
                "image_url": None
            }

            image = opt.get("image")
            if image:
                option_info["image_url"] = image.get("image_url")

            variation_data["options"].append(option_info)

        result["variations"].append(variation_data)

    return result


# =========================
# DATABASE HELPERS
# =========================

def get_db_connection():
    """Create database connection."""
    return mysql.connector.connect(**DB_CFG)


def fetch_active_shops() -> Dict[int, Dict[str, Any]]:
    """
    Load active shops and tokens from requestDatabase.ShopeeTokens.
    Returns dict keyed by shop_id for easy lookup.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT shop_id, shop_name, access_token
            FROM requestDatabase.ShopeeTokens
            WHERE access_token IS NOT NULL
              AND access_token <> ''
              AND (expires_at IS NULL OR expires_at > UNIX_TIMESTAMP())
            """
        )
        rows = cursor.fetchall()
        shops: Dict[int, Dict[str, Any]] = {}
        for shop_id, shop_name, token in rows:
            shops[int(shop_id)] = {
                "shop_id": int(shop_id),
                "shop_name": (shop_name or "").strip(),
                "access_token": (token or "").strip(),
            }
        print(f"[INFO] Loaded {len(shops)} active shop token(s)")
        return shops
    finally:
        cursor.close()
        conn.close()


def fetch_new_variation_items() -> List[Dict[str, Any]]:
    """
    Fetch product_id from new_items where launch_type = 'New Variation'.
    Joins with ShopeeTokens to resolve shop name -> shop_id.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT ni.id, ni.product_id, st.shop_id, ni.product_name_en, ni.launch_type
            FROM requestDatabase.new_items ni
            LEFT JOIN requestDatabase.ShopeeTokens st
              ON ni.shop = st.shop_name COLLATE utf8mb4_0900_ai_ci
            WHERE ni.launch_type = 'New Variation'
              AND ni.product_id IS NOT NULL
            """
        )
        rows = cursor.fetchall()
        items: List[Dict[str, Any]] = []
        for row_id, product_id, shop_id, product_name, launch_type in rows:
            items.append({
                "row_id": row_id,
                "product_id": int(product_id) if product_id else None,
                "shop_id": int(shop_id) if shop_id else None,
                "product_name": (product_name or "").strip(),
                "launch_type": launch_type,
            })
        print(f"[INFO] Found {len(items)} item(s) with launch_type = 'New Variation'")
        return items
    finally:
        cursor.close()
        conn.close()


DB_CFG_WEBAPP = dict(
    host=os.environ.get("DB_HOST", "localhost"),
    user="root",
    password=os.environ["DB_PASSWORD"],
    database="requestDatabase",
)


def save_to_db(shop_name: str, details: Dict[str, Any], new_item_id: int) -> None:
    """Update product details in shopee_listing_products by new_item_id."""
    conn = mysql.connector.connect(**DB_CFG_WEBAPP)
    cursor = conn.cursor()
    try:
        variations = details.get("variations") or []

        # Tier 1
        tier_name_1 = variations[0]["tier_name"] if len(variations) > 0 else None
        t1_variation = json.dumps(
            [opt["option_name"] for opt in variations[0]["options"]]
        ) if len(variations) > 0 else None
        variation_images = json.dumps(
            [opt["image_url"] for opt in variations[0]["options"] if opt.get("image_url")]
        ) if len(variations) > 0 else None

        # Tier 2
        tier_name_2 = variations[1]["tier_name"] if len(variations) > 1 else None
        t2_variation = json.dumps(
            [opt["option_name"] for opt in variations[1]["options"]]
        ) if len(variations) > 1 else None

        cursor.execute(
            """
            UPDATE shopee_listing_products
            SET shopee_product_name = %s,
                shopee_description = %s,
                tier_name_1 = %s,
                t1_variation = %s,
                shopee_variation_images = %s,
                tier_name_2 = %s,
                t2_variation = %s
            WHERE new_item_id = %s
            """,
            (
                details["item_name"],
                details["description"],
                tier_name_1,
                t1_variation,
                variation_images,
                tier_name_2,
                t2_variation,
                new_item_id,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()


# =========================
# MAIN LOGIC
# =========================

def print_product_details(details: Dict[str, Any]) -> None:
    """Pretty print product details."""
    print("\n" + "=" * 80)
    print(f"ITEM ID: {details['item_id']}")
    print(f"ITEM NAME: {details['item_name']}")
    print("-" * 80)

    print("\nDESCRIPTION:")
    desc = details['description']
    if len(desc) > 500:
        print(f"{desc[:500]}...\n[truncated, total {len(desc)} chars]")
    else:
        print(desc if desc else "(No description)")

    print("\nVARIATIONS:")
    if not details['variations']:
        print("  (No variations)")
    else:
        for var in details['variations']:
            print(f"\n  [{var['tier_name']}]")
            for opt in var['options']:
                img_status = f"[Y] {opt['image_url']}" if opt['image_url'] else "[N] No image"
                print(f"    \u2022 {opt['option_name']}")
                print(f"      Image: {img_status}")

    print("=" * 80)


def main():
    print(f"\n{'='*60}")
    print("SHOPEE PRODUCT VARIATION FETCHER")
    print(f"Mode: {'DRY RUN (no DB writes)' if DRY_RUN else 'LIVE'}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Step 1: Load active shops (for access tokens)
    shops = fetch_active_shops()
    if not shops:
        print("[ERROR] No active shops found. Exiting.")
        sys.exit(1)

    # Step 2: Fetch items from new_items where launch_type = 'New Variation'
    items = fetch_new_variation_items()
    if not items:
        print("[WARN] No items with launch_type = 'New Variation' found. Exiting.")
        sys.exit(0)

    # Step 3: Group items by shop_id for batch processing
    items_by_shop: Dict[int, List[Dict[str, Any]]] = {}
    skipped_items = []

    for item in items:
        shop_id = item.get("shop_id")
        product_id = item.get("product_id")

        if not shop_id or not product_id:
            skipped_items.append(item)
            continue

        if shop_id not in shops:
            print(f"[WARN] No token found for shop_id={shop_id}, skipping product_id={product_id}")
            skipped_items.append(item)
            continue

        if shop_id not in items_by_shop:
            items_by_shop[shop_id] = []
        items_by_shop[shop_id].append(item)

    if skipped_items:
        print(f"[WARN] Skipped {len(skipped_items)} item(s) due to missing shop_id or token")

    # Step 4: Process each shop's items
    all_results = []

    for shop_id, shop_items in items_by_shop.items():
        shop = shops[shop_id]
        shop_name = shop["shop_name"]
        access_token = shop["access_token"]

        print(f"\n[INFO] Processing shop: {shop_name} (shop_id={shop_id})")
        print(f"[INFO] Items to fetch: {len(shop_items)}")

        # Build mapping from product_id to original items (for new_item_id lookup)
        pid_to_items: Dict[int, List[Dict[str, Any]]] = {}
        for item in shop_items:
            pid = item["product_id"]
            pid_to_items.setdefault(pid, []).append(item)
        unique_product_ids = list(pid_to_items.keys())

        # Batch in groups of 50 (Shopee API limit)
        batch_size = 50
        for i in range(0, len(unique_product_ids), batch_size):
            batch = unique_product_ids[i:i + batch_size]

            try:
                response = fetch_item_base_info(shop_id, access_token, batch)
                item_list = response.get("item_list") or []

                print(f"[INFO] Received {len(item_list)} item(s) from API")

                for item_data in item_list:
                    # Fetch variation/model data per item
                    model_resp = None
                    if item_data.get("has_model"):
                        try:
                            model_resp = fetch_model_list(shop_id, access_token, item_data["item_id"])
                        except Exception as me:
                            print(f"[WARN] Failed to fetch models for item {item_data['item_id']}: {me}")

                    details = parse_product_details(item_data, model_resp)
                    all_results.append({
                        "shop_id": shop_id,
                        "shop_name": shop_name,
                        "details": details
                    })

                    print_product_details(details)

                    if not DRY_RUN:
                        # Update all shopee_listing_products rows for this product_id
                        matching_items = pid_to_items.get(details['item_id'], [])
                        for orig_item in matching_items:
                            try:
                                updated = save_to_db(shop_name, details, orig_item["row_id"])
                                if updated:
                                    print(f"[DB] Updated new_item_id={orig_item['row_id']} (product_id={details['item_id']})")
                                else:
                                    print(f"[DB] Skipped new_item_id={orig_item['row_id']} (no matching row)")
                            except Exception as db_err:
                                print(f"[DB ERROR] Failed to save new_item_id={orig_item['row_id']}: {db_err}")

                # Rate limiting - be nice to Shopee API
                if i + batch_size < len(unique_product_ids):
                    print("[INFO] Waiting 1 second before next batch...")
                    time.sleep(1)

            except Exception as e:
                print(f"[ERROR] Failed to fetch batch for shop_id={shop_id}: {e}")
                continue

    # Step 5: Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total items processed: {len(all_results)}")
    print(f"Total items skipped: {len(skipped_items)}")

    if DRY_RUN:
        print("\n[DRY RUN] No data was written to database.")
    else:
        print(f"\n[INFO] Data saved to requestDatabase.shopee_listing_products")


if __name__ == "__main__":
    main()
