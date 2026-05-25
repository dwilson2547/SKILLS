# Scraper Type: Authenticated Session

Use when the target data requires login, or when an API endpoint requires browser-set session
cookies that cannot be reproduced without a real browser visit.

---

## Template

```python
#!/usr/bin/env python3

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from cache_client import WebCacheClient
from request_auth_client import RequestAuthClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

LOGIN_URL = "https://example.com/login"
TARGET_URL = "https://example.com/parts"
DOMAIN = urlparse(TARGET_URL).netloc
CLIENT_NAME = "my_scraper"
OUTPUT_FILE = Path(f"results_{datetime.now():%Y%m%d_%H%M%S}.jsonl")

WEBCACHE_URL = os.environ.get("WEBCACHE_URL", "http://webcache.scrapestack.local")
REQUEST_AUTH_SERVER_URL = os.environ.get(
    "REQUEST_AUTH_SERVER_URL",
    "request-auth-server.scrapestack.local:9000",
)


def write_jsonl_record(out_file, record: dict) -> None:
    out_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    out_file.flush()


def bootstrap_session() -> requests.Session:
    email = os.environ["SCRAPER_EMAIL"]
    password = os.environ["SCRAPER_PASSWORD"]
    session = requests.Session()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(LOGIN_URL, wait_until="networkidle")
        page.fill('input[type="email"], input[name="email"]', email)
        page.fill('input[type="password"], input[name="password"]', password)
        page.click('button[type="submit"], input[type="submit"]')
        page.wait_for_load_state("networkidle")

        for cookie in context.cookies():
            session.cookies.set(cookie["name"], cookie["value"], domain=cookie.get("domain"), path=cookie.get("path"))

        browser.close()

    return session


def fetch_page(url: str, session, web_cache, request_auth) -> str:
    entry = web_cache.get(url)
    if entry:
        return entry["content"]

    with request_auth.acquire(DOMAIN) as permit:
        resp = session.get(url, timeout=30)
        permit.set_status(resp.status_code)
        if resp.status_code in (401, 403):
            raise RuntimeError(f"Auth failure on {url}; session may have expired")
        if resp.status_code == 429:
            raise SystemExit(f"429 from {DOMAIN}; request-auth has been informed")
        resp.raise_for_status()
        html = resp.text

    web_cache.store(url, html, CLIENT_NAME)
    return html


def main() -> None:
    session = bootstrap_session()
    request_auth = RequestAuthClient(REQUEST_AUTH_SERVER_URL)
    try:
        with WebCacheClient(WEBCACHE_URL) as web_cache:
            url = TARGET_URL
            with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
                while url:
                    html = fetch_page(url, session, web_cache, request_auth)
                    soup = BeautifulSoup(html, "lxml")
                    for card in soup.select(".product-card"):
                        write_jsonl_record(out, {
                            "site": CLIENT_NAME,
                            "source_url": url,
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                            "part_number": card.select_one(".sku-value").get_text(strip=True) if card.select_one(".sku-value") else "",
                            "title": card.select_one(".product-title").get_text(strip=True) if card.select_one(".product-title") else None,
                            "price": card.select_one("[data-price]").get("data-price") if card.select_one("[data-price]") else None,
                        })

                    next_el = soup.select_one('a[rel="next"]')
                    url = urljoin(url, next_el["href"]) if next_el and next_el.get("href") else None
    finally:
        request_auth.close()
```
