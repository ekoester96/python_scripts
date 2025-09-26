#!/usr/bin/env python3
# Author: Ethan
# Date created: 5/9/2025
# Date modified: 5/20/2025
# Description: This script is used to parse product data for newegg component urls

import requests
import re
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import csv
import time

DATE = datetime.now().strftime('%Y-%m-%d')
BASE_URL = "https://www.newegg.com/"
# list of component url pages to request and parse data from
url_list = [
    "https://www.newegg.com/p/pl?N=100006662&page=1",
    "https://www.newegg.com/p/pl?N=100006676&cm_sp=shop-all-products-_-categroy-_-CPU-Processor-top",
    "https://www.newegg.com/p/pl?N=100006650&cm_sp=shop-all-products-_-categroy-_-Memory-bottom",
    "https://www.newegg.com/p/pl?N=100006644&cm_sp=shop-all-products-_-categroy-_-Computer-Case-bottom",
    "https://www.newegg.com/p/pl?N=100006656&cm_sp=shop-all-products-_-categroy-_-Power-Supply-top",
    "https://www.newegg.com/p/pl?N=100006648&cm_sp=shop-all-products-_-categroy-_-Fans-PC-Cooling-top",
    "https://www.newegg.com/p/pl?N=100011692&cm_sp=shop-all-products-_-categroy-_-SSD-top",
    "https://www.newegg.com/p/pl?N=100006670&cm_sp=shop-all-products-_-categroy-_-Hard-Drive-top",
]

# need to spoof the user agent because websites will not accept http request straight from python
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)
    
user_agent = get_random_user_agent()

# this function updates the header of our http request to look like it came from a real computer/browser
def get_headers():
    return {
        "Host": "www.newegg.com",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "User-Agent": user_agent,
        "Origin": "https://www.newegg.com",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": "https://www.newegg.com",
        "Cache-Control": "no-cache",
        "Upgrade-Insecure-Requests": "1",
        "Dnt": "1"
    }

# this function updates our session with the new request headers/user agents
# we want to be able to call it when making new url requests or if there are errors making requests
def update_session():
    session = requests.Session()
    session.headers.update(get_headers())

# this function runs in a for loop in the paged_parser() function
def extract_product_info(item):
    # for every item cell we find the title
    title_tag = item.find('a', class_='item-title')
    if not title_tag:
        return None
    # the product name is located in the text of the title html tag which we can get through text.strip()
    product_name = title_tag.text.strip()
    # the product url is found in the title_tag and can be joined with base url. This is done because
    # sometimes product urls are not complete url paths. This ensures that we get a complete url every time
    product_url = urljoin(BASE_URL, title_tag['href'])

    # in Newegg the out of stock tag is in an item-promo-icon class. if the item is in stock then it will not have this tag
    stock_tag = item.find('i', class_='item-promo-icon')
    if stock_tag:
        stock_status = "OUT OF STOCK"
    else:
        stock_status = "IN STOCK"

    # price for the item
    price_tag = item.find('li', class_='price-current')
    if price_tag:
        price_value = price_tag.get_text(strip=True)
    else:
        price_value = "Price not found"

    # in newegg the brand is usually found as the title of an image file in the item-brand class
    brand = "Unknown"
    brand_tag = item.find('a', class_='item-brand')
    if brand_tag:
        brand_img = brand_tag.find('img')
        if brand_img and brand_img.get('title'):
            brand = brand_img.get('title')

    # the rating tag text has a lot of gunk in it, so I'm using regex to match a pattern similar to "4.5" etc
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

    # function is returning a dictionary with all the info stored for one item then the for loop 
    # will loop through all other items on the page
    return {
        'name': product_name,
        'url': product_url,
        'price': price_value,
        'stock': stock_status,
        'brand': brand,
        'rating': rating_text,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def extract_category_name(soup):
    # since the html tags for the components are not in the item cells there needs to be a different function to find the component category
    component_tag = soup.find('h1', class_="page-title-text")
    if component_tag:
        component_name = component_tag.text.strip()
    else:
        component_name = 'Unknown'
    return {
        'component': component_name
    }

def paged_parser(start_url, all_products=None):
    # all products has to be passed through the function and an if statement with check if the list is empty
    # since this function is looping through each url, if the variable is declared every loop it will overwrite
    # the items already in the list
    if all_products is None:
        all_products = []
    # each url is also passed through the function using a list
    response = requests.get(start_url)
    # this is soup aka the entire html page from the url that is being passed through previously
    soup = BeautifulSoup(response.text, 'html.parser')

    # the component name is in a different html div from the products list so we store the categories in a new dictionary
    category_dict = extract_category_name(soup)
    component_name = category_dict['component']

    # store all item cells into a variable that can then be used for parsing later
    items = soup.find_all('div', class_='item-cell')

    # add in a little sleep function to delay each url request
    time.sleep(random.randint(1, 3))

    # loop through every item cell and call the function that extracts data from each item
    for item in items:
        product = extract_product_info(item)
        if product:
            # Add the component to the product dictionary because the dictionary in extract_product_info() has no way to do that
            product['component'] = component_name
            all_products.append(product)

    # this section is finding all the links at the bottom of the url page and adding them into a list
    divs = soup.find_all('div', class_='btn-group-cell')
    links = []
    for div in divs:
        a_tags = div.find_all('a', href=True)
        for a in a_tags:
            links.append(a['href'])

    # using the links gathered we can make an http request for each link and gather products for every page on the url
    for link in links:
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')

        # add the component to the dictionary
        category_dict = extract_category_name(soup)
        component_name = category_dict['component']
        # find the items on the page
        items = soup.find_all('div', class_='item-cell')
        time.sleep(random.randint(1, 3))
        # get data for each item on the page which returns a dictionary and add the component dictionary to the list
        for item in items:
            product = extract_product_info(item)
            if product:
                product['component'] = component_name
                all_products.append(product)
    return all_products

# this function is going to pass through the data in all_products and write the field names for each category
def save_to_csv(products, filename=f"newegg_{DATE}.csv"):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['component', 'brand', 'name', 'price', 'stock', 'rating', 'url', 'timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for product in products:
            row = {field: product.get(field, '') for field in fieldnames}
            writer.writerow(row)

def main():
    # all_products needs to be declared here and passed through the parser so the data is not overwritten
    # in every iteration of the for loop
    all_products = []
    
    for url in url_list:
        # call the function that updates our http headers
        update_session()
        # loop through each url
        paged_parser(url, all_products)
        
    # pass all_products through to be saved as a csv file
    save_to_csv(all_products)

if __name__ == "__main__":
    main()
