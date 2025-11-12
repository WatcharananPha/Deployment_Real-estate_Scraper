import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import undetected_chromedriver as uc
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()
FACEBOOK_EMAIL = os.getenv("FACEBOOK_EMAIL")
FACEBOOK_PASSWORD = os.getenv("FACEBOOK_PASSWORD")
OUTPUT_CSV_FILE = "data/facebook_group_urls.csv"
PROFILE_PATH = "chrome-profile/fb-group-stage1"

GROUP_URLS = [
    "https://www.facebook.com/groups/302468990428489/",
    "https://www.facebook.com/groups/322977734828852/",
    "https://www.facebook.com/groups/812156038944325/",
    "https://www.facebook.com/groups/1472146056424210/",
    "https://www.facebook.com/groups/426467944402414/",
    "https://www.facebook.com/groups/homerentcm/",
    "https://www.facebook.com/groups/509895225859790/",
    "https://www.facebook.com/groups/1299302030158649/",
    "https://www.facebook.com/groups/530492663958652/",
    "https://www.facebook.com/groups/596670275854317/",
    "https://www.facebook.com/groups/cnxre/",
    "https://www.facebook.com/groups/1885263611797363/",
    "https://www.facebook.com/groups/1897854047114064/",
    "https://www.facebook.com/groups/303531690102574/",
    "https://www.facebook.com/groups/1881982752029163/",
    "https://www.facebook.com/groups/568026117396809/",
    "https://www.facebook.com/groups/1928645537294336/",
    "https://www.facebook.com/groups/298821664628156/",
    "https://www.facebook.com/groups/903971886395138/",
    "https://www.facebook.com/groups/142702946428033/members",
    "https://www.facebook.com/groups/250469775470436/",
    "https://www.facebook.com/groups/1873094122912006/",
    "https://www.facebook.com/groups/2083392538672247/",
    "https://www.facebook.com/groups/864193946960728/",
    "https://www.facebook.com/groups/baanchiangmai/",
    "https://www.facebook.com/groups/694087674785430/",
    "https://www.facebook.com/groups/411301775702951/",
    "https://www.facebook.com/groups/169718747164928/",
    "https://www.facebook.com/groups/1475061816108017/",
    "https://www.facebook.com/groups/1582425938465943/",
    "https://www.facebook.com/groups/sale.rent.poolvillachiangmai/",
    "https://www.facebook.com/groups/251125079442673/",
    "https://www.facebook.com/groups/1034329704984830/",
    "https://www.facebook.com/groups/203683550205761/",
    "https://www.facebook.com/groups/1450131905304596/",
    "https://www.facebook.com/groups/959493160788393/",
    "https://www.facebook.com/groups/2897034136980512/",
    "https://www.facebook.com/groups/korn.property/",
    "https://www.facebook.com/groups/1456428424593312/",
    "https://www.facebook.com/groups/152080739566471/",
    "https://www.facebook.com/groups/Land.House.C.M.2014/",
    "https://www.facebook.com/groups/2336780789695894/",
    "https://www.facebook.com/groups/236116797208244/",
    "https://www.facebook.com/groups/landhomechiangmai/",
]


def login(driver):
    print("Login -> opening m.facebook.com")
    driver.get("https://m.facebook.com")
    time.sleep(3)
    for s in [
        "button[data-cookiebanner='accept_button_dialog']",
        "button[title='Allow all cookies']",
        "button[title='Accept All']",
        "button[aria-label='Allow all cookies']",
    ]:
        btns = driver.find_elements(By.CSS_SELECTOR, s)
        if btns and btns[0].is_displayed():
            btns[0].click()
            time.sleep(2)
            break
    email = driver.find_elements(By.ID, "m_login_email")
    pwd = driver.find_elements(By.ID, "m_login_password")
    if not email:
        email = driver.find_elements(By.ID, "email")
        pwd = driver.find_elements(By.ID, "pass")
    if email and pwd:
        email[0].clear()
        email[0].send_keys(FACEBOOK_EMAIL)
        pwd[0].send_keys(FACEBOOK_PASSWORD)
        pwd[0].send_keys(Keys.RETURN)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "a[aria-label='Menu'], a[aria-label='Home'], a[aria-label='Search']",
                )
            )
        )
    print("Login -> completed")


def parse_days(time_str):
    s = (time_str or "").strip().lower()
    if not s or "เมื่อสักครู่" in s or "just now" in s:
        return 0
    if (
        "นาที" in s
        or "minute" in s
        or "min" in s
        or "ชม" in s
        or "ชั่วโมง" in s
        or "hour" in s
        or "hrs" in s
        or "hr" in s
    ):
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


def human_reload(driver, url):
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
    return ok or page_loaded(driver)


def normalize_url(u):
    v = (
        u.strip()
        .replace("://facebook.com", "://www.facebook.com")
        .replace("://www.facebook.com", "://m.facebook.com")
    )
    if "/members" in v:
        v = v.split("/members")[0] + "/"
    return v if v.endswith("/") else v + "/"


def collect_urls(driver, group_url):
    group_url = normalize_url(group_url)
    print(f"Group -> loading {group_url}")
    ok_nav = human_reload(driver, group_url)
    if not ok_nav:
        print("Group -> load failed, skipping")
        return []
    seen = set()
    results = []
    prev_len = 0
    stagnant = 0
    loops = 0
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
            days_ago = parse_days(tlabel)
            if (days_ago == 999) and ut:
                now_epoch = int(datetime.now(timezone.utc).timestamp())
                diff_days = int((now_epoch - int(ut)) // 86400)
                days_ago = diff_days if diff_days >= 0 else 999
            seen.add(href)
            if days_ago <= 7:
                results.append(href)
            elif days_ago > 7:
                return results
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
    print(f"Group -> collected {len(results)} URLs (<=7 days)")
    return results


def main():
    out_dir = Path(os.path.dirname(OUTPUT_CSV_FILE))
    if out_dir and not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)
    print("Init -> creating Chrome profile")
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--lang=en-US")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    options.page_load_strategy = "eager"
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(90)
    driver.set_script_timeout(90)
    login(driver)
    print("Run -> collecting from all groups")
    rows = []
    total = 0
    for i, link in enumerate(GROUP_URLS, start=1):
        print(f"Group {i}/{len(GROUP_URLS)}")
        urls = collect_urls(driver, link)
        for u in urls:
            rows.append(
                {
                    "group_name": link.split("/groups/")[1].split("/")[0],
                    "group_url": link,
                    "post_url": u,
                }
            )
        total += len(urls)
        print(f"Total: {total} URLs")
        time.sleep(1.0)
    driver.quit()
    print(f"Save -> writing {OUTPUT_CSV_FILE} with {len(rows)} rows")
    df = pd.DataFrame(rows, columns=["group_name", "group_url", "post_url"])
    df.to_csv(OUTPUT_CSV_FILE, index=False, encoding="utf-8-sig")
    print("Done")


if __name__ == "__main__":
    main()
