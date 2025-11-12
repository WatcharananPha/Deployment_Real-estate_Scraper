#!/usr/bin/env python3
import sys
import importlib.util
from pathlib import Path

PLATFORMS = {
    "facebook_urls": "src/facebook/group_urls.py",
    "facebook_details": "src/facebook/post_details.py",
    "ddproperty_urls": "src/ddproperty/urls.py",
    "ddproperty_details": "src/ddproperty/details.py",
    "livinginsider_urls": "src/livinginsider/urls.py",
    "livinginsider_details": "src/livinginsider/details.py",
    "kaidee_urls": "src/kaidee/urls.py",
    "kaidee_details": "src/kaidee/details.py",
    "marketplace_urls": "src/marketplace/urls.py",
    "marketplace_details": "src/marketplace/details.py",
}
def run_scraper(task):
    if task not in PLATFORMS:
        print(f"Unknown task: {task}")
        print(f"Available: {', '.join(PLATFORMS.keys())}")
        sys.exit(1)

    script = Path(PLATFORMS[task])
    if not script.exists():
        print(f"Script not found: {script}")
        sys.exit(1)

    print(f"\n==> Running {task}...")
    spec = importlib.util.spec_from_file_location("module", str(script))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()
    print(f"✓ {task} completed")


def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py <task> [<task2> ...]")
        print(f"Available tasks: {', '.join(PLATFORMS.keys())}")
        print("\nExamples:")
        print("  python run.py facebook_urls")
        print("  python run.py ddproperty_urls ddproperty_details")
        print(
            "  python run.py facebook_urls facebook_details livinginsider_urls livinginsider_details"
        )
        sys.exit(1)

    tasks = sys.argv[1:]
    for task in tasks:
        run_scraper(task)


if __name__ == "__main__":
    main()
