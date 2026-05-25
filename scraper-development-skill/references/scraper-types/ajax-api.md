# Scraper Type: Direct API (JSON Endpoint)

Use only after Phase 1 step 3 (replay test) confirmed that the captured API request returns the
expected data when replayed with `requests` using the browser's exact headers and cookies.

**Do not attempt this template if the replay hasn't been verified.**

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

import requests
from cache_client import ImgCacheClient, WebCacheClient
from request_auth_client import RequestAuthClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://example.com/api/v1/parts"
DOMAIN = urlparse(BASE_URL).netloc
CLIENT_NAME = "my_scraper"
PAGE_SIZE = 50
OUTPUT_FILE = Path(f"results_{datetime.now():%Y%m%d_%H%M%S}.jsonl")

WEBCACHE_URL = os.environ.get("WEBCACHE_URL", "http://webcache.scrapestack.local")
IMGCACHE_URL = os.environ.get("IMGCACHE_URL", "http://imgcache.scrapestack.local")
REQUEST_AUTH_SERVER_URL = os.environ.get(
    "REQUEST_AUTH_SERVER_URL",
    "request-auth-server.scrapestack.local:9000",
)
CACHE_MAX_AGE_SECONDS = int(os.environ.get("CACHE_MAX_AGE_SECONDS", str(23 * 3600)))

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://example.com/",
}


def write_jsonl_record(out_file, record: dict) -> None:
    out_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    out_file.flush()


def fetch_page(session, page_num: int, web_cache, request_auth) -> dict:
    params = {"page": page_num, "limit": PAGE_SIZE}
    cache_key = f"{BASE_URL}?page={page_num}&limit={PAGE_SIZE}"
    entry = web_cache.get(cache_key, max_age=CACHE_MAX_AGE_SECONDS)
    if entry:
        return json.loads(entry["content"])

    with request_auth.acquire(DOMAIN) as permit:
        resp = session.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
        permit.set_status(resp.status_code)
        if resp.status_code == 429:
            raise SystemExit(f"429 from {DOMAIN}; request-auth has been informed")
        resp.raise_for_status()
        body = resp.text

    web_cache.store(cache_key, body, CLIENT_NAME)
    return json.loads(body)


def cache_image(image_url: str | None, session, img_cache, request_auth) -> str | None:
    if not image_url:
        return None
    meta = img_cache.lookup(image_url)
    if meta:
        return meta["content_hash"]

    with request_auth.acquire(DOMAIN) as permit:
        resp = session.get(image_url, timeout=30)
        permit.set_status(resp.status_code)
        resp.raise_for_status()
        image_bytes = resp.content

    return img_cache.store(image_url, image_bytes, CLIENT_NAME)["content_hash"]


def parse_item(item: dict, session, img_cache, request_auth) -> dict:
    image_url = item.get("image_url")
    return {
        "site": CLIENT_NAME,
        "source_url": BASE_URL,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "part_number": str(item.get("sku", "")),
        "title": item.get("name"),
        "price": item.get("price"),
        "condition": item.get("condition"),
        "image_content_hash": cache_image(image_url, session, img_cache, request_auth),
    }


def main() -> None:
    session = requests.Session()
    request_auth = RequestAuthClient(REQUEST_AUTH_SERVER_URL)
    try:
        with WebCacheClient(WEBCACHE_URL) as web_cache, ImgCacheClient(IMGCACHE_URL) as img_cache:
            page_num = 1
            with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
                while True:
                    data = fetch_page(session, page_num, web_cache, request_auth)
                    items = data.get("items", [])
                    if not items:
                        break
                    for item in items:
                        write_jsonl_record(out, parse_item(item, session, img_cache, request_auth))
                    if len(items) < PAGE_SIZE:
                        break
                    page_num += 1
    finally:
        request_auth.close()
```

---

## Notes

- Request-auth permits wrap only the target-site requests.
- Cache lookups/stores stay outside the permit.
- Do not add local `backoff.json` or a second rate limiter.
