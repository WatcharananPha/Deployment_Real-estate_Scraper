import re
import csv
import sys
import time
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

INPUT_CSV = Path("data/livinginsider_listing_urls.csv")
OUTPUT_CSV = "data/livinginsider_scraped_details.csv"


def first_text(elems):
    return elems[0].text.strip() if elems else ""


if not INPUT_CSV.exists():
    hits = list(Path.cwd().rglob("livinginsider_listing_urls.csv"))
    INPUT_CSV = hits[0] if hits else None
    if not INPUT_CSV:
        sys.exit(1)


def click_consent(driver):
    btns = driver.find_elements(By.CSS_SELECTOR, "#onetrust-accept-btn-handler")
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


def human_reload(driver, url):
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
    return ok or page_loaded(driver)


def parse_coords(text):
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)", text)
    return f"{m.group(1)},{m.group(2)}" if m else ""


def scrape_one(driver, url):
    ok = human_reload(driver, url)
    if not ok:
        return None
    desc = first_text(
        driver.find_elements(By.CSS_SELECTOR, "#desc-text-nl .wordwrap-box .wordwrap")
    )
    phone_nodes = driver.find_elements(
        By.CSS_SELECTOR, "a.p-phone-contact[data-zcgrbcb]"
    )
    phones = ", ".join(
        sorted(
            {
                n.get_attribute("data-zcgrbcb")
                for n in phone_nodes
                if n.get_attribute("data-zcgrbcb")
            }
        )
    )
    vc = [
        e.text.strip()
        for e in driver.find_elements(
            By.CSS_SELECTOR, ".box-show-view-click .text-custom-gray-new"
        )
    ]
    return {
        "URL": url,
        "Title": first_text(
            driver.find_elements(By.CSS_SELECTOR, "h1.font_sarabun.show-title")
        ),
        "Price": first_text(
            driver.find_elements(By.CSS_SELECTOR, ".show_price_topic .price_topic b")
        ),
        "PricePerArea": first_text(
            driver.find_elements(
                By.CSS_SELECTOR, ".show_price_topic .price_cal_area_text"
            )
        ),
        "PropertyType": first_text(
            driver.find_elements(
                By.CSS_SELECTOR, ".box_tag_topic_detail .box_tag_building"
            )
        ),
        "PostType": first_text(
            driver.find_elements(
                By.CSS_SELECTOR, ".box_tag_topic_detail .box_tag_posttype"
            )
        ),
        "Size": first_text(
            driver.find_elements(
                By.CSS_SELECTOR,
                ".detail_property_list_des_new .detail-property-list-text",
            )
        ),
        "Description": desc,
        "CreatedDate": first_text(
            driver.find_elements(By.CSS_SELECTOR, ".row-detail-time .font_10_date")
        ),
        "Boosted": first_text(
            driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'row-detail-time')]//span[contains(text(),'ดันประกาศล่าสุด')]",
            )
        ),
        "Location": first_text(
            driver.find_elements(
                By.CSS_SELECTOR, ".form-group.group-location-detail .detail-text-zone a"
            )
        ),
        "Views": vc[0] if len(vc) > 0 else "",
        "Clicks": vc[1] if len(vc) > 1 else "",
        "Coordinates": parse_coords(desc),
        "MaskedContacts": phones,
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
    print(f"Scraped {len(rows)} listings")


if __name__ == "__main__":
    main()
