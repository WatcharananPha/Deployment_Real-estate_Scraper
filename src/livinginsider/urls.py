import time
import csv
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

START_URL = "https://www.livinginsider.com/living_zone/45/all/all/1/%E0%B9%80%E0%B8%8A%E0%B8%B5%E0%B8%A2%E0%B8%87%E0%B9%83%E0%B8%AB%E0%B8%A1%E0%B9%88.html"
OUTPUT_CSV = "data/livinginsider_listing_urls.csv"
PAGE_TIMEOUT = 45
MAX_PAGES = 200


def build_page_url(u, page):
    p = urlparse(u)
    parts = [x for x in p.path.split("/") if x]
    k = None
    for i, seg in enumerate(parts):
        if re.fullmatch(r"\d+", seg):
            k = i
    if k is None:
        base = p.path.rstrip("/")
        new_path = base if page <= 1 else base + f"/{page}"
    else:
        parts[k] = "1" if page <= 1 else str(page)
        new_path = "/" + "/".join(parts)
    return urlunparse(
        (
            p.scheme,
            p.netloc,
            new_path,
            p.params,
            urlencode(dict(parse_qsl(p.query)), doseq=True),
            p.fragment,
        )
    )


def wait_ready(driver, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if driver.execute_script("return document.readyState") == "complete":
            return True
        time.sleep(0.2)
    return False


def deep_scroll(driver, rounds=18, pause=0.7):
    h0 = 0
    for _ in range(rounds):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        h = driver.execute_script("return document.body.scrollHeight")
        if h == h0:
            break
        h0 = h


def collect_links_js(driver, base):
    hrefs = driver.execute_script(
        """
const out = [];
const a1 = Array.from(document.querySelectorAll("a[href*='/livingdetail/'][href$='.html']"));
const a2 = Array.from(document.querySelectorAll("a[href^='/livingdetail/'][href$='.html']"));
const all = [...a1, ...a2];
for (const a of all){
  const h = a.getAttribute('href') || '';
  if (h && !h.includes('bclick') && !h.includes('stories') && !h.includes('banner')){
    out.push(h);
  }
}
return Array.from(new Set(out));
"""
    )
    fixed = []
    for h in hrefs:
        fixed.append(base + h if h.startswith("/") else h)
    return list(dict.fromkeys(fixed))


def main():
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    driver = uc.Chrome(options=options)
    base = f"{urlparse(START_URL).scheme}://{urlparse(START_URL).netloc}"

    page = 1
    all_urls = set()
    last_first = ""
    driver.get(build_page_url(START_URL, page))
    wait_ready(driver, PAGE_TIMEOUT)

    while page <= MAX_PAGES:
        deep_scroll(driver, rounds=20, pause=0.8)
        urls_now = collect_links_js(driver, base)
        if not urls_now:
            break
        if page > 1 and urls_now[0] == last_first:
            break
        last_first = urls_now[0]
        all_urls.update(urls_now)

        page += 1
        prev_last = urls_now[-1]
        driver.get(build_page_url(START_URL, page))
        t0 = time.time()
        changed = False
        while time.time() - t0 < PAGE_TIMEOUT:
            wait_ready(driver, 3)
            deep_scroll(driver, rounds=6, pause=0.6)
            cur = collect_links_js(driver, base)
            if cur and (cur[0] != last_first or cur[-1] != prev_last):
                changed = True
                break
            time.sleep(0.3)
        if not changed:
            break

    driver.quit()

    if all_urls:
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["url"])
            for u in sorted(all_urls):
                w.writerow([u])
        print(f"Collected {len(all_urls)} URLs")


if __name__ == "__main__":
    main()
