import csv
import sys
import time
from pathlib import Path
import undetected_chromedriver as uc
from dotenv import load_dotenv
import os
from selenium.webdriver.common.by import By

load_dotenv("deployment/.env")
FACEBOOK_EMAIL = os.getenv("FACEBOOK_EMAIL", "")
FACEBOOK_PASSWORD = os.getenv("FACEBOOK_PASSWORD", "")

INPUT_CSV = Path("data/marketplace_listing_urls.csv")
OUTPUT_CSV = "data/marketplace_scraped_details.csv"


def first_text(elems):
    return elems[0].text.strip() if elems else ""


if not INPUT_CSV.exists():
    hits = list(Path.cwd().rglob("marketplace_listing_urls.csv"))
    INPUT_CSV = hits[0] if hits else None
    if not INPUT_CSV:
        sys.exit(1)


def wait_present(driver, by, sel, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if driver.find_elements(by, sel):
            return True
        time.sleep(0.25)
    return False


def login_facebook(driver):
    driver.get("https://www.facebook.com/login")
    wait_present(driver, By.ID, "email", 10)
    email_field = driver.find_elements(By.ID, "email")
    pwd_field = driver.find_elements(By.ID, "pass")
    if email_field and pwd_field:
        email_field[0].send_keys(FACEBOOK_EMAIL)
        pwd_field[0].send_keys(FACEBOOK_PASSWORD)
        btns = driver.find_elements(By.CSS_SELECTOR, "button[type='submit']")
        if btns:
            btns[0].click()
            time.sleep(3)


def page_loaded(driver):
    try_len = driver.execute_script(
        "return document.body && document.body.innerHTML ? document.body.innerHTML.length : 0"
    )
    return try_len and try_len > 1000


def human_reload(driver, url):
    driver.get(url)
    time.sleep(1.2)
    ok = wait_present(
        driver, By.CSS_SELECTOR, "span[data-uia='product_title_heading']", 8
    )
    if ok or page_loaded(driver):
        return True
    driver.refresh()
    time.sleep(1.2)
    ok = wait_present(
        driver, By.CSS_SELECTOR, "span[data-uia='product_title_heading']", 8
    )
    if ok or page_loaded(driver):
        return True
    driver.get("https://www.facebook.com/marketplace/chiangmai/")
    time.sleep(1.5)
    driver.get(url)
    time.sleep(1.2)
    ok = wait_present(
        driver, By.CSS_SELECTOR, "span[data-uia='product_title_heading']", 8
    )
    return ok or page_loaded(driver)


def deep_scroll_description(driver):
    desc_text = ""
    desc_header = driver.find_elements(
        By.XPATH,
        "//div[contains(text(), 'Description') or contains(text(), 'คำอธิบาย')]",
    )
    if desc_header:
        parent = desc_header[0]
        for _ in range(5):
            parent = parent.find_element(By.XPATH, "..")
        desc_sect = parent.find_elements(By.CSS_SELECTOR, "span, p")
        desc_text = " ".join([e.text.strip() for e in desc_sect if e.text.strip()])
    if not desc_text:
        t0 = time.time()
        while time.time() - t0 < 5:
            prev_h = driver.execute_script(
                "return document.body.parentNode.scrollHeight"
            )
            driver.execute_script(
                "window.scrollTo(0, document.body.parentNode.scrollHeight)"
            )
            time.sleep(0.3)
            new_h = driver.execute_script(
                "return document.body.parentNode.scrollHeight"
            )
            if new_h == prev_h:
                break
        desc_sect = driver.find_elements(
            By.CSS_SELECTOR,
            "div[data-uia*='description'] span, div[data-uia*='description'] p",
        )
        desc_text = " ".join([e.text.strip() for e in desc_sect if e.text.strip()])
    return desc_text


def scrape_one(driver, url):
    ok = human_reload(driver, url)
    if not ok:
        return None
    title = first_text(
        driver.find_elements(By.CSS_SELECTOR, "span[data-uia='product_title_heading']")
    )
    price = first_text(
        driver.find_elements(By.CSS_SELECTOR, "span[data-uia='product_price']")
    )
    desc = deep_scroll_description(driver)
    seller = first_text(
        driver.find_elements(By.CSS_SELECTOR, "span[data-uia*='seller']")
    )
    location = first_text(
        driver.find_elements(By.CSS_SELECTOR, "span[data-uia*='location']")
    )
    return {
        "URL": url,
        "Title": title,
        "Price": price,
        "Description": desc,
        "Seller": seller,
        "Location": location,
    }


def main():
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.page_load_strategy = "eager"
    driver = uc.Chrome(options=options)

    login_facebook(driver)
    time.sleep(2)

    with open(str(INPUT_CSV), "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        urls = [r[0].strip() for r in reader if r and r[0].strip()]

    rows = []
    for u in urls:
        r = scrape_one(driver, u)
        if r:
            rows.append(r)
        time.sleep(0.5)

    driver.quit()

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["URL", "Title", "Price", "Description", "Seller", "Location"]
        )
        w.writeheader()
        w.writerows(rows)
    print(f"Scraped {len(rows)} Marketplace listings")


if __name__ == "__main__":
    main()
