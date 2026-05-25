# Scraper Type: Playwright (JS-Rendered Content)

Use when Phase 1 confirms the target data is only present after JavaScript executes.

---

## Template

```python
#!/usr/bin/env python3

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import TimeoutError as PWTimeout, sync_playwright
from cache_client import ImgCacheClient, WebCacheClient
from request_auth_client import RequestAuthClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://example.com/parts"
DOMAIN = urlparse(BASE_URL).netloc
CLIENT_NAME = "my_scraper"
OUTPUT_FILE = Path(f"results_{datetime.now():%Y%m%d_%H%M%S}.jsonl")

WEBCACHE_URL = os.environ.get("WEBCACHE_URL", "http://webcache.scrapestack.local")
IMGCACHE_URL = os.environ.get("IMGCACHE_URL", "http://imgcache.scrapestack.local")
REQUEST_AUTH_SERVER_URL = os.environ.get(
    "REQUEST_AUTH_SERVER_URL",
    "request-auth-server.scrapestack.local:9000",
)


def write_jsonl_record(out_file, record: dict) -> None:
    out_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    out_file.flush()


def fetch_rendered_html(url: str, page, web_cache, request_auth) -> str:
    entry = web_cache.get(url)
    if entry:
        return entry["content"]

    with request_auth.acquire(DOMAIN) as permit:
        response = page.goto(url, wait_until="networkidle", timeout=30_000)
        permit.set_status(response.status if response else 0)
        html = page.content()

    web_cache.store(url, html, CLIENT_NAME)
    return html


def main() -> None:
    request_auth = RequestAuthClient(REQUEST_AUTH_SERVER_URL)
    try:
        with WebCacheClient(WEBCACHE_URL) as web_cache, ImgCacheClient(IMGCACHE_URL) as img_cache:
            with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
                with sync_playwright() as pw:
                    browser = pw.chromium.launch(headless=True)
                    page = browser.new_page()
                    fetch_rendered_html(BASE_URL, page, web_cache, request_auth)
                    try:
                        page.wait_for_selector(".product-card", timeout=10_000)
                    except PWTimeout:
                        raise RuntimeError("Timed out waiting for product cards")

                    items = page.evaluate("""() => {
                        return [...document.querySelectorAll('.product-card')].map(el => ({
                            part_number: el.querySelector('.sku-value')?.textContent?.trim() ?? '',
                            title: el.querySelector('.product-title')?.textContent?.trim() ?? null,
                            price: el.querySelector('[data-price]')?.getAttribute('data-price') ?? null,
                            image_url: el.querySelector('img.product-image')?.src ?? null,
                            source_url: window.location.href,
                        }));
                    }""")

                    for item in items:
                        image_hash = None
                        if item.get("image_url"):
                            meta = img_cache.lookup(item["image_url"])
                            image_hash = meta["content_hash"] if meta else None
                        write_jsonl_record(out, {
                            "site": CLIENT_NAME,
                            "source_url": item.get("source_url", BASE_URL),
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                            "part_number": item.get("part_number", ""),
                            "title": item.get("title"),
                            "price": item.get("price"),
                            "image_content_hash": image_hash,
                        })

                    browser.close()
    finally:
        request_auth.close()
```
