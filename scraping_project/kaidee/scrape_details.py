import csv
import time
from pathlib import Path
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

OUTPUT_CSV_FILE = (
    os.environ.get("KAIDEE_DETAILS_OUTPUT") or "kaidee_scraped_details.csv"
)
WAIT = int(os.environ.get("KAIDEE_WAIT", 25))


def resolve_input_csv():
    cands = [
        Path("Scraping") / "kaidee_listing_urls.csv",
        Path("kaidee_listing_urls.csv"),
    ]
    for p in cands:
        if p.exists():
            return p
    found = list(Path.cwd().rglob("kaidee_listing_urls.csv"))
    if found:
        return found[0]
    return None


def scrape(driver, url):
    w = WebDriverWait(driver, WAIT)
    driver.get(url)
    btns = driver.find_elements(
        By.CSS_SELECTOR,
        "button[aria-label*='cookie i understand'], button[aria-label*='accept'], button:has(span[lang])",
    )
    if btns:
        driver.execute_script("arguments[0].click();", btns[0])
        time.sleep(0.3)
    title_el = w.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "h1.sc-747m9u-7"))
    )
    price_el = w.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.sc-1w68tq4-0 span.sc-3tpgds-0")
        )
    )
    desc_el = driver.find_elements(By.CSS_SELECTOR, "div.sc-1kndlp1-0 p.inner-text")
    area_el = driver.find_elements(
        By.XPATH, "//ul[@id='has-attributes']//li[.//span[text()='เนื้อที่']]//span//b"
    )
    phone_els = driver.find_elements(By.CSS_SELECTOR, "span.masked[data-value]")
    title = title_el.text.strip()
    price = price_el.text.strip()
    desc = desc_el[0].text.strip() if desc_el else ""
    area = area_el[0].text.strip() if area_el else ""
    phones = sorted(
        {
            e.get_attribute("data-value").strip()
            for e in phone_els
            if e.get_attribute("data-value")
        }
    )
    return {
        "URL": url,
        "Title": title,
        "Price": price,
        "Area": area,
        "Phone": ", ".join(phones),
        "Description": desc,
    }


def run():
    input_csv = resolve_input_csv()
    if not input_csv:
        return
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    driver = uc.Chrome(
        options=options, version_main=int(os.environ.get("CHROME_VERSION", 140))
    )
    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        urls = [r[0].strip() for r in reader if r and r[0].strip()]
    rows = []
    for u in urls:
        rows.append(scrape(driver, u))
        time.sleep(1)
    driver.quit()
    with open(OUTPUT_CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["URL", "Title", "Price", "Area", "Phone", "Description"]
        )
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    run()
