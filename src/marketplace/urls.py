import re
import time
from pathlib import Path
import undetected_chromedriver as uc
from dotenv import load_dotenv
import os
from selenium.webdriver.common.by import By

load_dotenv("deployment/.env")
FACEBOOK_EMAIL = os.getenv("FACEBOOK_EMAIL", "")
FACEBOOK_PASSWORD = os.getenv("FACEBOOK_PASSWORD", "")

OUTPUT_CSV = "data/marketplace_listing_urls.csv"


def wait_present(driver, by, sel, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if driver.find_elements(by, sel):
            return True
        time.sleep(0.25)
    return False


def login_facebook(driver):
    driver.get("https://www.facebook.com/login")
    wait_present(driver, By.ID, "email", 10)
    email_field = driver.find_elements(By.ID, "email")
    pwd_field = driver.find_elements(By.ID, "pass")
    if email_field and pwd_field:
        email_field[0].send_keys(FACEBOOK_EMAIL)
        pwd_field[0].send_keys(FACEBOOK_PASSWORD)
        btns = driver.find_elements(By.CSS_SELECTOR, "button[type='submit']")
        if btns:
            btns[0].click()
            time.sleep(3)


def normalize_marketplace_url(url):
    if isinstance(url, str):
        url = url.strip()
        url = re.sub(r"[?#].*", "", url)
    return url


def scroll_load(driver, target_height):
    t0 = time.time()
    while time.time() - t0 < 12:
        h = driver.execute_script("return document.body.parentNode.scrollHeight")
        if h >= target_height:
            return True
        driver.execute_script(f"window.scrollTo(0, {target_height})")
        time.sleep(0.5)
    return False


def main():
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.page_load_strategy = "eager"
    driver = uc.Chrome(options=options)

    login_facebook(driver)
    time.sleep(2)

    urls = set()
    page = 1
    while page <= 20:
        url = f"https://www.facebook.com/marketplace/chiangmai/search/?query=condo&delivery_method=local_pickup&sortBy=creation_time_descending&page={page-1}"
        driver.get(url)
        time.sleep(1.2)
        scroll_load(driver, 3000)
        items = driver.find_elements(By.CSS_SELECTOR, "a[href*='/marketplace/item/']")
        if not items:
            break
        for item in items:
            href = item.get_attribute("href")
            if href:
                urls.add(normalize_marketplace_url(href))
        page += 1

    driver.quit()

    with open(OUTPUT_CSV, "w", encoding="utf-8") as f:
        f.write("URL\n")
        for url in sorted(urls):
            f.write(f"{url}\n")
    print(f"Collected {len(urls)} Marketplace URLs")


if __name__ == "__main__":
    main()
