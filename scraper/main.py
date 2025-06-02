import json
import time
from scraper import get_amazon_bestseller_links_selenium, scrape_product_info

INPUT_SEARCH_FILE = "data/input_search.json"
INPUT_URLS_FILE = "data/input_urls.json"
INPUT_PRODUCTS_FILE = "data/input_products.json"

def main():
    with open(INPUT_SEARCH_FILE, "r", encoding="utf-8") as f:
        search_data = json.load(f)
        category_url = search_data.get("category_url")

    product_links = get_amazon_bestseller_links_selenium(category_url, num_products=20)
    with open(INPUT_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump({"urls": product_links}, f, indent=2)

    product_data = []
    for url in product_links:
        print(f"Scraping: {url}")
        info = scrape_product_info(url)
        product_data.append(info)
        time.sleep(2) 

    with open(INPUT_PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(product_data, f, indent=2, ensure_ascii=False)

    print("Product data saved in input_products")


if __name__ == "__main__":
    main()
