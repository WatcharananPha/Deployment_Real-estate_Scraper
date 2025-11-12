"""browser.py
Centralized WebDriver creation and (optionally) login helpers.
This file provides a small Selenium-based helper. Replace or extend as needed.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing import Optional

from .config import settings


def build_driver(headless: Optional[bool] = None) -> webdriver.Chrome:
    headless = settings.HEADLESS if headless is None else headless
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(executable_path=settings.CHROME_DRIVER_PATH, options=opts)
    return driver


def close_driver(driver: webdriver.Chrome) -> None:
    try:
        driver.quit()
    except Exception:
        pass
