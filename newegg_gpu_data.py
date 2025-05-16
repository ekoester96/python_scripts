# Author: Ethan
#!/bin/env/ python3
# Date created: 5/9/2025
# Date modified: 5/16/2025
# Description: This script is used to parse product data for newegg componenet URLS the example URL_1 is for gpu components but can be changed to
# different categories. The END_PAGE can also be changed to include more or less products. 

import requests
import re
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import csv

BASE_URL = "https://www.newegg.com/"
URL_1 = "https://www.newegg.com/GPUs-Video-Graphics-Cards/SubCategory/ID-48/"
START_PAGE = 1
END_PAGE = 10

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

def get_headers():
    return {
        "Host": "www.newegg.com",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "User-Agent": get_random_user_agent(),
        "Origin": "https://www.newegg.com",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": "https://www.newegg.com",
        "Cache-Control": "no-cache",
        "Upgrade-Insecure-Requests": "1",
        "Dnt": "1"
    }

def update_session():
    get_random_user_agent()
    session = requests.Session()
    session.headers.update(get_headers())

def extract_product_info(item):

    title_tag = item.find('a', class_='item-title')
    if not title_tag:
        return None

    product_name = title_tag.text.strip()
    product_url = urljoin(BASE_URL, title_tag['href'])

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
        'url': product_url,
        'price': price_value,
        'stock': stock_status,
        'brand': brand,
        'rating': rating_text,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


def paged_parser():
    end_page = END_PAGE
    page_number = START_PAGE
    all_products = []

    while page_number <= end_page:
        pages = f'Page-{page_number}' if page_number > 1 else ''
        response = requests.get(f'{URL_1}{pages}')
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', class_='item-cell')

        for item in items:
            product = extract_product_info(item)
            if product:
                all_products.append(product)

        page_number += 1

    return all_products


def save_to_csv(products, filename="newegg_gpu.csv"):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['brand', 'name', 'price', 'stock', 'rating', 'url', 'timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for product in products:
            row = {field: product.get(field, '') for field in fieldnames}
            writer.writerow(row)

def main():
    update_session()
    all_products = paged_parser()
    save_to_csv(all_products)

if __name__ == "__main__":
    main()
