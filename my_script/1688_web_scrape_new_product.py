import mysql.connector
import time
import logging
import sys
import os
import json
import requests
import re
import random
import subprocess

# Fix Windows console encoding for Chinese characters
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass  # Fallback if reconfigure not available

# Fix for Python 3.12+ (distutils was removed)
import setuptools

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, InvalidSessionIdException
from urllib3.exceptions import ReadTimeoutError
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# --- Human-Like Delay ---
def human_delay(min_s, max_s):
    """Sleep for a random duration to mimic human behavior."""
    delay = random.uniform(min_s, max_s)
    time.sleep(delay)


# --- Simulate Idle Browsing ---
def simulate_idle_browsing(driver):
    """Randomly scroll and pause to break predictable navigation patterns."""
    try:
        scroll_distance = random.randint(200, 800)
        direction = random.choice([1, -1])
        driver.execute_script(f"window.scrollBy(0, {scroll_distance * direction});")
        human_delay(1, 3)
        driver.execute_script(f"window.scrollBy(0, {random.randint(100, 400) * -direction});")
        human_delay(0.5, 2)
    except Exception:
        pass


# --- Humanized Mouse Movement ---
def human_move_and_click(driver, x, y, click=True):
    """Move to coordinates with slight jitter and optional click."""
    jitter_x = random.randint(-3, 3)
    jitter_y = random.randint(-3, 3)
    actions = ActionChains(driver)
    actions.move_by_offset(int(x) + jitter_x, int(y) + jitter_y)
    if click:
        human_delay(0.05, 0.2)
        actions.click()
    actions.perform()
    actions.reset_actions()


# --- Driver Setup (using undetected-chromedriver) ---
def _detect_chrome_major_version() -> int | None:
    """
    Best-effort detection of the installed Chrome major version.

    Used to keep `undetected_chromedriver`'s `version_main` in sync with the
    locally installed browser so we don't hit SessionNotCreatedException from
    Chrome/ChromeDriver mismatches.
    """
    # Windows: read version from registry (works even when Chrome is running)
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
            version, _ = winreg.QueryValueEx(key, "version")
            winreg.CloseKey(key)
            m = re.search(r"(\d+)\.", version)
            if m:
                return int(m.group(1))
        except Exception:
            pass

    # Fallback: chrome --version (works on Linux/Mac, fails on Windows when Chrome is open)
    try:
        chrome_path = uc.find_chrome_executable()
        if not chrome_path:
            return None
        out = subprocess.check_output(
            [chrome_path, "--version"],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()
        m = re.search(r"(\d+)\.", out)
        return int(m.group(1)) if m else None
    except Exception:
        return None


def setup_driver(profile_path):
    options = uc.ChromeOptions()

    # Profile settings
    options.add_argument(f'--user-data-dir={profile_path}')
    options.add_argument('--profile-directory=Profile 1')
    options.add_argument('--start-maximized')

    # Hardcode Chrome major version to match installed browser.
    # Update this number when Chrome updates.
    driver = uc.Chrome(options=options, version_main=145, patcher_force_close=True)

    return driver


# --- Session Health Check ---
def is_dead_session(e: Exception) -> bool:
    """Check if exception indicates a dead/crashed browser session."""
    msg = str(e).lower()
    return (
        isinstance(e, InvalidSessionIdException)
        or "invalid session id" in msg
        or "not connected to devtools" in msg
        or "session deleted" in msg
        or "disconnected" in msg
        or "chrome not reachable" in msg
    )


# --- Safe Navigation with Timeout Handling ---
def safe_get(driver, url, page_timeout=45, retries=2, rebuild_driver_fn=None):
    """Navigate to URL with timeout handling, retries, and optional driver rebuild."""
    driver.set_page_load_timeout(page_timeout)

    last_err = None
    for attempt in range(retries + 1):
        try:
            driver.get(url)
            return driver  # Return driver (may be rebuilt)

        except TimeoutException:
            # Page is still loading; stop loading and let explicit waits take over
            try:
                driver.execute_script("window.stop();")
            except Exception:
                pass
            return driver

        except (ReadTimeoutError, WebDriverException, InvalidSessionIdException) as e:
            # Check if session is dead and needs rebuild
            if is_dead_session(e) and rebuild_driver_fn:
                print(f"  [WARN] Browser session crashed, rebuilding driver...")
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = rebuild_driver_fn()
                driver.set_page_load_timeout(page_timeout)
                # Try once more with new driver
                try:
                    driver.get(url)
                    return driver
                except Exception as e2:
                    print(f"  [ERROR] Failed after rebuild: {e2}")
                    raise e2

            last_err = e
            # chromedriver/browser may be temporarily stuck; retry
            if attempt < retries:
                print(f"  [WARN] Navigation timeout, retrying... (attempt {attempt + 1}/{retries})")
                human_delay(2, 5)
                continue
            raise last_err

    return driver

# --- Check if 1688 is Logged Out ---
def check_1688_login(driver):
    """Check if user is logged in to 1688. Returns True if logged in."""
    try:
        # Navigate to order list page
        url = "https://air.1688.com/app/ctf-page/trade-order-list/buyer-order-list.html?spm=a260k.home2025.leftmenu_EXPEND.dorder&page=1&pageSize=10"
        safe_get(driver, url)
        human_delay(8, 15)

        # Check for login modal/popup - try multiple methods
        login_detected = False

        # Method 1: Check for login modal elements in main page
        # <input name="fm-sms-login-id" class="fm-text" id="fm-sms-login-id" placeholder="\u8bf7\u8f93\u5165\u624b\u673a\u53f7">
        # <button class="fm-button fm-submit sms-login button-low-light">\u767b\u5f55</button>
        login_selectors = [
            'input[name="fm-sms-login-id"]',
            'input#fm-sms-login-id',
            'input[placeholder="\u8bf7\u8f93\u5165\u624b\u673a\u53f7"]',
            'button.fm-submit.sms-login',
            'button.fm-button.fm-submit',
            '.fm-login',
            '#login-form',
            'input.fm-text[type="text"]'
        ]

        for selector in login_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 0:
                    print(f"[DEBUG] Found login element with selector: {selector}")
                    login_detected = True
                    break
            except:
                continue

        # Method 2: Check if inside an iframe
        if not login_detected:
            try:
                iframes = driver.find_elements(By.TAG_NAME, 'iframe')
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        for selector in login_selectors:
                            try:
                                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                if elements and len(elements) > 0:
                                    print(f"[DEBUG] Found login element in iframe with selector: {selector}")
                                    login_detected = True
                                    break
                            except:
                                continue
                        driver.switch_to.default_content()
                        if login_detected:
                            break
                    except:
                        driver.switch_to.default_content()
                        continue
            except:
                driver.switch_to.default_content()

        # Method 3: Check URL for login redirect
        current_url = driver.current_url.lower()
        if "login" in current_url or "passport" in current_url:
            print(f"[DEBUG] URL contains login/passport: {current_url}")
            login_detected = True

        # Method 4: Check page source for login form
        if not login_detected:
            try:
                page_source = driver.page_source
                if '\u8bf7\u8f93\u5165\u624b\u673a\u53f7' in page_source or 'fm-sms-login-id' in page_source or 'fm-submit' in page_source:
                    print("[DEBUG] Found login text in page source")
                    login_detected = True
            except:
                pass

        # If login detected, let user login manually
        if login_detected:
            logging.warning("1688 login modal detected!")
            print("\n" + "="*60)
            print("[WARNING] 1688 is NOT logged in!")
            print("="*60)
            print("\nPlease login manually in the browser window.")
            print("(Note: If CAPTCHA fails, you may need to login in normal Chrome first)")
            print("="*60)


            # Navigate back to order list after login
            safe_get(driver, url)
            human_delay(4, 8)

            # Check again if still showing login
            page_source = driver.page_source
            current_url = driver.current_url.lower()
            if '\u8bf7\u8f93\u5165\u624b\u673a\u53f7' in page_source or 'fm-sms-login-id' in page_source or "login" in current_url:
                print("[ERROR] Still not logged in. Exiting.")
                return False

        print("[OK] 1688 is logged in.")
        return True

    except Exception as e:
        logging.error(f"Error checking 1688 login: {e}")
        import traceback
        traceback.print_exc()
        return False

# --- Download Image ---
def download_image(url, filepath):
    """Download image from URL and save to filepath. Returns True on success."""
    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to download image: {e}")
        return False


# --- Sanitize Filename ---
def sanitize_filename(name):
    """Remove invalid characters from filename."""
    # Remove characters that are invalid in Windows filenames
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', name)
    # Limit length
    return sanitized[:100] if len(sanitized) > 100 else sanitized


# --- Database Connection ---
def connect_db():
    """Connect to requestDatabase for reading product data."""
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user="root",
        password=os.environ["DB_PASSWORD"],
        database="requestDatabase",
        port=3306
    )


def connect_target_db():
    """Connect to requestDatabase for writing."""
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user="root",
        password=os.environ["DB_PASSWORD"],
        database="requestDatabase",
        port=3306
    )


def insert_shopee_listings(product_id, product_name, reference_links, launch_type, variation_names, variation_imgs, gallery_urls, description_imgs, description_txt, item_date=None):
    """
    Insert scraped data into shopee_listing_products + shopee_listing_variations.
    """
    conn = connect_target_db()

    try:
        cursor = conn.cursor()

        # Prepare shared data
        hero_img = gallery_urls[0] if gallery_urls else None
        supporting_imgs = json.dumps(gallery_urls[1:]) if gallery_urls and len(gallery_urls) > 1 else None
        desc_imgs_json = json.dumps(description_imgs) if description_imgs else None

        # Extract first URL from reference_links JSON
        url_1688 = None
        if reference_links:
            try:
                links = json.loads(reference_links) if isinstance(reference_links, str) else reference_links
                if isinstance(links, list) and len(links) > 0:
                    url_1688 = links[0]
                elif isinstance(links, str):
                    url_1688 = links
            except (json.JSONDecodeError, TypeError):
                url_1688 = str(reference_links)

        # 1. Insert product row into shopee_listing_products
        query_product = """
            INSERT INTO shopee_listing_products
                (product_id, launch_type, item_type, `1688_url`, `1688_product_name`,
                 `1688_hero`, `1688_supporting_image`,
                 `1688_product_description_text`, `1688_product_description_image`,
                 item_date, status)
            VALUES (%s, %s, 'new_product', %s, %s, %s, %s, %s, %s, %s, 'bot')
            ON DUPLICATE KEY UPDATE
                `1688_url` = VALUES(`1688_url`),
                `1688_product_name` = VALUES(`1688_product_name`),
                `1688_hero` = VALUES(`1688_hero`),
                `1688_supporting_image` = VALUES(`1688_supporting_image`),
                `1688_product_description_text` = VALUES(`1688_product_description_text`),
                `1688_product_description_image` = VALUES(`1688_product_description_image`),
                item_date = VALUES(item_date)
        """
        cursor.execute(query_product, (
            product_id, launch_type, url_1688, product_name,
            hero_img, supporting_imgs, description_txt, desc_imgs_json, item_date,
        ))

        # 2. Insert variation rows
        rows_inserted = 0
        cursor.execute("DELETE FROM shopee_listing_variations WHERE product_id = %s", (product_id,))

        if variation_names and len(variation_names) > 0:
            for i, var_name in enumerate(variation_names):
                var_img = variation_imgs[i] if variation_imgs and len(variation_imgs) > i else None
                cursor.execute("""
                    INSERT INTO shopee_listing_variations
                        (product_id, sort_order, `1688_variation`, `1688_variation_image`)
                    VALUES (%s, %s, %s, %s)
                """, (product_id, i, var_name, var_img))
                rows_inserted += 1

        conn.commit()
        cursor.close()

        print(f"  [DB] Inserted 1 product + {rows_inserted} variation(s) for: {product_name}")
        print(f"       - hero + {len(gallery_urls) - 1 if gallery_urls and len(gallery_urls) > 1 else 0} supporting images")
        print(f"       - {len(variation_names) if variation_names else 0} variations")
        print(f"       - {len(description_imgs) if description_imgs else 0} description images")
        return rows_inserted

    except Exception as e:
        print(f"  [DB] Error: {e}")
        return 0
    finally:
        conn.close()


def get_product_names_from_db():
    """Fetch product_id, product_name_cn, variation_list_cn, and reference_links from new_items,
    excluding products already scraped in shopee_listings table."""
    conn = None
    try:
        conn = connect_target_db()
        cursor = conn.cursor()
        # Query products that haven't been scraped yet (not in shopee_listings)
        query = """
            SELECT ni.product_id, ni.product_name_cn, ni.variation_list_cn, ni.reference_links, ni.launch_type, DATE(ni.date) AS item_date
            FROM new_items ni
            WHERE ni.product_name_cn IS NOT NULL
              AND ni.product_name_cn != ''
              AND ni.launch_type = 'New Product'
              AND ni.product_id NOT IN (
                  SELECT product_id FROM shopee_listing_products WHERE product_id IS NOT NULL
              )
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        # Return list of tuples: (product_id, product_name, variation_list_cn, reference_links, launch_type, item_date)
        products = [(row[0], row[1], row[2], row[3], row[4], row[5]) for row in rows if row[0] and row[1]]
        print(f"Found {len(products)} products to scrape (excluding already scraped).")
        return products
    except Exception as e:
        print(f"Error fetching products from DB: {e}")
        return []
    finally:
        if conn:
            conn.close()

# --- Navigate to 1688 Order List ---
def navigate_to_order_list(driver, rebuild_driver_fn=None):
    """Navigate to the 1688 order list page. Returns driver (may be rebuilt)."""
    url = "https://air.1688.com/app/ctf-page/trade-order-list/buyer-order-list.html?spm=a260k.home2025.leftmenu_EXPEND.dorder&page=1&pageSize=10"
    logging.info(f"Navigating to: {url}")
    driver = safe_get(driver, url, rebuild_driver_fn=rebuild_driver_fn)

    # Wait for page to load
    try:
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except TimeoutException:
        pass  # Continue anyway, page may be usable

    # Wait for dynamic content - the search function will do additional waiting
    human_delay(2, 5)
    logging.info("Order list page loaded.")
    return driver

# --- Search for Product ---
def search_product(driver, product_name_cn):
    """Search for a product by entering product_name_cn into the search input field."""
    print(f"Searching for: {product_name_cn}")

    try:
        # Wait for APP-ROOT element to exist first (top level)
        print("[DEBUG] Waiting for APP-ROOT element...")
        max_wait = 30
        app_root_found = False

        for i in range(max_wait):
            count = driver.execute_script("return document.querySelectorAll('app-root').length")
            if count > 0:
                print(f"[DEBUG] Found app-root after {i+1} seconds")
                app_root_found = True
                break
            human_delay(0.8, 1.5)

        if not app_root_found:
            print(f"[ERROR] No app-root element found after {max_wait} seconds")
            return False

        # Wait for nested shadow DOMs to be ready
        human_delay(4, 8)

        # Step 1: Focus the search input via shadow DOM traversal and clear it
        focus_result = driver.execute_script("""
            try {
                const appRoot = document.querySelector('app-root');
                if (!appRoot || !appRoot.shadowRoot) return 'FAIL: No app-root or shadowRoot';

                const orderSearch = appRoot.shadowRoot.querySelector('order-search');
                if (!orderSearch || !orderSearch.shadowRoot) return 'FAIL: No order-search or shadowRoot';

                const orderSearchKeywords = orderSearch.shadowRoot.querySelector('order-search-keywords');
                if (!orderSearchKeywords || !orderSearchKeywords.shadowRoot) return 'FAIL: No order-search-keywords or shadowRoot';

                const qInputs = orderSearchKeywords.shadowRoot.querySelectorAll('q-input');
                for (const qInput of qInputs) {
                    const placeholder = qInput.getAttribute('placeholder') || '';
                    if (placeholder.includes('\u5546\u54c1\u540d\u79f0')) {
                        if (qInput.shadowRoot) {
                            const input = qInput.shadowRoot.querySelector('input');
                            if (input) {
                                input.focus();
                                input.select();
                                return 'SUCCESS';
                            }
                        }
                    }
                }

                return 'FAIL: Could not find input in nested shadow DOM';
            } catch (e) {
                return 'FAIL: ' + e.message;
            }
        """)

        print(f"[DEBUG] Focus result: {focus_result}")

        if focus_result != 'SUCCESS':
            print("[ERROR] Could not focus search input")
            return False

        # Step 2: Clear existing text and type new search text via keyboard
        human_delay(0.3, 0.8)
        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL)
        actions.send_keys(Keys.BACK_SPACE)
        actions.send_keys(product_name_cn)
        actions.perform()
        actions.reset_actions()

        print(f"[DEBUG] Typed search text via send_keys")

        human_delay(0.8, 2)

        # Step 3: Click search button via ActionChains coordinate click
        button_info = driver.execute_script("""
            try {
                const appRoot = document.querySelector('app-root');
                if (!appRoot || !appRoot.shadowRoot) return {error: 'No app-root'};
                const orderSearch = appRoot.shadowRoot.querySelector('order-search');
                if (!orderSearch || !orderSearch.shadowRoot) return {error: 'No order-search'};
                const orderSearchActions = orderSearch.shadowRoot.querySelector('order-search-actions');
                if (!orderSearchActions || !orderSearchActions.shadowRoot) return {error: 'No order-search-actions'};
                const qButton = orderSearchActions.shadowRoot.querySelector('q-button[type="primary"]');
                if (!qButton) return {error: 'No q-button found'};
                const rect = qButton.getBoundingClientRect();
                return {
                    success: true,
                    x: rect.x + rect.width / 2,
                    y: rect.y + rect.height / 2,
                    width: rect.width,
                    height: rect.height
                };
            } catch (e) { return {error: e.message}; }
        """)

        print(f"[DEBUG] Button info: {button_info}")

        if 'error' in button_info:
            print(f"[ERROR] Could not locate search button: {button_info['error']}")
            return False

        human_move_and_click(driver, button_info['x'], button_info['y'])

        print("[DEBUG] Clicked search button via ActionChains coordinate click")

        human_delay(2, 5)
        return True

    except Exception as e:
        print(f"Error searching: {e}")
        import traceback
        traceback.print_exc()
        return False

# --- Click Product Result ---
def click_product_result(driver):
    """Click on the first product result link (nested in shadow DOM)."""
    try:
        print("Waiting for product results...")

        # Wait for results to load after search
        human_delay(2, 5)

        # Product links are inside nested shadow DOM:
        # APP-ROOT -> ORDER-LIST -> ORDER-ITEM -> ORDER-ITEM-ENTRY-PRODUCT -> a.product-name
        # Use recursive shadow DOM search via JavaScript to find and get the href
        product_info = driver.execute_script("""
            // Recursive function to find elements in shadow DOM
            function findInShadow(root, selector) {
                let result = root.querySelectorAll(selector);
                if (result.length > 0) return Array.from(result);

                const allElements = root.querySelectorAll('*');
                for (const el of allElements) {
                    if (el.shadowRoot) {
                        result = findInShadow(el.shadowRoot, selector);
                        if (result.length > 0) {
                            return result;
                        }
                    }
                }
                return [];
            }

            // Wait and retry logic
            const productLinks = findInShadow(document, 'a.product-name');

            if (productLinks.length === 0) {
                return {error: 'No product links found'};
            }

            // Get first product link
            const firstProduct = productLinks[0];
            const href = firstProduct.getAttribute('href');
            const text = firstProduct.textContent.trim();

            return {
                success: true,
                count: productLinks.length,
                text: text,
                href: href
            };
        """)

        print(f"[DEBUG] Product search result: {product_info}")

        if 'error' in product_info:
            # Retry with longer wait
            print("[DEBUG] No products found, retrying with longer wait...")
            human_delay(4, 8)

            product_info = driver.execute_script("""
                function findInShadow(root, selector) {
                    let result = root.querySelectorAll(selector);
                    if (result.length > 0) return Array.from(result);

                    const allElements = root.querySelectorAll('*');
                    for (const el of allElements) {
                        if (el.shadowRoot) {
                            result = findInShadow(el.shadowRoot, selector);
                            if (result.length > 0) {
                                return result;
                            }
                        }
                    }
                    return [];
                }

                const productLinks = findInShadow(document, 'a.product-name');

                if (productLinks.length === 0) {
                    return {error: 'No product links found after retry'};
                }

                const firstProduct = productLinks[0];
                const href = firstProduct.getAttribute('href');
                const text = firstProduct.textContent.trim();

                return {
                    success: true,
                    count: productLinks.length,
                    text: text,
                    href: href
                };
            """)

            if 'error' in product_info:
                print(f"[ERROR] {product_info['error']}")
                return False

        print(f"Found {product_info['count']} product(s)")
        print(f"Opening: {product_info['text'][:50]}..." if len(product_info.get('text', '')) > 50 else f"Opening: {product_info.get('text', 'N/A')}")
        print(f"URL: {product_info['href']}")

        # Navigate directly to the product URL in the same tab
        product_url = product_info['href']
        safe_get(driver, product_url)

        # Wait for page to load
        human_delay(2, 5)
        print(f"Product page loaded: {driver.current_url}")
        return True

    except Exception as e:
        print(f"Error clicking product: {e}")
        import traceback
        traceback.print_exc()
        return False

# --- Fetch SKU Variation Images ---
def fetch_sku_images(driver, variation_list_cn):
    """
    Fetch SKU variation image URLs by clicking/hovering each variation button
    and capturing the high-res preview image from the gallery.

    Args:
        driver: Selenium WebDriver instance
        variation_list_cn: JSON string like '["\u5200\u53c9\u52fa", "\u5496\u5561\u8272", "\u7eaf\u9ed1\u8272"]'

    Returns:
        list: Ordered list of image URLs matching variation_list_cn order
    """
    # Parse variation_list_cn to get ordered list
    if not variation_list_cn:
        print("[INFO] No variations to fetch (variation_list_cn is empty)")
        return []

    try:
        variations = json.loads(variation_list_cn)
        if not isinstance(variations, list):
            print("[INFO] variation_list_cn is not a list")
            return []
    except json.JSONDecodeError:
        print("[INFO] Invalid JSON in variation_list_cn")
        return []

    if not variations:
        print("[INFO] No variations to fetch (empty list)")
        return []

    print(f"\nFetching SKU images ({len(variations)} variations)...")

    # Wait for SKU elements to load
    human_delay(1.5, 4)

    result = []
    seen_bases = {}  # Cache: normalized_name -> url (to avoid duplicate clicks)

    # For each variation in order
    for variation in variations:
        # Normalize: "\u9ed1\u8272 - 38" -> "\u9ed1\u8272", "\u7c89\u8272  M80-100\u65a4" -> "\u7c89\u8272"
        base_variation = variation.strip()
        if " - " in base_variation:
            base_variation = base_variation.split(" - ")[0].strip()
        elif re.search(r'\s{2,}', base_variation):
            base_variation = re.split(r'\s{2,}', base_variation)[0].strip()

        # Check cache first
        if base_variation in seen_bases:
            result.append(seen_bases[base_variation])
            continue
        # Scroll element into view and get fresh coordinates
        button_info = driver.execute_script("""
            const targetLabel = arguments[0];

            // Pattern 1: button.sku-filter-button with span.label-name (need to click)
            for (const btn of document.querySelectorAll('button.sku-filter-button')) {
                const label = btn.querySelector('span.label-name');
                if (label && label.textContent.trim() === targetLabel) {
                    btn.scrollIntoView({ block: 'center' });
                    const rect = btn.getBoundingClientRect();
                    return {
                        x: rect.x + rect.width / 2,
                        y: rect.y + rect.height / 2,
                        pattern: 'click'
                    };
                }
            }

            // Pattern 2: div.v-flex with span.item-label - hover over the img
            for (const div of document.querySelectorAll('div.v-flex')) {
                const label = div.querySelector('span.item-label');
                const img = div.querySelector('img.ant-image-img');
                if (label && label.textContent.trim() === targetLabel && img) {
                    img.scrollIntoView({ block: 'center' });
                    const rect = img.getBoundingClientRect();
                    return {
                        x: rect.x + rect.width / 2,
                        y: rect.y + rect.height / 2,
                        pattern: 'hover'
                    };
                }
            }

            // Pattern 3: td.ant-table-cell > div.gyp-pro-table-title with <p> label and <img> - hover for popover
            for (const title of document.querySelectorAll('div.gyp-pro-table-title')) {
                const p = title.querySelector('p');
                const img = title.querySelector('img');
                if (p && p.textContent.trim() === targetLabel && img) {
                    img.scrollIntoView({ block: 'center' });
                    const rect = img.getBoundingClientRect();
                    return {
                        x: rect.x + rect.width / 2,
                        y: rect.y + rect.height / 2,
                        pattern: 'hover_popover'
                    };
                }
            }

            return null;  // Not found
        """, base_variation)

        if not button_info and ' ' in base_variation:
            # Fallback: retry with just the first word (e.g. "\u767d\u8272 \u5927\u53f7" -> "\u767d\u8272")
            first_word = base_variation.split(' ')[0].strip()
            print(f"  [RETRY] {base_variation} -> trying first word: {first_word}")
            button_info = driver.execute_script("""
                const targetLabel = arguments[0];

                // Pattern 1: button.sku-filter-button with span.label-name (need to click)
                for (const btn of document.querySelectorAll('button.sku-filter-button')) {
                    const label = btn.querySelector('span.label-name');
                    if (label && label.textContent.trim() === targetLabel) {
                        btn.scrollIntoView({ block: 'center' });
                        const rect = btn.getBoundingClientRect();
                        return {
                            x: rect.x + rect.width / 2,
                            y: rect.y + rect.height / 2,
                            pattern: 'click'
                        };
                    }
                }

                // Pattern 2: div.v-flex with span.item-label - hover over the img
                for (const div of document.querySelectorAll('div.v-flex')) {
                    const label = div.querySelector('span.item-label');
                    const img = div.querySelector('img.ant-image-img');
                    if (label && label.textContent.trim() === targetLabel && img) {
                        img.scrollIntoView({ block: 'center' });
                        const rect = img.getBoundingClientRect();
                        return {
                            x: rect.x + rect.width / 2,
                            y: rect.y + rect.height / 2,
                            pattern: 'hover'
                        };
                    }
                }

                // Pattern 3: td.ant-table-cell > div.gyp-pro-table-title with <p> label and <img> - hover for popover
                for (const title of document.querySelectorAll('div.gyp-pro-table-title')) {
                    const p = title.querySelector('p');
                    const img = title.querySelector('img');
                    if (p && p.textContent.trim() === targetLabel && img) {
                        img.scrollIntoView({ block: 'center' });
                        const rect = img.getBoundingClientRect();
                        return {
                            x: rect.x + rect.width / 2,
                            y: rect.y + rect.height / 2,
                            pattern: 'hover_popover'
                        };
                    }
                }

                return null;  // Not found
            """, first_word)

        if not button_info:
            print(f"  [SKIP] {base_variation} (not found on page)")
            result.append(None)
            continue

        try:
            human_delay(0.2, 0.6)  # Wait for scroll to settle

            # Move to button coordinates with humanized movement
            should_click = button_info['pattern'] == 'click'
            human_move_and_click(driver, button_info['x'], button_info['y'], click=should_click)

            human_delay(0.4, 1.2)  # Wait for gallery/popover to update

            # Get the variation image based on pattern
            if button_info['pattern'] == 'hover_popover':
                # Pattern 3: read the last ant-popover image (each hover appends a new popover)
                preview_url = driver.execute_script("""
                    const popovers = document.querySelectorAll('.ant-popover-inner-content img');
                    if (popovers.length === 0) return null;
                    return popovers[popovers.length - 1].src;
                """)
            else:
                # Pattern 1 & 2: read from gallery preview
                preview_url = driver.execute_script("""
                    const img = document.querySelector('.od-gallery-preview .od-gallery-list li:first-child img.preview-img');
                    return img ? img.src : null;
                """)

            if preview_url:
                result.append(preview_url)
                seen_bases[base_variation] = preview_url  # Cache for duplicates
                print(f"  [OK] {base_variation} -> URL found")
            else:
                result.append(None)
                print(f"  [WARN] {base_variation} -> no preview image found")

        except Exception as e:
            print(f"  [ERROR] {base_variation} -> {e}")
            result.append(None)

    print(f"SKU images found: {sum(1 for x in result if x)}/{len(variations)}")

    return result


# --- Fetch Gallery Images ---
def fetch_gallery_images(driver):
    """
    Fetch product gallery image URLs from 1688 product page.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        list: Array of image URLs [url1, url2, ...]
    """
    print(f"\nFetching gallery images...")

    # Wait for gallery to load
    human_delay(1.5, 4)

    # Step 1: Scroll through gallery to load all images (handle lazy loading)
    max_scroll_attempts = 50  # Safety limit
    for _ in range(max_scroll_attempts):
        # Check if scroll down button exists and is visible
        can_scroll = driver.execute_script("""
            const btn = document.querySelector('button.od-gallery-button-under');
            if (!btn) return false;
            const style = window.getComputedStyle(btn);
            return style.visibility !== 'hidden' && style.display !== 'none';
        """)

        if not can_scroll:
            break  # No more scrolling needed

        # Click the scroll button
        driver.execute_script("""
            const btn = document.querySelector('button.od-gallery-button-under');
            if (btn) btn.click();
        """)

        human_delay(0.2, 0.7)  # Wait for scroll animation and image loading

    # Step 2: Now collect all gallery images
    gallery_data = driver.execute_script("""
        const images = [];
        let skippedVideos = 0;

        // Select all li items in the gallery list
        const items = document.querySelectorAll('.od-gallery-list > li');

        items.forEach((item) => {
            // Skip video entries (contains .od-video-wrapper)
            if (item.querySelector('.od-video-wrapper')) {
                skippedVideos++;
                return;
            }

            // Get the gallery image
            const img = item.querySelector('img.ant-image-img.preview-img');
            if (img && img.src) {
                images.push(img.src);
            }
        });

        return {
            images: images,
            skippedVideos: skippedVideos
        };
    """)

    if not gallery_data or not gallery_data.get('images'):
        print("  [WARN] No gallery images found on page")
        return []

    images = gallery_data['images']
    skipped_videos = gallery_data.get('skippedVideos', 0)

    if skipped_videos > 0:
        print(f"  [DEBUG] Found {len(images)} gallery images (skipped {skipped_videos} video)")
    else:
        print(f"  [DEBUG] Found {len(images)} gallery images")

    print(f"Gallery images found: {len(images)}")

    return images


# --- Fetch Description Content ---
def fetch_description_content(driver):
    """
    Fetch product description content (text + images) from 1688 product page.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        tuple: (description_imgs, description_txt) where:
            - description_imgs: List of image URLs (max 40)
            - description_txt: Combined text content as string
    """
    print(f"\nFetching description content...")

    # Step 1: Scroll to #description section to trigger lazy loading
    print("  [DEBUG] Scrolling to #description section...")
    driver.execute_script("""
        const descSection = document.querySelector('#description');
        if (descSection) {
            descSection.scrollIntoView({ behavior: 'instant', block: 'center' });
        } else {
            window.scrollTo(0, document.body.scrollHeight);
        }
    """)
    human_delay(2, 5)

    # Step 2: Wait for description component to be ready
    print("  [DEBUG] Waiting for description component...")
    max_wait = 10
    for i in range(max_wait):
        is_ready = driver.execute_script("""
            const desc = document.querySelector('#description');
            if (!desc) return 'no_description_section';

            const vDetail = desc.querySelector('.html-description');
            if (!vDetail) return 'no_html-description';
            if (!vDetail.shadowRoot) return 'no_shadow_root';

            const detail = vDetail.shadowRoot.querySelector('div#detail');
            if (!detail) return 'no_detail_div';
            if (detail.innerHTML.length < 100) return 'content_loading';

            return 'ready';
        """)

        if is_ready == 'ready':
            print(f"  [DEBUG] Description ready after {i+1} seconds")
            break
        else:
            print(f"  [DEBUG] Status: {is_ready}, waiting...")
            human_delay(0.8, 2)
    else:
        print(f"  [WARN] Description not ready after {max_wait} seconds")
        return ([], None)

    # Step 3: Extract content
    description_data = driver.execute_script("""
        const desc = document.querySelector('#description');
        if (!desc) return { error: 'No #description section found' };

        const vDetail = desc.querySelector('.html-description');
        if (!vDetail) return { error: 'No .html-description component found' };
        if (!vDetail.shadowRoot) return { error: vDetail.tagName + ' has no shadow root' };

        const detailDiv = vDetail.shadowRoot.querySelector('div#detail');
        if (!detailDiv) return { error: 'No div#detail in shadow root' };

        const rawContent = [];

        // EXCLUDE these containers entirely (by selector)
        const excludeSelectors = [
            '.sdmap-dynamic-offer-list',
            '.offer-list-wapper',
            '.desc-dynamic-module',
            '.rich-text-component'
        ];

        const excludeImageClasses = ['dynamic-backup-img'];

        function isInsideExcludedContainer(node) {
            let current = node;
            while (current && current !== detailDiv) {
                if (current.nodeType === Node.ELEMENT_NODE) {
                    for (const selector of excludeSelectors) {
                        if (current.matches && current.matches(selector)) {
                            return true;
                        }
                    }
                }
                current = current.parentElement;
            }
            return false;
        }

        function extractContent(node) {
            if (isInsideExcludedContainer(node)) return;

            if (node.nodeType === Node.TEXT_NODE) {
                const text = node.textContent.trim();
                if (text && text !== '&nbsp;') {
                    rawContent.push({ type: 'text', content: text });
                }
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                for (const selector of excludeSelectors) {
                    if (node.matches && node.matches(selector)) return;
                }

                if (node.tagName === 'IMG') {
                    for (const cls of excludeImageClasses) {
                        if (node.classList.contains(cls)) return;
                    }

                    const src = node.getAttribute('src');
                    if (src && !src.startsWith('data:') && src.startsWith('http')) {
                        rawContent.push({ type: 'image', content: src });
                    }
                } else {
                    for (const child of node.childNodes) {
                        extractContent(child);
                    }
                }
            }
        }

        extractContent(detailDiv);

        // Merge consecutive text blocks
        const content = [];
        let pendingTexts = [];

        for (const item of rawContent) {
            if (item.type === 'text') {
                pendingTexts.push(item.content);
            } else {
                if (pendingTexts.length > 0) {
                    content.push({ type: 'text', content: pendingTexts.join('\\n') });
                    pendingTexts = [];
                }
                content.push({ type: 'image', content: item.content });
            }
        }

        if (pendingTexts.length > 0) {
            content.push({ type: 'text', content: pendingTexts.join('\\n') });
        }

        return {
            component: vDetail.tagName,
            content: content
        };
    """)

    # Step 4: Process the result
    if not description_data:
        print("  [WARN] No description data returned")
        return ([], None)

    if 'error' in description_data:
        print(f"  [WARN] {description_data['error']}")
        return ([], None)

    content = description_data.get('content', [])
    component = description_data.get('component', 'unknown')

    print(f"  [DEBUG] Component: {component}")

    # Separate images and text
    description_imgs = [c.get('content') for c in content if c.get('type') == 'image']
    text_blocks = [c.get('content') for c in content if c.get('type') == 'text']
    description_txt = '\n'.join(text_blocks) if text_blocks else None

    print(f"  [DEBUG] Found {len(text_blocks)} text blocks and {len(description_imgs)} images")

    if not content:
        print("  [INFO] No description content found")
        return ([], None)

    print(f"Description: {len(description_imgs)} images, {len(text_blocks)} text blocks")

    # Return tuple of (images_list, combined_text)
    return (description_imgs, description_txt)


# --- Check if Session Expired (quick check) ---
def check_session_expired(driver):
    """Quick check if redirected to login page. Returns True if session expired."""
    try:
        current_url = driver.current_url.lower()
        if "login" in current_url or "passport" in current_url:
            return True
        # Check page source for login form
        page_source = driver.page_source
        if '\u8bf7\u8f93\u5165\u624b\u673a\u53f7' in page_source or 'fm-sms-login-id' in page_source:
            return True
        return False
    except:
        return False

# --- Process All Products ---
def process_products(driver, products, profile_path):
    """Process each product: search, click, fetch data, and insert into shopee_listings."""
    total_success = 0
    total_fail = 0
    total_inserted = 0

    # Create rebuild function for crashed sessions
    def rebuild_driver():
        print("  [INFO] Creating new browser instance...")
        new_driver = setup_driver(profile_path)
        human_delay(2, 5)
        return new_driver

    for idx, (product_id, product_name, variation_list_cn, reference_links, launch_type, item_date) in enumerate(products, 1):
        try:
            print(f"\n[{idx}/{len(products)}] Processing: {product_name}")
        except:
            print(f"\n[{idx}/{len(products)}] Processing: [product with encoding issue]")
        sys.stdout.flush()

        # Navigate to order list for each search (with rebuild capability)
        try:
            driver = navigate_to_order_list(driver, rebuild_driver)
        except Exception as e:
            print(f"  [ERROR] Failed to navigate: {e}")
            total_fail += 1
            continue

        # Check if session expired mid-run
        if check_session_expired(driver):
            print("\n" + "="*60)
            print("[WARNING] Session expired! Please login again.")
            print("="*60)
            driver = navigate_to_order_list(driver, rebuild_driver)
            human_delay(2, 5)

        # Search for product
        if not search_product(driver, product_name):
            print(f"[FAIL] Could not search: {product_name}")
            total_fail += 1
            continue

        # Click product result
        if click_product_result(driver):
            # Fetch gallery images FIRST (before clicking variations changes the gallery)
            gallery_urls = fetch_gallery_images(driver)

            # Fetch SKU variation images (clicks/hovers buttons, changes gallery)
            variation_imgs = fetch_sku_images(driver, variation_list_cn)

            # Fetch description content (returns tuple of images and text)
            description_imgs, description_txt = fetch_description_content(driver)

            # Parse variation names from variation_list_cn
            variation_names = []
            if variation_list_cn:
                try:
                    variation_names = json.loads(variation_list_cn)
                    if not isinstance(variation_names, list):
                        variation_names = []
                except json.JSONDecodeError:
                    variation_names = []

            # Insert into database
            print("\nInserting into database...")
            rows_inserted = insert_shopee_listings(
                product_id,
                product_name,
                reference_links,
                launch_type,
                variation_names,
                variation_imgs,
                gallery_urls,
                description_imgs,
                description_txt,
                item_date
            )
            if rows_inserted > 0:
                total_inserted += rows_inserted

            print(f"[SUCCESS] {product_name}")
            total_success += 1
        else:
            print(f"[FAIL] No results for: {product_name}")
            total_fail += 1

        human_delay(4, 10)

        # Random idle browsing (30% chance) to break predictable patterns
        if random.random() < 0.3:
            print("  [IDLE] Simulating idle browsing...")
            simulate_idle_browsing(driver)

        # Batch breaks to avoid sustained rapid activity
        if idx % 15 == 0:
            pause = random.uniform(300, 600)
            print(f"\n[PAUSE] Long break after {idx} products ({pause:.0f}s)...")
            time.sleep(pause)
        elif idx % 5 == 0:
            pause = random.uniform(120, 300)
            print(f"\n[PAUSE] Short break after {idx} products ({pause:.0f}s)...")
            time.sleep(pause)

    return total_success, total_fail, total_inserted

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

    # Chrome profile path (same pattern as Updated_V3_ShopeeMY-Scrap.py)
    # Use "User Data" folder path, and specify profile in setup_driver
    profile_path = r"C:\Users\User 2\AppData\Local\Google\Chrome\User Data\Profile 1"

    print("="*60)
    print("1688 Order Search & Database Storage")
    print("="*60)
    print("Data will be saved to: requestDatabase.shopee_listing_products + shopee_listing_variations")

    # Setup driver with profile
    print("\nStarting Chrome with profile...")
    print("[INFO] Make sure ALL Chrome windows are CLOSED before running!")

    driver = setup_driver(profile_path)

    try:
        # Check if logged in to 1688 (will prompt for manual login if needed)
        print("\nChecking 1688 login status...")
        if not check_1688_login(driver):
            print("Cannot proceed without login. Exiting.")
            return

        # Fetch products from database (with variations)
        print("\nFetching products from database...")
        products = get_product_names_from_db()

        if not products:
            print("No products found in database. Exiting.")
            return

        print(f"Found {len(products)} products to process.")
        sys.stdout.flush()

        # Debug: print first few products
        print("\n[DEBUG] First 3 products:")
        for i, (pid, name, variations, ref_links, ltype, _date) in enumerate(products[:3]):
            try:
                print(f"  {i+1}. [ID: {pid}] {name}")
                print(f"      Variations: {variations[:50]}..." if variations and len(variations) > 50 else f"      Variations: {variations}")
                print(f"      URL: {ref_links[:60]}..." if ref_links and len(ref_links) > 60 else f"      URL: {ref_links}")
            except:
                print(f"  {i+1}. [encoding error - product exists]")
        sys.stdout.flush()

        # Process all products
        total_success, total_fail, total_inserted = process_products(driver, products, profile_path)

        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total Products: {len(products)}")
        print(f"Success: {total_success}")
        print(f"Failed: {total_fail}")
        print(f"Rows Inserted: {total_inserted}")

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nScript completed. Browser will remain open.")
        driver.quit()

if __name__ == "__main__":
    main()
