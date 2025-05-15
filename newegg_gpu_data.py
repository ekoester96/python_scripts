import requests
import re
import random
from bs4 import BeautifulSoup
# this code extracts data from a list of products on Neweggs graphics cards components category but
# it can be modified to get data from other components or pages on Newegg.com

base_url = "https://www.newegg.com/"
url1 = "https://www.newegg.com/GPUs-Video-Graphics-Cards/SubCategory/ID-48"

# this is a list of user agents that will be picked at random and incorporated into the header
# to prevent the web server from blocking http requests
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
]


def get_random_user_agent():
    return random.choice(user_agents)

# this function returns a browser header it's not the best it needs to be worked on
def get_headers():
    return {
        "Host": "www.newegg.com",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "User-Agent": get_random_user_agent(),
        "Origin": "https://www.newegg.com",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": "https://www.google.com/",
        "Cache-Control": "no-cache",
        "Upgrade-Insecure-Requests": "1",
        "Dnt": "1"
    }
# here we need to call the functions that pick a random user agent and update our sessions
# with the header and user agent we've generated
get_random_user_agent()
session = requests.Session()
session.headers.update(get_headers())

# here is the function that extracts data from each item on the page like product name, brand, rating, stock status
def extract_product_info(item):

    title_tag = item.find('a', class_='item-title')
    if not title_tag:
        return None

    product_name = title_tag.text.strip()

    stock_tag = item.find('i', class_='item-promo-icon')
    stock_status = 'OUT OF STOCK' if stock_tag and 'OUT OF STOCK' in stock_tag.text else 'IN STOCK'

    price_tag = item.find('li', class_='price-current')
    if price_tag:
        price_value = price_tag.get_text(strip=True)

    else:
        price_value = "Price not found"

    brand = "Unknown"
    brand_tag = item.find('div', class_='item-branding')
    if brand_tag:
        brand_img = brand_tag.find('img')
        if brand_img and brand_img.get('title'):
            brand = brand_img.get('title')

    rating_tag = item.find('a', class_='item-rating')
    if rating_tag:
        rating_text = rating_tag.get('title', '')
        rating_match = re.search(r'\d.\d', rating_text)
        if rating_match:
            rating_text = rating_match.group()
        else:
            rating_text = "N/A"
    else:
        rating_text = "N/A"


    return {
      'name': product_name,
      'price': price_value,
      'stock': stock_status,
      'brand': brand,
      'rating': rating_text,
    }

# this function is for parsing the first html page because there is no page number
def html_parser():
    response = requests.get("https://www.newegg.com/GPUs-Video-Graphics-Cards/SubCategory/ID-48/")

    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.find_all('div', class_='item-cell')

    for item in items:
        product = extract_product_info(item)
        print(product)

html_parser()

# this function parses each page number in a while loop
def paged_parser():
    page_number = 2
    pages = "Page-" + str(page_number)
    while page_number < 5:
        response = requests.get("https://www.newegg.com/GPUs-Video-Graphics-Cards/SubCategory/ID-48/" + pages)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', class_='item-cell')
        page_number += 1

        for item in items:
            product = extract_product_info(item)
            print(product)

paged_parser()
