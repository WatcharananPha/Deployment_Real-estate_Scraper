import os
import time
import csv
from pathlib import Path
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()
FACEBOOK_EMAIL = os.environ.get('FACEBOOK_EMAIL')
FACEBOOK_PASSWORD = os.environ.get('FACEBOOK_PASSWORD')
INPUT_LINKS_CSV = Path(os.environ.get('FB_POST_URLS_CSV') or Path.cwd() / 'facebook_group_post_urls.csv')
OUTPUT_DETAILS_CSV = Path(os.environ.get('FB_POST_DETAILS_CSV') or Path.cwd() / 'facebook_post_details.csv')
PROFILE_PATH = os.environ.get('FB_PROFILE_PATH')
WAIT = int(os.environ.get('FB_WAIT', 30))

def click_cookie(driver):
    sels = [
        'button[data-cookiebanner="accept_button"]',
        'button[data-cookiebanner="accept_button_dialog"]',
        "button[title='Allow all cookies']",
        "button[aria-label='Allow all cookies']",
        "div[role='dialog'] div[aria-label*='cookies'] button",
    ]
    for s in sels:
        btns = driver.find_elements(By.CSS_SELECTOR, s)
        if btns and btns[0].is_displayed() and btns[0].is_enabled():
            btns[0].click()
            time.sleep(1)
            break

def login(driver):
    driver.get("https://www.facebook.com/?locale=en_US")
    time.sleep(2)
    click_cookie(driver)
    if "login" in driver.current_url.lower():
        WebDriverWait(driver, WAIT).until(EC.presence_of_element_located((By.ID, "email"))).send_keys(FACEBOOK_EMAIL)
        driver.find_element(By.ID, "pass").send_keys(FACEBOOK_PASSWORD)
        driver.find_element(By.NAME, "login").click()
    WebDriverWait(driver, WAIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="main"]')))

def expand_see_more(driver, root):
    driver.execute_script("""
        (function(root){
          function clickAll(){
            var q = (root||document).querySelectorAll("div[role='button'],span[role='button'],a[role='button']");
            var did=false;
            for (var i=0;i<q.length;i++){
              var t=(q[i].innerText||"").trim();
              if(!t) continue;
              if(t.includes("See more")||t.includes("See More")||t.includes("ดูเพิ่มเติม")||t.includes("เพิ่มเติม")){
                try{q[i].click();did=true;}catch(e){}
              }
            }
            return did;
          }
          var n=0; while(n<4 && clickAll()){ n++; }
        })(arguments[0]);
    """, root)

def extract_text(driver):
    txt = driver.execute_script("""
        function pick(){
          var sels=[
            "div[role='dialog'] [data-ad-rendering-role='story_message']",
            "div[role='main']  [data-ad-rendering-role='story_message']",
            "div[role='dialog'] [data-ad-preview='message']",
            "div[role='main']  [data-ad-preview='message']",
            "div[role='dialog'] article",
            "div[role='main']  article"
          ];
          for(var i=0;i<sels.length;i++){
            var e=document.querySelector(sels[i]);
            if(e){ return e; }
          }
          return document.querySelector("div[role='dialog']")||document.querySelector("div[role='main']");
        }
        var el=pick();
        return el? (el.textContent||"").trim() : "";
    """)
    if not txt:
        return ""
    bad = [
        "Like","Comment","Share","Send","Follow","Save","More",
        "ถูกใจ","แสดงความคิดเห็น","แชร์","ส่งข้อความ","บันทึก","ติดตาม"
    ]
    for b in bad:
        txt = txt.replace(b, " ")
    txt = " ".join(txt.split())
    return txt.strip()

def get_raw_post_text(driver, permalink):
    for step in range(3):
        driver.get(permalink)
        WebDriverWait(driver, WAIT).until(EC.any_of(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']")),
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='main']"))
        ))
        root = driver.find_elements(By.CSS_SELECTOR, "div[role='dialog'], div[role='main']")
        if root:
            expand_see_more(driver, root[0])
        text = extract_text(driver)
        if len(text) > 20:
            return text
        if step == 0:
            driver.refresh()
            time.sleep(2)
        else:
            driver.get("https://www.facebook.com/")
            time.sleep(1.5)
    return ""

if not FACEBOOK_EMAIL or not FACEBOOK_PASSWORD:
    raise SystemExit(1)
if not INPUT_LINKS_CSV.exists():
    raise SystemExit(1)

opts = uc.ChromeOptions()
if PROFILE_PATH:
    opts.add_argument(f'--user-data-dir={PROFILE_PATH}')
opts.add_argument('--disable-notifications')
opts.add_argument('--lang=en-US')
opts.page_load_strategy = "eager"
driver = uc.Chrome(options=opts)
driver.set_page_load_timeout(90)
driver.set_script_timeout(90)

login(driver)

with open(INPUT_LINKS_CSV, 'r', encoding='utf-8-sig', newline='') as infile, \
     open(OUTPUT_DETAILS_CSV, 'w', newline='', encoding='utf-8-sig') as outfile:
    r = csv.DictReader(infile)
    w = csv.writer(outfile)
    w.writerow(['Post_URL', 'Full_Post_Content'])
    for row in r:
        url = (row.get('PostURL') or '').strip()
        if not url:
            continue
        txt = get_raw_post_text(driver, url) or "N/A"
        w.writerow([url, txt])
        time.sleep(1.2)

driver.quit()