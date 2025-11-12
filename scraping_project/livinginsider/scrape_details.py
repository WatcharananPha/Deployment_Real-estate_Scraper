import re
import csv
import sys
import time
from pathlib import Path
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

INPUT_CSV = Path(
    os.environ.get("LIV_INPUT") or Path("Scraping") / "livinginsider_listing_urls.csv"
)
OUTPUT_CSV = os.environ.get("LIV_DETAILS_OUTPUT") or "livinginsider_scraped_details.csv"


def first_text(elems):
    return elems[0].text.strip() if elems else ""


def resolve_csv(p):
    if p.exists():
        return p
    hits = [
        c
        for c in Path.cwd().rglob("livinginsider_listing_urls.csv")
        if c.parent.name == "Scraping"
    ]
    if hits:
        return hits[0]
    sys.exit(1)


def click_consent(driver):
    btns = []
    btns += driver.find_elements(By.CSS_SELECTOR, "#onetrust-accept-btn-handler")
    btns += driver.find_elements(
        By.XPATH, "//*[self::a or self::button][contains(., 'ยอมรับ')]"
    )
    btns = [e for e in btns if e.is_displayed() and e.is_enabled()]
    if btns:
        driver.execute_script("arguments[0].click();", btns[0])
        time.sleep(0.3)


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
    return try_len and try_len > 1000


def human_reload_flow(driver, url):
    driver.get(url)
    click_consent(driver)
    ok = wait_present(driver, By.CSS_SELECTOR, "div.space_padding_top_data", 8)
    if ok or page_loaded(driver):
        return True
    driver.refresh()
    click_consent(driver)
    ok = wait_present(driver, By.CSS_SELECTOR, "div.space_padding_top_data", 8)
    if ok or page_loaded(driver):
        return True
    driver.get("https://www.livinginsider.com/")
    time.sleep(1.2)
    driver.get(url)
    click_consent(driver)
    ok = wait_present(driver, By.CSS_SELECTOR, "div.space_padding_top_data", 8)
    if ok or page_loaded(driver):
        return True
    return False


def parse_coords(text):
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)", text)
    return f"{m.group(1)},{m.group(2)}" if m else ""


def scrape_one(driver, url):
    ok = human_reload_flow(driver, url)
    if not ok:
        return None
    title = first_text(
        driver.find_elements(By.CSS_SELECTOR, "h1.font_sarabun.show-title")
    )
    price = first_text(
        driver.find_elements(By.CSS_SELECTOR, ".show_price_topic .price_topic b")
    )
    price_per_area = first_text(
        driver.find_elements(By.CSS_SELECTOR, ".show_price_topic .price_cal_area_text")
    )
    prop_type = first_text(
        driver.find_elements(By.CSS_SELECTOR, ".box_tag_topic_detail .box_tag_building")
    )
    post_type = first_text(
        driver.find_elements(By.CSS_SELECTOR, ".box_tag_topic_detail .box_tag_posttype")
    )
    created_date = first_text(
        driver.find_elements(By.CSS_SELECTOR, ".row-detail-time .font_10_date")
    )
    boosted_text = first_text(
        driver.find_elements(
            By.XPATH,
            "//div[contains(@class,'row-detail-time')]//span[contains(text(),'ดันประกาศล่าสุด')]",
        )
    )
    size_text = first_text(
        driver.find_elements(
            By.CSS_SELECTOR, ".detail_property_list_des_new .detail-property-list-text"
        )
    )
    description = first_text(
        driver.find_elements(By.CSS_SELECTOR, "#desc-text-nl .wordwrap-box .wordwrap")
    )
    location_text = first_text(
        driver.find_elements(
            By.CSS_SELECTOR, ".form-group.group-location-detail .detail-text-zone a"
        )
    )
    vc = [
        e.text.strip()
        for e in driver.find_elements(
            By.CSS_SELECTOR, ".box-show-view-click .text-custom-gray-new"
        )
    ]
    views = vc[0] if len(vc) > 0 else ""
    clicks = vc[1] if len(vc) > 1 else ""
    coords = parse_coords(description)
    phone_nodes = driver.find_elements(
        By.CSS_SELECTOR, "a.p-phone-contact[data-zcgrbcb]"
    )
    phones_masked = []
    for n in phone_nodes:
        v = n.get_attribute("data-zcgrbcb") or ""
        if v:
            phones_masked.append(v)
    phones_masked = ", ".join(sorted(set(phones_masked)))
    return {
        "URL": url,
        "Title": title,
        "Price": price,
        "PricePerArea": price_per_area,
        "PropertyType": prop_type,
        "PostType": post_type,
        "Size": size_text,
        "Description": description,
        "CreatedDate": created_date,
        "Boosted": boosted_text,
        "Location": location_text,
        "Views": views,
        "Clicks": clicks,
        "Coordinates": coords,
        "MaskedContacts": phones_masked,
    }


csv_path = resolve_csv(INPUT_CSV)
options = uc.ChromeOptions()
options.add_argument("--disable-notifications")
options.add_argument("--start-maximized")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.page_load_strategy = "eager"
driver = uc.Chrome(options=options)

with open(str(csv_path), "r", encoding="utf-8") as f:
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
            "PricePerArea",
            "PropertyType",
            "PostType",
            "Size",
            "Description",
            "CreatedDate",
            "Boosted",
            "Location",
            "Views",
            "Clicks",
            "Coordinates",
            "MaskedContacts",
        ],
    )
    w.writeheader()
    w.writerows(rows)
