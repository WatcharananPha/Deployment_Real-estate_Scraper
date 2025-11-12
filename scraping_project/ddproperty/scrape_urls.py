import time
import csv
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

START_URL = (
    os.environ.get("DDP_START_URL") or "https://www.ddproperty.com/%E0%B8%A3%E0%B8% ..."
)
OUTPUT_CSV_FILE = os.environ.get("DDP_OUTPUT") or "ddproperty_listing_urls.csv"
WEBDRIVER_WAIT_TIMEOUT = int(os.environ.get("DDP_WAIT", 20))
MAX_PAGES = int(os.environ.get("DDP_MAX_PAGES", 200))

MONTH_ABBR = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
DATE_REGEX = re.compile(rf"\b{MONTH_ABBR}\s+\d{{1,2}},\s+\d{{4}}\b", re.I)
REL_REGEX = re.compile(r"(\d+)\s*(h|d|w|mo|y)\s*ago", re.I)
TH_TZ = timezone(timedelta(hours=7))


def build_page_url(start_url, page):
    u = urlparse(start_url)
    q = urlencode(dict(parse_qsl(u.query)), doseq=True)
    path = u.path.rstrip("/")
    m = re.match(r"^(.*?)(/\d+)$", path)
    base = m.group(1) if m else path
    new_path = base if page <= 1 else base + f"/{page}"
    return urlunparse((u.scheme, u.netloc, new_path, u.params, q, u.fragment))


def within_30_days(text):
    now = datetime.now(TH_TZ)
    m = DATE_REGEX.search(text)
    if m:
        dt = datetime.strptime(m.group(0), "%b %d, %Y").date()
        delta = (now.date() - dt).days
        return 0 <= delta <= 30
    m2 = REL_REGEX.search(text)
    if m2:
        n = int(m2.group(1))
        unit = m2.group(2).lower()
        if unit == "h":
            return True
        if unit == "d":
            return n <= 30
        if unit == "w":
            return n * 7 <= 30
        if unit == "mo":
            return n * 30 <= 30
        if unit == "y":
            return n * 365 <= 30
    return False


def run():
    print("Initializing Chrome Driver...")
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, WEBDRIVER_WAIT_TIMEOUT)

    first_url = build_page_url(START_URL, 1)
    driver.get(first_url)

    btns = driver.find_elements(By.XPATH, "//button[normalize-space(text())='ยอมรับ']")
    if btns:
        btns[0].click()
        time.sleep(1)

    all_listing_urls = set()
    page_num = 1
    last_first_href = ""

    while page_num <= MAX_PAGES:
        listing_sel = "a.listing-card-link, a.card-footer"
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, listing_sel)))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.4)

        cards = driver.find_elements(By.CSS_SELECTOR, listing_sel)
        hrefs_now = [e.get_attribute("href") for e in cards if e.get_attribute("href")]
        if not hrefs_now:
            break
        if page_num > 1 and hrefs_now[0] == last_first_href:
            break
        last_first_href = hrefs_now[0]

        hrefs_filtered = []
        for e in cards:
            h = e.get_attribute("href")
            if not h:
                continue
            rec_nodes = e.find_elements(
                By.XPATH,
                ".//span[@da-id='lc-feature-info' or contains(@class,'info-value') or (contains(@class,'pg-font-caption-xs') and contains(., 'โพสต์อีกครั้งเมื่อ'))]",
            )
            if not rec_nodes:
                anc = None
                try:
                    anc = e.find_element(
                        By.XPATH,
                        "./ancestor::div[contains(@class,'details-group-root') or contains(@class,'listing-card') or contains(@class,'content')][1]",
                    )
                except:
                    anc = None
                if anc:
                    rec_nodes = anc.find_elements(
                        By.XPATH,
                        ".//span[@da-id='lc-feature-info' or contains(@class,'info-value') or (contains(@class,'pg-font-caption-xs') and contains(., 'โพสต์อีกครั้งเมื่อ'))]",
                    )
            rec_text = rec_nodes[0].text if rec_nodes else e.text
            if within_30_days(rec_text):
                hrefs_filtered.append(h)

        new_urls = set(hrefs_filtered) - all_listing_urls
        all_listing_urls.update(hrefs_filtered)

        next_num = page_num + 1
        next_url = build_page_url(START_URL, next_num)
        prev_last = hrefs_now[-1]
        driver.get(next_url)

        t0 = time.time()
        changed = False
        while time.time() - t0 < WEBDRIVER_WAIT_TIMEOUT:
            state = driver.execute_script("return document.readyState")
            if state == "complete":
                els = driver.find_elements(By.CSS_SELECTOR, listing_sel)
                if els:
                    h = els[0].get_attribute("href")
                    hh = els[-1].get_attribute("href")
                    if h and h != last_first_href:
                        changed = True
                        break
                    if hh and hh != prev_last:
                        changed = True
                        break
            time.sleep(0.3)
        if not changed:
            break

        page_num = next_num

    driver.quit()

    if all_listing_urls:
        with open(OUTPUT_CSV_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ListingURL"])
            for url in sorted(all_listing_urls):
                w.writerow([url])


if __name__ == "__main__":
    run()
