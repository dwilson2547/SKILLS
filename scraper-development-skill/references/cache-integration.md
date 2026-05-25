# Cache Integration

All new scrapers should be designed for the **scrape-stack** ecosystem by default.

- HTML / rendered page content → `WebCacheClient`
- Images → `ImgCacheClient`
- Videos → `VidCacheClient`
- Generic downloaded files → `FileCacheClient` when needed
- Target-site rate limiting / permits → `RequestAuthClient`

The old `bot_scraper_lib` guidance is obsolete. New scrapers should wire the scrape-stack clients
directly.

---

## Installation

```bash
pip install dwilson-cache-client
pip install dwilson-request-auth-client
```

Or install from local scrape-stack package directories if you are developing against the workspace:

```bash
pip install /path/to/web_scrapers/scrape_stack/libs/cache_client
pip install /path/to/web_scrapers/scrape_stack/services/request_authorization/client
```

---

## Default service endpoints

These should be the default assumptions for newly generated scrapers:

```python
import os

WEBCACHE_URL = os.environ.get("WEBCACHE_URL", "http://webcache.scrapestack.local")
IMGCACHE_URL = os.environ.get("IMGCACHE_URL", "http://imgcache.scrapestack.local")
VIDCACHE_URL = os.environ.get("VIDCACHE_URL", "http://vidcache.scrapestack.local")
FILECACHE_URL = os.environ.get("FILECACHE_URL", "http://filecache.scrapestack.local")
REQUEST_AUTH_SERVER_URL = os.environ.get(
    "REQUEST_AUTH_SERVER_URL",
    "request-auth-server.scrapestack.local:9000",
)
CACHE_MAX_AGE_SECONDS = int(os.environ.get("CACHE_MAX_AGE_SECONDS", str(23 * 3600)))
```

Use a stable lowercase `CLIENT_NAME` for every scraper (for example `"pyp"` or `"rockauto_parts"`).

---

## Client setup

```python
from cache_client import FileCacheClient, ImgCacheClient, VidCacheClient, WebCacheClient
from request_auth_client import RequestAuthClient

CLIENT_NAME = "my_scraper"

with WebCacheClient(WEBCACHE_URL) as web_cache, \
     ImgCacheClient(IMGCACHE_URL) as img_cache, \
     VidCacheClient(VIDCACHE_URL) as vid_cache, \
     FileCacheClient(FILECACHE_URL) as file_cache:
    request_auth = RequestAuthClient(REQUEST_AUTH_SERVER_URL)
    try:
        scrape(
            web_cache=web_cache,
            img_cache=img_cache,
            vid_cache=vid_cache,
            file_cache=file_cache,
            request_auth=request_auth,
        )
    finally:
        request_auth.close()
```

If a scraper does not need images, videos, or files, omit those clients rather than creating a
generic helper abstraction up front.

---

## WebCache — mandatory check-before-fetch

### `requests` pattern

```python
def fetch_html(url: str, session, web_cache, request_auth, domain: str) -> str:
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

### Playwright pattern

```python
def fetch_rendered_html(url: str, page, web_cache, request_auth, domain: str) -> str:
    entry = web_cache.get(url, max_age=CACHE_MAX_AGE_SECONDS)
    if entry:
        return entry["content"]

    with request_auth.acquire(domain) as permit:
        response = page.goto(url, wait_until="networkidle", timeout=30_000)
        permit.set_status(response.status if response else 0)
        html = page.content()

    web_cache.store(url, html, CLIENT_NAME)
    return html
```

**Important:** cache lookups and cache writes do **not** need request-auth permits. Permits wrap
only the actual target-site request.

---

## ImgCache — route image ingestion through scrape-stack

```python
def cache_image(image_url: str, session, img_cache, request_auth, domain: str) -> str | None:
    if not image_url:
        return None

    meta = img_cache.lookup(image_url)
    if meta:
        return meta["content_hash"]

    with request_auth.acquire(domain) as permit:
        resp = session.get(image_url, timeout=30)
        permit.set_status(resp.status_code)
        resp.raise_for_status()
        image_bytes = resp.content

    result = img_cache.store(image_url, image_bytes, CLIENT_NAME)
    return result["content_hash"]
```

Store the returned content hash in the scraper output rather than treating the source URL as a
durable identifier.

---

## VidCache / FileCache

If you are scraping large media files, prefer the cache service APIs over bespoke local storage.
For videos and generic files, use the appropriate scrape-stack client and keep target-site fetches
behind request-auth permits.

For files that the cache service can download server-side, prefer that pattern. For direct client
downloads, keep the fetch itself under `request_auth.acquire(domain)` and then upload/store the
bytes through the relevant cache client after the permit is released.
