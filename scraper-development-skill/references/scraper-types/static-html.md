# Scraper Type: Static HTML (requests + BeautifulSoup)

Use only after Phase 1 step 3 (replay test) confirmed that a plain `requests.get()` with the
browser's captured headers returns the full page content including the target data.

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
CACHE_MAX_AGE_SECONDS = int(os.environ.get("CACHE_MAX_AGE_SECONDS", str(23 * 3600)))


def write_jsonl_record(out_file, record: dict) -> None:
    out_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    out_file.flush()


def fetch_page(url: str, session, web_cache, request_auth) -> str:
    entry = web_cache.get(url, max_age=CACHE_MAX_AGE_SECONDS)
    if entry:
        return entry["content"]

    with request_auth.acquire(DOMAIN) as permit:
        resp = session.get(url, timeout=30)
        permit.set_status(resp.status_code)
        if resp.status_code == 429:
            raise SystemExit(f"429 from {DOMAIN}; request-auth has been informed")
        resp.raise_for_status()
        html = resp.text

    web_cache.store(url, html, CLIENT_NAME)
    return html


def cache_image(image_url: str | None, session, img_cache, request_auth) -> str | None:
    if not image_url:
        return None
    meta = img_cache.lookup(image_url)
    if meta:
        return meta["content_hash"]

    with request_auth.acquire(DOMAIN) as permit:
        resp = session.get(image_url, timeout=15)
        permit.set_status(resp.status_code)
        resp.raise_for_status()
        image_bytes = resp.content

    return img_cache.store(image_url, image_bytes, CLIENT_NAME)["content_hash"]


def get_next_url(soup: BeautifulSoup, current_url: str) -> str | None:
    next_el = soup.select_one('a[rel="next"], .pagination .next:not(.disabled)')
    return urljoin(current_url, next_el["href"]) if next_el and next_el.get("href") else None


def main() -> None:
    session = requests.Session()
    request_auth = RequestAuthClient(REQUEST_AUTH_SERVER_URL)
    try:
        with WebCacheClient(WEBCACHE_URL) as web_cache, ImgCacheClient(IMGCACHE_URL) as img_cache:
            url = BASE_URL
            with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
                while url:
                    html = fetch_page(url, session, web_cache, request_auth)
                    soup = BeautifulSoup(html, "lxml")
                    cards = soup.select(".product-card")
                    if not cards:
                        break

                    for card in cards:
                        image_el = card.select_one("img.product-image")
                        image_url = image_el["src"] if image_el and image_el.get("src") else None
                        record = {
                            "site": CLIENT_NAME,
                            "source_url": url,
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                            "part_number": card.select_one(".sku-value").get_text(strip=True) if card.select_one(".sku-value") else "",
                            "title": card.select_one(".product-title").get_text(strip=True) if card.select_one(".product-title") else None,
                            "price": card.select_one("[data-price]").get("data-price") if card.select_one("[data-price]") else None,
                            "image_content_hash": cache_image(image_url, session, img_cache, request_auth),
                        }
                        write_jsonl_record(out, record)

                    url = get_next_url(soup, url)
    finally:
        request_auth.close()
```
