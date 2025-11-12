import re
import time
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

START_URL = (
    "https://www.kaidee.com/listing/for-sale/condo-apartment?region_id=1&province_id=16"
)
OUTPUT_CSV = "data/kaidee_listing_urls.csv"

ITEM_REGEX = re.compile(r"/item/(\d+)")


def human_reload(driver, url):
    driver.get(url)
    time.sleep(0.8)
    try:
        btns = driver.find_elements(By.CSS_SELECTOR, "button[onclick*='close']")
        btns = [e for e in btns if e.is_displayed()]
        if btns:
            driver.execute_script("arguments[0].click();", btns[0])
            time.sleep(0.3)
    except:
        pass
    return True


def main():
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.page_load_strategy = "eager"
    driver = uc.Chrome(options=options)

    urls = set()
    page = 1
    while page <= 15:
        url = f"{START_URL}&page={page}"
        human_reload(driver, url)
        time.sleep(0.5)
        items = driver.find_elements(By.CSS_SELECTOR, "div.items_index-item")
        if not items:
            break
        for item in items:
            link = item.find_elements(By.CSS_SELECTOR, "a.item-link")
            if link:
                href = link[0].get_attribute("href")
                if href:
                    urls.add(href)
        page += 1

    driver.quit()

    with open(OUTPUT_CSV, "w", encoding="utf-8") as f:
        f.write("URL\n")
        for url in sorted(urls):
            f.write(f"{url}\n")
    print(f"Collected {len(urls)} Kaidee URLs")


if __name__ == "__main__":
    main()
