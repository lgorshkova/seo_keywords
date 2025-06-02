from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

CHROMEDRIVER_PATH = "C:/webdrivers/chromedriver.exe"


def get_amazon_bestseller_links_selenium(category_url: str, num_products: int = 20):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=de-DE")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0.0.0 Safari/537.36")

    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(category_url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = []
    for a in soup.select("a.a-link-normal[href*='/dp/']"):
        href = a.get("href")
        if href and "/dp/" in href:
            full_link = f"https://www.amazon.de{href.split('?')[0]}"
            if full_link not in links:
                links.append(full_link)
        if len(links) >= num_products:
            break

    driver.quit()
    return links


def scrape_product_info(url: str):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=de-DE")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0.0.0 Safari/537.36")

    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "productTitle")))
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract title
        title_tag = soup.select_one("#productTitle")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Extract bullet points
        bullets = [li.get_text(strip=True) for li in soup.select("#feature-bullets ul li") if li.get_text(strip=True)]

        # Extract description from multiple potential sources
        description = ""
        desc_tag = soup.select_one("#productDescription")
        if desc_tag:
            description = desc_tag.get_text(strip=True)
        else:
            aplus_tag = soup.select_one("div[data-cel-widget='aplus']")
            if aplus_tag:
                description = aplus_tag.get_text(strip=True)
            else:
                meta_tag = soup.find("meta", {"name": "description"})
                if meta_tag and meta_tag.get("content"):
                    description = meta_tag["content"].strip()

        return {
            "url": url,
            "title": title,
            "bullets": bullets,
            "description": description
        }

    except Exception as e:
        return {
            "url": url,
            "title": "",
            "bullets": [],
            "description": "",
            "error": str(e)
        }

    finally:
        driver.quit()
