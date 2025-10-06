import time
import random
import requests
import logging
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth

# IMPORTANT: Replace with your actual Discord Webhook URL
DISCORD_WEBHOOK_URL = ""
SEARCH_TERM = "9070XT" # Change to whatever item you want to search
MAX_PRICE = 600.00 # Select max price for the item
PAGES_TO_SCRAPE = 3 
CHECK_INTERVAL_MIN_SECONDS = 900
CHECK_INTERVAL_MAX_SECONDS = 1800

# Optional: To use a proxy, set its address here (e.g., "ip_address:port")
# Get proxies from reputable providers. Using a proxy is highly recommended for reliability.
PROXY_SERVER = "" # Example: "username:password@123.45.67.89:8080"

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0'
]
# --- END CONFIGURATION ---

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    """Sets up the Selenium Chrome WebDriver with stealth and proxy options."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("start-maximized")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    if PROXY_SERVER:
        options.add_argument(f'--proxy-server={PROXY_SERVER}')
        logging.info(f"Using proxy server: {PROXY_SERVER}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    return driver

def human_like_scroll(driver):
    """Simulates a human scrolling down the page."""
    total_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(0, total_height, random.randint(300, 500)):
        driver.execute_script(f"window.scrollTo(0, {i});")
        time.sleep(random.uniform(0.2, 0.5))

def send_discord_notification(product_name, product_url, site_name, price):
    """Sends a formatted notification to the configured Discord webhook."""
    if DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        logging.warning("Discord webhook URL is not set. Skipping notification.")
        return

    data = {"content": f"🎉 **Price & Stock Alert!** 🎉 @everyone", "embeds": [{"title": f"{product_name}", "description": f"**Found in stock at {site_name} for ${price:,.2f}!**", "url": product_url, "color": 65280, "fields": [{"name": "Product", "value": product_name, "inline": True}, {"name": "Price", "value": f"${price:,.2f}", "inline": True}], "footer": {"text": f"Found at {site_name} | GPU Stock Scraper"}}]}
    try:
        result = requests.post(DISCORD_WEBHOOK_URL, json=data)
        result.raise_for_status()
        logging.info(f"Successfully sent Discord notification for {product_name}!")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Discord notification: {e}")

def parse_price(price_text):
    """Extracts a float value from a price string."""
    try:
        cleaned_price = re.sub(r'[^\d.]', '', price_text)
        return float(cleaned_price)
    except (ValueError, TypeError):
        return None

def get_url_with_retries(driver, url, retries=2, delay=5):
    """Attempts to load a URL with a specified number of retries."""
    for i in range(retries):
        try:
            driver.get(url)
            return True
        except (TimeoutException, WebDriverException) as e:
            logging.warning(f"Attempt {i+1}/{retries}: Failed to load {url}. Retrying in {delay}s... Error: {e}")
            time.sleep(delay)
    logging.error(f"Failed to load {url} after {retries} attempts.")
    return False

def check_bestbuy(driver, search_term):
    logging.info("Checking Best Buy...")
    for page in range(1, PAGES_TO_SCRAPE + 1):
        logging.info(f"Checking Best Buy - Page {page}...")
        url = f"https://www.bestbuy.com/site/searchpage.jsp?st={search_term.replace(' ', '+')}&cp={page}"
        if not get_url_with_retries(driver, url):
            break
        
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".sku-item-list")))
            human_like_scroll(driver)
            products = driver.find_elements(By.CSS_SELECTOR, ".sku-item")
            if not products:
                logging.info(f"No products found on Best Buy page {page}. This might be the last page.")
                break
            for product in products:
                try:
                    add_to_cart_button = product.find_element(By.CSS_SELECTOR, ".add-to-cart-button:not([disabled])")
                    if add_to_cart_button.is_displayed() and add_to_cart_button.is_enabled():
                        price_element = product.find_element(By.CSS_SELECTOR, ".priceView-hero-price span")
                        price = parse_price(price_element.text)
                        if price and price <= MAX_PRICE:
                            product_title_element = product.find_element(By.CSS_SELECTOR, ".sku-title h4 a")
                            product_name = product_title_element.text
                            product_url = product_title_element.get_attribute('href')
                            logging.info(f"✅ IN STOCK & UNDER PRICE at Best Buy: {product_name} for ${price}")
                            send_discord_notification(product_name, product_url, "Best Buy", price)
                except Exception:
                    continue
        except TimeoutException:
            logging.info(f"Timed out waiting for products on Best Buy page {page}. Assuming it's the last page.")
            break
        except Exception as e:
            logging.error(f"An error occurred while checking Best Buy page {page}: {e}")
            break
        time.sleep(random.uniform(4, 7))


def check_newegg(driver, search_term):
    logging.info("Checking Newegg...")
    for page in range(1, PAGES_TO_SCRAPE + 1):
        logging.info(f"Checking Newegg - Page {page}...")
        url = f"https://www.newegg.com/p/pl?d={search_term.replace(' ', '+')}&page={page}"
        if not get_url_with_retries(driver, url):
            break
        
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".item-cells-wrap")))
            human_like_scroll(driver)
            items = driver.find_elements(By.CSS_SELECTOR, ".item-cell")
            if not items:
                logging.info(f"No products found on Newegg page {page}.")
                break
            for item in items:
                try:
                    add_to_cart_button = item.find_element(By.CSS_SELECTOR, ".item-button-area button.btn-primary")
                    if "ADD TO CART" in add_to_cart_button.text.upper():
                        price_container = item.find_element(By.CSS_SELECTOR, ".price-current")
                        price_dollars = price_container.find_element(By.TAG_NAME, "strong").text
                        price_cents = price_container.find_element(By.TAG_NAME, "sup").text
                        price = parse_price(f"{price_dollars}{price_cents}")
                        if price and price <= MAX_PRICE:
                            title_element = item.find_element(By.CSS_SELECTOR, "a.item-title")
                            product_name = title_element.text
                            product_url = title_element.get_attribute('href')
                            logging.info(f"✅ IN STOCK & UNDER PRICE at Newegg: {product_name} for ${price}")
                            send_discord_notification(product_name, product_url, "Newegg", price)
                except Exception:
                    continue
        except Exception as e:
            logging.error(f"An error occurred while checking Newegg page {page}: {e}")
            break
        time.sleep(random.uniform(4, 7))


def check_amazon(driver, search_term):
    """Checks Amazon for the specified product, handling non-standard search result items."""
    logging.info("Checking Amazon...")
    for page in range(1, PAGES_TO_SCRAPE + 1):
        logging.info(f"Checking Amazon - Page {page}...")
        url = f"https://www.amazon.com/s?k={search_term.replace(' ', '+')}&page={page}"
        if not get_url_with_retries(driver, url):
            break

        try:
            if "api-services-support@amazon.com" in driver.page_source:
                logging.warning(f"Amazon is asking for a CAPTCHA on page {page}. Skipping.")
                break
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-component-type='s-search-result']")))
            human_like_scroll(driver)
            results = driver.find_elements(By.CSS_SELECTOR, "[data-component-type='s-search-result']")
            if not results:
                logging.info(f"No products found on Amazon page {page}.")
                break
            
            for result in results:
                try:
                    # First, check for a title. If none exists, this is not a standard product item.
                    try:
                        title_element = result.find_element(By.CSS_SELECTOR, "h2 a.a-link-normal")
                        product_name = title_element.text
                        if not product_name.strip(): # Skip if title is empty
                            continue
                        product_url = title_element.get_attribute('href')
                    except NoSuchElementException:
                        # This block is not a standard product (e.g., an ad or info box). Silently skip it.
                        continue

                    # Now that we have a title, we can proceed.
                    # Skip sponsored items or known out-of-stock markers
                    if "Sponsored" in result.get_attribute('innerHTML') or "Currently unavailable" in result.text:
                        continue

                    price = None
                    # Strategy 1: Look for the price in the standard price container.
                    try:
                        price_element = result.find_element(By.CSS_SELECTOR, "span.a-price")
                        price_offscreen = price_element.find_element(By.CSS_SELECTOR, "span.a-offscreen")
                        price = parse_price(price_offscreen.get_attribute('textContent'))
                    except NoSuchElementException:
                        pass

                    # Strategy 2: Fallback to combining whole and fraction parts.
                    if price is None:
                        try:
                            price_whole_element = result.find_element(By.CSS_SELECTOR, "span.a-price-whole")
                            price_fraction_element = result.find_element(By.CSS_SELECTOR, "span.a-price-fraction")
                            price_str = f"{price_whole_element.text}.{price_fraction_element.text}"
                            price = parse_price(price_str)
                        except NoSuchElementException:
                            pass
                    
                    # If price is still not found after finding a title, log it for debugging.
                    if price is None:
                        # We found a title but no price, this is a case worth logging.
                        logging.warning(f"Found product '{product_name}' but could not parse a price.")
                        continue

                    # Process the found item
                    if price and price <= MAX_PRICE:
                        logging.info(f"✅ POTENTIALLY IN STOCK & UNDER PRICE at Amazon: {product_name} for ${price}")
                        send_discord_notification(product_name, product_url, "Amazon", price)

                except Exception as e:
                    # This is a catch-all for any other unexpected errors for a single item.
                    logging.error(f"An unexpected error occurred while processing an Amazon item. Error: {e}")
                    continue
        except Exception as e:
            logging.error(f"A critical error occurred while checking Amazon page {page}: {e}")
            break
        time.sleep(random.uniform(5, 8))


def main():
    """Main function to run the scraper in a loop."""
    while True:
        driver = None # Initialize driver to None
        try:
            driver = setup_driver()
            check_bestbuy(driver, SEARCH_TERM)
            time.sleep(random.uniform(15, 30))
            check_newegg(driver, SEARCH_TERM)
            time.sleep(random.uniform(15, 30))
            check_amazon(driver, SEARCH_TERM)
        except Exception as e:
            logging.critical(f"A fatal error occurred in the main loop: {e}")
        finally:
            if driver:
                driver.quit()

        sleep_duration = random.randint(CHECK_INTERVAL_MIN_SECONDS, CHECK_INTERVAL_MAX_SECONDS)
        logging.info(f"--- Check complete. Waiting for {sleep_duration // 60} minutes before next check. ---")
        time.sleep(sleep_duration)

if __name__ == "__main__":
    main()
