from datetime import datetime, timezone
import os
import re
import time
from pathlib import Path
from typing import List

import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

from ..common.config import settings

FACEBOOK_EMAIL = os.environ.get("FACEBOOK_EMAIL")
FACEBOOK_PASSWORD = os.environ.get("FACEBOOK_PASSWORD")

GROUP_URLS = []


def parse_relative_time_to_days(time_str):
    s = (time_str or "").strip().lower()
    if not s:
        return 999
    if "เมื่อสักครู่" in s or "just now" in s:
        return 0
    if "นาที" in s or "minute" in s or "min" in s:
        return 0
    if "ชม" in s or "ชั่วโมง" in s or "hour" in s or "hrs" in s or "hr" in s:
        return 0
    m = re.search(r"(\d+)", s)
    n = int(m.group(1)) if m else 0
    if "วัน" in s or "day" in s or "d" == s[-1:]:
        return n
    if "สัปดาห์" in s or "week" in s or "wk" in s or "w" == s[-1:]:
        return n * 7
    if "เดือน" in s or "month" in s or "mo" in s:
        return n * 30
    if "ปี" in s or "year" in s or "yr" in s:
        return n * 365
    return 999


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
    ok = wait_present(
        driver,
        By.CSS_SELECTOR,
        "div[role='main'], #m_group_stories_container, article",
        8,
    )
    if ok or page_loaded(driver):
        return True
    driver.refresh()
    ok = wait_present(
        driver,
        By.CSS_SELECTOR,
        "div[role='main'], #m_group_stories_container, article",
        8,
    )
    if ok or page_loaded(driver):
        return True
    driver.get("https://www.livinginsider.com/")
    time.sleep(1.2)
    driver.get(url)
    ok = wait_present(
        driver,
        By.CSS_SELECTOR,
        "div[role='main'], #m_group_stories_container, article",
        8,
    )
    if ok or page_loaded(driver):
        return True
    return False


def normalize_group_url(u):
    v = u.strip()
    v = v.replace("://facebook.com", "://www.facebook.com")
    v = v.replace("://www.facebook.com", "://m.facebook.com")
    if "/members" in v:
        v = v.split("/members")[0] + "/"
    if not v.endswith("/"):
        v = v + "/"
    return v


def collect_group_post_urls(driver, group_url):
    group_url = normalize_group_url(group_url)
    ok_nav = human_reload_flow(driver, group_url)
    if not ok_nav:
        return []
    seen = set()
    results = []
    prev_len = 0
    stagnant = 0
    loops = 0
    stop = False
    while True:
        data = driver.execute_script(
            """
            function absUrl(href){ if(!href) return null; if(href.indexOf('http')===0) return href.split('?')[0]; return location.origin + href.split('?')[0]; }
            var posts = Array.from(document.querySelectorAll('article, div[role="article"]'));
            var out = [];
            for (var i=0;i<posts.length;i++){
                var p = posts[i];
                var a = p.querySelector("a[href*='/posts/'], a[href*='/permalink/'], a[href*='story.php']");
                if(!a) continue;
                var href = absUrl(a.getAttribute('href'));
                if(!href) continue;
                var t = p.querySelector("a[aria-label], time[aria-label], abbr[aria-label]");
                var tlabel = null;
                if(t){ tlabel = t.getAttribute('aria-label') || t.textContent || ""; }
                if(!tlabel){
                    var t2 = p.querySelector("span[aria-label], div[aria-label]");
                    if(t2){ tlabel = t2.getAttribute('aria-label') || t2.textContent || ""; }
                }
                var ut = null;
                var uel = p.querySelector('abbr[data-utime], time[data-utime]');
                if(uel){ var v = parseInt(uel.getAttribute('data-utime')); if(!isNaN(v)) ut = v; }
                out.push([href, tlabel, ut]);
            }
            return out;
        """
        )
        for href, tlabel, ut in data:
            if href in seen:
                continue
            days_ago = parse_relative_time_to_days(tlabel)
            if (days_ago == 999) and ut:
                now_epoch = int(datetime.now(timezone.utc).timestamp())
                diff_days = int((now_epoch - int(ut)) // 86400)
                days_ago = diff_days if diff_days >= 0 else 999
            seen.add(href)
            if days_ago <= 7:
                results.append(href)
            elif days_ago > 7:
                stop = True
                break
        if stop:
            break
        driver.execute_script("window.scrollBy(0, 1400);")
        time.sleep(1.4)
        curr_len = len(seen)
        if curr_len == prev_len:
            stagnant += 1
        else:
            stagnant = 0
        prev_len = curr_len
        loops += 1
        if stagnant >= 6 or loops >= 3000:
            break
    return results


def run(group_urls: List[str], output_csv: str):
    out_dir = Path(output_csv).parent
    if out_dir and not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--lang=en-US")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    profile_dir = os.environ.get("FB_PROFILE_PATH")
    if profile_dir:
        options.add_argument(f"--user-data-dir={profile_dir}")
    options.page_load_strategy = "eager"
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(90)
    driver.set_script_timeout(90)
    for i, link in enumerate(group_urls, start=1):
        urls = collect_group_post_urls(driver, link)
        rows = [{"group": link, "post_url": u} for u in urls]
        if rows:
            df_out = pd.DataFrame(rows, columns=["group", "post_url"])
            if Path(output_csv).exists():
                df_out.to_csv(
                    output_csv,
                    mode="a",
                    header=False,
                    index=False,
                    encoding="utf-8-sig",
                )
            else:
                df_out.to_csv(output_csv, index=False, encoding="utf-8-sig")
    driver.quit()


if __name__ == "__main__":
    out = os.environ.get("FB_GROUP_OUTPUT") or str(
        Path.cwd() / "facebook_group_post_urls.csv"
    )
    GROUP_URLS = GROUP_URLS or []
    run(GROUP_URLS, out)

from typing import List
import pandas as pd


def scrape_group_urls(group_urls: List[str]) -> pd.DataFrame:
    cols = ["group_id", "post_id", "post_url", "extracted_at"]
    return pd.DataFrame(columns=cols)


if __name__ == "__main__":
    print("facebook.scrape_group_urls placeholder")
