import time
import csv
from multiprocessing import Pool, cpu_count
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

INPUT_CSV_FILE = os.environ.get("DDP_INPUT") or "ddproperty_listing_urls.csv"
OUTPUT_CSV_FILE = (
    os.environ.get("DDP_DETAILS_OUTPUT") or "ddproperty_scraped_details.csv"
)
WEBDRIVER_WAIT_TIMEOUT = int(os.environ.get("DDP_WAIT", 25))
PROCESSES = max(
    1, min(cpu_count(), int(os.environ.get("DDP_PROCS", max(1, min(cpu_count(), 4)))))
)


def text_or_empty(driver, css):
    els = driver.find_elements(By.CSS_SELECTOR, css)
    return els[0].text.strip() if els else ""


def first_el(driver, css):
    els = driver.find_elements(By.CSS_SELECTOR, css)
    return els[0] if els else None


def click_js(driver, el):
    driver.execute_script("arguments[0].click();", el)


def any_visible(driver, selector):
    return driver.execute_script(
        """
        const sel = arguments[0];
        const els = document.querySelectorAll(sel);
        for (const el of els) {
            const cs = getComputedStyle(el);
            const r = el.getBoundingClientRect();
            if (cs.display !== 'none' && cs.visibility !== 'hidden' && parseFloat(cs.opacity) !== 0 && r.width > 0 && r.height > 0) {
                return true;
            }
        }
        return false;
    """,
        selector,
    )


def close_visible_modal(driver, wait, body_selectors):
    for sel in body_selectors:
        if any_visible(driver, sel):
            btn = first_el(
                driver,
                "button[da-id='modal-close-button'], button.btn-close, button[aria-label='Close']",
            )
            if btn:
                click_js(driver, btn)
            t0 = time.time()
            while (
                any_visible(driver, sel) and time.time() - t0 < WEBDRIVER_WAIT_TIMEOUT
            ):
                time.sleep(0.2)
            return


def scrape_listing_details(driver, url):
    wait = WebDriverWait(driver, WEBDRIVER_WAIT_TIMEOUT)
    details = {"URL": url}
    driver.get(url)
    btns = driver.find_elements(By.XPATH, "//button[normalize-space(text())='ยอมรับ']")
    if btns:
        click_js(driver, btns[0])
        time.sleep(1)
    main_content_selector = "div[da-id='property-snapshot-info']"
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, main_content_selector)))
    details["Title"] = text_or_empty(driver, "h1[da-id='property-title']")
    details["Address"] = text_or_empty(driver, "p[da-id='property-address']")
    price_txt = text_or_empty(driver, "h2[da-id='price-amount']")
    details["Price"] = price_txt.replace("฿", "").strip()
    amenity_cards = driver.find_elements(
        By.CSS_SELECTOR, "div.amenity[da-id*='-amenity']"
    )
    for a in amenity_cards:
        imgs = a.find_elements(By.TAG_NAME, "img")
        labels = [
            i.get_attribute("aria-label") for i in imgs if i.get_attribute("aria-label")
        ]
        val_el = a.find_elements(By.CSS_SELECTOR, "p.amenity-text")
        if labels and val_el:
            details[labels[0]] = val_el[0].text.strip()
    see_more_btn = first_el(
        driver, "button[da-id='meta-table-see-more-btn'], button[da-id='see-more-meta']"
    )
    if see_more_btn:
        click_js(driver, see_more_btn)
        modal_body_sel = "div.property-modal-body"
        WebDriverWait(driver, WEBDRIVER_WAIT_TIMEOUT).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, modal_body_sel))
        )
        modal_body = first_el(driver, modal_body_sel)
        if modal_body:
            wrappers = modal_body.find_elements(
                By.CSS_SELECTOR, "div.property-modal-body-wrapper"
            )
            for w in wrappers:
                icons = w.find_elements(By.TAG_NAME, "img")
                alts = [i.get_attribute("alt") for i in icons if i.get_attribute("alt")]
                val_el = w.find_elements(By.CSS_SELECTOR, "p.property-modal-body-value")
                if alts and val_el:
                    key = alts[0].replace("-o", "").replace("-", " ").title()
                    details[key] = val_el[0].text.strip()
        close_visible_modal(driver, wait, [modal_body_sel])
    read_more_btn = first_el(
        driver,
        "button[da-id='description-widget-show-more-lnk'], button[da-id='property-description-show-more']",
    )
    if read_more_btn:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", read_more_btn
        )
        time.sleep(0.5)
        click_js(driver, read_more_btn)
        desc_modal_selectors = [
            "div.description-modal-body",
            "div[da-id='description-modal-body']",
        ]
        expanded_desc_selectors = [
            "div[da-id='description-widget-body']",
            "div[da-id='description-text']",
            "div.property-description",
        ]
        desc_body = None
        t0 = time.time()
        while time.time() - t0 < WEBDRIVER_WAIT_TIMEOUT:
            for sel in desc_modal_selectors:
                el = first_el(driver, sel)
                if el and any_visible(driver, sel):
                    desc_body = el
                    break
            if desc_body:
                break
            for sel in expanded_desc_selectors:
                el = first_el(driver, sel)
                if el and el.text.strip():
                    details["Description"] = el.text.strip()
                    desc_body = None
                    break
            if "Description" in details:
                break
            time.sleep(0.2)
        if desc_body:
            html = desc_body.get_attribute("innerHTML") or ""
            details["Description"] = html.replace("<br>", "\n").strip()
            close_visible_modal(driver, wait, desc_modal_selectors)
        if "Description" not in details:
            details["Description"] = text_or_empty(
                driver, "div[da-id='description-widget-body']"
            )
    return details


def run_batch(urls):
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.page_load_strategy = "eager"
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(180)
    out = []
    for url in urls:
        d = scrape_listing_details(driver, url)
        out.append(d)
        time.sleep(2.0)
    driver.quit()
    return out


def chunk(seq, size):
    return [seq[i : i + size] for i in range(0, len(seq), size)]


if __name__ == "__main__":
    with open(INPUT_CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        urls_to_scrape = [row[0] for row in reader if row and row[0].strip()]
    if not urls_to_scrape:
        with open(OUTPUT_CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["URL"])
            writer.writeheader()
        raise SystemExit(0)
    batch_size = max(1, (len(urls_to_scrape) + PROCESSES - 1) // PROCESSES)
    batches = chunk(urls_to_scrape, batch_size)
    with Pool(PROCESSES) as pool:
        results = pool.map(run_batch, batches)
    all_details = [d for batch in results for d in batch]
    headers = sorted({"URL"} | {k for d in all_details for k in d.keys()})
    with open(OUTPUT_CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(all_details)
