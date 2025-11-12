import time
import os
import csv
import re
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()
FACEBOOK_EMAIL = os.environ.get("FACEBOOK_EMAIL")
FACEBOOK_PASSWORD = os.environ.get("FACEBOOK_PASSWORD")
START_URL = (
    os.environ.get("FB_MARKETPLACE_START")
    or "https://www.facebook.com/marketplace/chiangmai/propertyrentals/?exact=false"
)
OUTPUT_CSV_FILE = (
    os.environ.get("FB_MARKETPLACE_OUTPUT") or "facebook_marketplace_urls.csv"
)
TARGET_URL_COUNT = int(os.environ.get("FB_MARKETPLACE_TARGET", 500))
WEBDRIVER_WAIT_TIMEOUT = int(os.environ.get("FB_WAIT", 20))


def normalize_marketplace_url(u):
    if not u:
        return None
    u = u.strip().split("?")[0].split("#")[0]
    m = re.search(r"/marketplace/item/(\d+)", u)
    if not m:
        return None
    item_id = m.group(1)
    return f"https://www.facebook.com/marketplace/item/{item_id}/"


def run():
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_argument(
        f"--user-data-dir={os.environ.get('FB_PROFILE_PATH','C:/chrome-profiles/fb-marketplace')}"
    )

    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, WEBDRIVER_WAIT_TIMEOUT)

    driver.get(START_URL)

    time.sleep(7)
    popup_container_selector = "div[aria-label='Accessible login form']"
    popup_forms = driver.find_elements(By.CSS_SELECTOR, popup_container_selector)

    if popup_forms:
        popup_form = popup_forms[0]
        email_input = popup_form.find_element(By.NAME, "email")
        pass_input = popup_form.find_element(By.NAME, "pass")
        login_button_selector = "div[aria-label='Log in to Facebook']"
        login_button = popup_form.find_element(By.CSS_SELECTOR, login_button_selector)
        email_input.send_keys(FACEBOOK_EMAIL)
        pass_input.send_keys(FACEBOOK_PASSWORD)
        login_button.click()
        wait.until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, popup_container_selector)
            )
        )
        time.sleep(5)

    all_listing_urls = set()
    stagnant_scrolls = 0

    while len(all_listing_urls) < TARGET_URL_COUNT:
        last_height = driver.execute_script("return document.body.scrollHeight")
        item_link_selector = "a[href*='/marketplace/item/']"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, item_link_selector))
        )
        listing_elements = driver.find_elements(By.CSS_SELECTOR, item_link_selector)
        for element in listing_elements:
            raw = element.get_attribute("href")
            norm = normalize_marketplace_url(raw)
            if norm:
                all_listing_urls.add(norm)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            stagnant_scrolls += 1
        else:
            stagnant_scrolls = 0
        if stagnant_scrolls >= 5:
            break

    driver.quit()

    if all_listing_urls:
        final_urls = sorted(list(all_listing_urls))[:TARGET_URL_COUNT]
        with open(OUTPUT_CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["MarketplaceURL"])
            for url in final_urls:
                writer.writerow([url])


if __name__ == "__main__":
    run()
