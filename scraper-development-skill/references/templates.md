# Web Scraper Code Templates

> **Note:** For full scraper templates, use the documents in `references/scraper-types/`. This
> file is the quick reference for the shared scrape-stack patterns every generated scraper should
> follow.

---

## Client setup

```python
from cache_client import ImgCacheClient, VidCacheClient, WebCacheClient
from request_auth_client import RequestAuthClient

WEBCACHE_URL = os.environ.get("WEBCACHE_URL", "http://webcache.scrapestack.local")
IMGCACHE_URL = os.environ.get("IMGCACHE_URL", "http://imgcache.scrapestack.local")
VIDCACHE_URL = os.environ.get("VIDCACHE_URL", "http://vidcache.scrapestack.local")
REQUEST_AUTH_SERVER_URL = os.environ.get(
    "REQUEST_AUTH_SERVER_URL",
    "request-auth-server.scrapestack.local:9000",
)
CLIENT_NAME = "my_scraper"

with WebCacheClient(WEBCACHE_URL) as web_cache, ImgCacheClient(IMGCACHE_URL) as img_cache:
    request_auth = RequestAuthClient(REQUEST_AUTH_SERVER_URL)
    try:
        scrape(web_cache=web_cache, img_cache=img_cache, request_auth=request_auth)
    finally:
        request_auth.close()
```

---

## Mandatory cache-before-fetch pattern

```python
def fetch_page(url: str, session, web_cache, request_auth, domain: str) -> str:
    entry = web_cache.get(url, max_age=CACHE_MAX_AGE_SECONDS)
    if entry:
        return entry["content"]

    with request_auth.acquire(domain) as permit:
        resp = session.get(url, timeout=30)
        permit.set_status(resp.status_code)
        resp.raise_for_status()
        html = resp.text

    web_cache.store(url, html, CLIENT_NAME)
    return html
```

---

## Incremental JSONL save

Never accumulate all records in memory and write at the end.

```python
import json
from datetime import datetime
from pathlib import Path

OUTPUT_FILE = Path(f"results_{datetime.now():%Y%m%d_%H%M%S}.jsonl")

def write_jsonl_record(out_file, record: dict) -> None:
    out_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    out_file.flush()
```

Suggested record shape:

```python
record = {
    "site": "example_site",
    "source_url": page_url,
    "scraped_at": datetime.utcnow().isoformat(),
    "title": "...",
    "price": "...",
    "part_number": "...",
    "image_content_hash": "...",
}
```

---

## Image caching pattern

```python
def cache_image(image_url: str, session, img_cache, request_auth, domain: str) -> str | None:
    if not image_url:
        return None

    meta = img_cache.lookup(image_url)
    if meta:
        return meta["content_hash"]

    with request_auth.acquire(domain) as permit:
        resp = session.get(image_url, timeout=15)
        permit.set_status(resp.status_code)
        resp.raise_for_status()
        image_bytes = resp.content

    result = img_cache.store(image_url, image_bytes, CLIENT_NAME)
    return result["content_hash"]
```

---

## Request-auth pattern

```python
with request_auth.acquire(DOMAIN) as permit:
    resp = session.get(url, timeout=30)
    permit.set_status(resp.status_code)
    if resp.status_code == 429:
        raise SystemExit(f"429 from {DOMAIN}; request-auth has been informed")
    resp.raise_for_status()
```

Do not wrap cache-service calls in permits.

---

## Scraper header comment

```python
# Site: [Site Name]
# Strategy: [ajax-api | static-html | playwright-rendered | authenticated]
# Endpoint / Base URL: [URL]
# Last recon: [YYYY-MM-DD]
```
