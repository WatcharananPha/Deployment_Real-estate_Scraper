import time
import os
import csv
from pathlib import Path
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()
INPUT_CSV_FILE = Path(
    os.environ.get("FB_MARKETPLACE_INPUT")
    or Path.cwd() / "facebook_marketplace_urls.csv"
)
OUTPUT_CSV_FILE = Path(
    os.environ.get("FB_MARKETPLACE_DETAILS")
    or Path.cwd() / "facebook_marketplace_details.csv"
)
WEBDRIVER_WAIT_TIMEOUT = int(os.environ.get("FB_WAIT", 25))
SCROLL_STEP_PX = int(os.environ.get("FB_SCROLL_STEP", 900))
MAX_SCROLL_TRIES = int(os.environ.get("FB_MAX_SCROLL_TRIES", 15))


def scrape_marketplace_details(driver, url):
    wait = WebDriverWait(driver, WEBDRIVER_WAIT_TIMEOUT)
    details = {"URL": url}
    driver.get(url)
    h1 = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
    details["Title"] = h1.text.strip()
    price_xpath = "//h1/following-sibling::div[1]//span"
    details["Price"] = driver.find_element(By.XPATH, price_xpath).text.strip()
    detail_items = driver.find_elements(By.CSS_SELECTOR, "div[role='listitem'] span")
    property_details = [item.text.strip() for item in detail_items if item.text.strip()]
    details["Property_Details"] = " | ".join(property_details)
    desc_h2_xpath = (
        "//h2[.//span[contains(., 'คำอธิบาย')] or .//span[contains(., 'Description')]]"
    )
    desc_h2_elements = driver.find_elements(By.XPATH, desc_h2_xpath)
    if not desc_h2_elements:
        last_height = 0
        for i in range(MAX_SCROLL_TRIES):
            driver.execute_script(f"window.scrollBy(0, {SCROLL_STEP_PX});")
            time.sleep(0.8)
            desc_h2_elements = driver.find_elements(By.XPATH, desc_h2_xpath)
            if desc_h2_elements:
                break
            new_height = driver.execute_script("return document.body.scrollHeight;")
            if new_height == last_height:
                driver.execute_script(
                    "window.scrollTo(0, Math.max(document.documentElement.scrollTop - 600, 0));"
                )
                time.sleep(0.5)
            last_height = new_height
    description_text = ""
    if desc_h2_elements:
        desc_h2 = desc_h2_elements[0]
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior:'instant', block:'center'});",
            desc_h2,
        )
        time.sleep(0.6)
        containers = desc_h2.find_elements(
            By.XPATH,
            "./following-sibling::div | parent::div/following-sibling::div | ancestor::div[1]/following-sibling::div",
        )
        container = containers[0] if containers else None
        if not container:
            cands = driver.find_elements(
                By.XPATH,
                "//h2[.//span[contains(., 'คำอธิบาย') or contains(., 'Description')]]/following::div[1]",
            )
            container = cands[0] if cands else None
        if container:
            for _ in range(3):
                see_more = container.find_elements(
                    By.XPATH,
                    ".//div[@role='button'][.//span[contains(., 'ดูเพิ่มเติม') or contains(., 'See more')]]",
                )
                if see_more:
                    if ("ดูน้อยลง" in see_more[0].text) or (
                        "See less" in see_more[0].text
                    ):
                        break
                    driver.execute_script("arguments[0].click();", see_more[0])
                    time.sleep(0.6)
                else:
                    alt = desc_h2.find_elements(
                        By.XPATH,
                        "./following-sibling::div//div[@role='button'][.//span[contains(., 'ดูเพิ่มเติม') or contains(., 'See more')]]",
                    )
                    if alt:
                        driver.execute_script("arguments[0].click();", alt[0])
                        time.sleep(0.6)
                    else:
                        break
            spans = container.find_elements(
                By.XPATH, ".//span[string-length(normalize-space())>0]"
            )
            parts = [s.text.strip() for s in spans if s.text.strip()]
            description_text = (
                "\n".join(parts)
                if parts
                else (container.get_attribute("innerText") or "").strip()
            )
    details["Description"] = description_text
    return details


def run():
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--lang=en-US")
    options.add_argument(
        f"--user-data-dir={os.environ.get('FB_PROFILE_PATH','C:/chrome-profiles/fb-marketplace')}"
    )
    options.page_load_strategy = "eager"
    driver = uc.Chrome(options=options)
    driver.command_executor._client_config.timeout = 300
    driver.set_page_load_timeout(240)
    driver.set_script_timeout(240)

    wait = WebDriverWait(driver, WEBDRIVER_WAIT_TIMEOUT)
    driver.get("https://www.facebook.com/?locale=en_US")
    time.sleep(7)

    popup_container_selector = "div[aria-label='Accessible login form'], div[aria-label='เข้าสู่ระบบแบบช่วยการเข้าถึง']"
    popup_forms = driver.find_elements(By.CSS_SELECTOR, popup_container_selector)
    if popup_forms:
        popup_form = popup_forms[0]
        email_input = popup_form.find_element(By.NAME, "email")
        pass_input = popup_form.find_element(By.NAME, "pass")
        login_button = popup_form.find_element(
            By.CSS_SELECTOR, "div[aria-label*='Log in'], div[aria-label*='เข้าสู่ระบบ']"
        )
        email_input.clear()
        email_input.send_keys(FACEBOOK_EMAIL)
        pass_input.clear()
        pass_input.send_keys(FACEBOOK_PASSWORD)
        login_button.click()
        wait.until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, popup_container_selector)
            )
        )
        time.sleep(5)

    with open(INPUT_CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        urls_to_scrape = [row[0].strip() for row in reader if row and row[0].strip()]

    all_details = []
    for i, url in enumerate(urls_to_scrape):
        details = scrape_marketplace_details(driver, url)
        all_details.append(details)
        time.sleep(2.5)

    driver.quit()

    if all_details:
        headers = ["URL", "Title", "Price", "Property_Details", "Description"]
        with open(OUTPUT_CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(all_details)


if __name__ == "__main__":
    run()
