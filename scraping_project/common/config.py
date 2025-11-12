"""config.py
Load environment variables (via python-dotenv) and expose configuration values.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    DATA_DIR: str = os.environ.get("DATA_DIR", "data")
    HEADLESS: bool = os.environ.get("HEADLESS", "1") in ("1", "true", "True")
    CHROME_DRIVER_PATH: str = os.environ.get(
        "CHROME_DRIVER_PATH", "/usr/bin/chromedriver"
    )


settings = Settings()
