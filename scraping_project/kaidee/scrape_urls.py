import time
import csv
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

START_URL = (
    os.environ.get("KAIDEE_START")
    or "https://baan.kaidee.com/c2p1-realestate/chiangmai"
)
OUTPUT_CSV_FILE = os.environ.get("KAIDEE_OUTPUT") or "kaidee_listing_urls.csv"
PAGE_TIMEOUT = int(os.environ.get("KAIDEE_PAGE_TIMEOUT", 40))
MAX_PAGES = int(os.environ.get("KAIDEE_MAX_PAGES", 200))

PATTERN = re.compile(r"https://baan\.kaidee\.com/product-\d+")


def build_page_url(u, page):
    if page <= 1:
        return u
    if u.endswith("/"):
        return f"{u}p-{page}"
    return f"{u}/p-{page}"


def wait_ready(driver, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if driver.execute_script("return document.readyState") == "complete":
            return True
        time.sleep(0.2)
    return False


def deep_scroll(driver, rounds=12, pause=0.8):
    prev = 0
    for _ in range(rounds):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        cur = driver.execute_script("return document.body.scrollHeight")
        if cur == prev:
            break
        prev = cur


def extract_links(html):
    urls = set(PATTERN.findall(html))
    return sorted(urls)


def run():
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    driver = uc.Chrome(options=options)

    page = 1
    all_urls = set()
    last_first = ""

    while page <= MAX_PAGES:
        url = build_page_url(START_URL, page)
        driver.get(url)
        wait_ready(driver, PAGE_TIMEOUT)
        deep_scroll(driver, rounds=15, pause=0.8)

        html = driver.page_source
        links = extract_links(html)

        if not links:
            break
        if page > 1 and links[0] == last_first:
            break

        last_first = links[0]
        all_urls.update(links)
        page += 1

    driver.quit()

    if all_urls:
        with open(OUTPUT_CSV_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ListingURL"])
            for u in sorted(all_urls):
                w.writerow([u])


if __name__ == "__main__":
    run()
