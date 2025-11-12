import csv
import sys
import time
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

INPUT_CSV = Path("data/kaidee_listing_urls.csv")
OUTPUT_CSV = "data/kaidee_scraped_details.csv"


def first_text(elems):
    return elems[0].text.strip() if elems else ""


if not INPUT_CSV.exists():
    hits = list(Path.cwd().rglob("kaidee_listing_urls.csv"))
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


def page_loaded(driver):
    try_len = driver.execute_script(
        "return document.body && document.body.innerHTML ? document.body.innerHTML.length : 0"
    )
    return try_len and try_len > 500


def human_reload(driver, url):
    driver.get(url)
    time.sleep(0.6)
    ok = wait_present(driver, By.CSS_SELECTOR, ".item-detail-title", 8)
    if ok or page_loaded(driver):
        return True
    driver.refresh()
    time.sleep(0.6)
    ok = wait_present(driver, By.CSS_SELECTOR, ".item-detail-title", 8)
    if ok or page_loaded(driver):
        return True
    driver.get("https://www.kaidee.com/")
    time.sleep(1.2)
    driver.get(url)
    time.sleep(0.6)
    ok = wait_present(driver, By.CSS_SELECTOR, ".item-detail-title", 8)
    return ok or page_loaded(driver)


def scrape_one(driver, url):
    ok = human_reload(driver, url)
    if not ok:
        return None
    title = first_text(driver.find_elements(By.CSS_SELECTOR, ".item-detail-title"))
    price = first_text(
        driver.find_elements(By.CSS_SELECTOR, ".item-detail-price-value")
    )
    prop_info = driver.find_elements(
        By.CSS_SELECTOR, ".item-detail-main-info .detail-desc-info-item"
    )
    property_type = ""
    for p in prop_info:
        txt = p.text
        if "ประเภท" in txt or "Type" in txt:
            parts = txt.split(":", 1)
            property_type = parts[1].strip() if len(parts) > 1 else ""
            break
    desc = first_text(
        driver.find_elements(By.CSS_SELECTOR, ".item-detail-description-content")
    )
    phone = first_text(driver.find_elements(By.CSS_SELECTOR, ".seller-phone-number"))
    return {
        "URL": url,
        "Title": title,
        "Price": price,
        "PropertyType": property_type,
        "Description": desc,
        "MaskedPhone": phone,
    }


def main():
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.page_load_strategy = "eager"
    driver = uc.Chrome(options=options)

    with open(str(INPUT_CSV), "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        urls = [r[0].strip() for r in reader if r and r[0].strip()]

    rows = []
    for u in urls:
        r = scrape_one(driver, u)
        if r:
            rows.append(r)
        time.sleep(0.4)

    driver.quit()

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "URL",
                "Title",
                "Price",
                "PropertyType",
                "Description",
                "MaskedPhone",
            ],
        )
        w.writeheader()
        w.writerows(rows)
    print(f"Scraped {len(rows)} Kaidee listings")


if __name__ == "__main__":
    main()
