# Scraper Type: Direct API (JSON Endpoint)

Use only after Phase 1 step 3 (replay test) confirmed that the captured API request returns the
expected data when replayed with `requests` using the browser's exact headers and cookies.

**Do not attempt this template if the replay hasn't been verified.** Modern APIs are routinely
secured with tokens, fingerprinting, or cookie chains that require a live browser. If you haven't
run the replay test, default to `scraper-types/playwright-rendered.md` instead.

If the API requires session cookies that can't be replayed, combine with
`scraper-types/authenticated.md` to bootstrap the session via Playwright, then use `requests`.

---

## Investigation Notes for This Type

During Phase 1, document these before writing code:

- **Endpoint URL** and all query parameters (page, limit, offset, sort, etc.)
- **Required headers**: `Authorization`, `X-Api-Key`, `Referer`, `Origin`, custom headers
- **Required cookies**: run the cookie isolation sub-routine if a bare request returns 403
- **Response schema**: what keys hold items, total count, next-page indicator
- **Pagination style**: `?page=N`, `?offset=N`, cursor token in response, or link headers

---

## Template

```python
#!/usr/bin/env python3
# Site: [Site Name]
# Strategy: ajax-api
# Discovered endpoint: [API URL from investigation]
# Last recon: [YYYY-MM-DD]

import json
import logging
import time
import random
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from bot_scraper_lib import build_context, RateLimiter, make_record, write_record

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# --- Config ---
BASE_URL  = "https://example.com/api/v1/parts"
DOMAIN    = urlparse(BASE_URL).netloc
PAGE_SIZE = 50
HEADERS   = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://example.com/",
    # "Authorization": "Bearer ...",  # add if required
}
OUTPUT_FILE = Path(f"results_{datetime.now():%Y%m%d_%H%M%S}.jsonl")

# --- Backoff ---
limiter = RateLimiter(DOMAIN)

SELECTORS = {
    # For API scrapers, document the response keys rather than CSS selectors
    "items_key":    "items",        # top-level key holding the list
    "total_key":    "total",        # key for total record count (or None)
    "part_number":  "sku",          # field name for part number
    "title":        "name",
    "price":        "price",
    "condition":    "condition",
    "image_url":    "image_url",
}


def fetch_page(session: requests.Session, page: int, ctx) -> dict:
    params = {"page": page, "limit": PAGE_SIZE}
    cache_url = f"{BASE_URL}?page={page}&limit={PAGE_SIZE}"
    entry = ctx.web_cache.get(cache_url)
    if entry:
        return json.loads(entry["content"])

    resp = session.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
    if resp.status_code == 429:
        limiter.ban(resp.headers.get("Retry-After"))
    resp.raise_for_status()

    ctx.web_cache.store(cache_url, resp.text, ctx.client_name)
    return resp.json()


def parse_item(item: dict, ctx) -> dict:
    image_url = item.get(SELECTORS["image_url"])
    image_hash = None
    if image_url and ctx.img_cache:
        try:
            meta = ctx.img_cache.lookup(image_url)
            if meta:
                image_hash = meta["content_hash"]
            else:
                import requests as req
                result = ctx.img_cache.store(image_url, req.get(image_url, timeout=15).content, ctx.client_name)
                image_hash = result["content_hash"]
        except Exception as e:
            logger.warning(f"Image cache failed for {image_url}: {e}")

    return make_record(
        DOMAIN,
        BASE_URL,
        part_number=str(item.get(SELECTORS["part_number"], "")),
        condition=item.get(SELECTORS["condition"], "new"),
        title=item.get(SELECTORS["title"]),
        price=item.get(SELECTORS["price"]),
        image_url=image_url,
        image_content_hash=image_hash,
        # video_content_hash=video_hash,  # add when with_videos=True
    )


def main():
    limiter.check()

    with build_context("my_scraper", with_images=True) as ctx:
        # Add with_videos=True for scrapers that collect video files.
        session = requests.Session()
        page = 1
        total_scraped = 0

        with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
            while True:
                logger.info(f"Fetching page {page}...")
                data = fetch_page(session, page, ctx)

                items = data.get(SELECTORS["items_key"], [])
                if not items:
                    logger.info("No more items.")
                    break

                for item in items:
                    record = parse_item(item, ctx)
                    write_record(record, out)
                    total_scraped += 1

                logger.info(f"Page {page}: {len(items)} items (total: {total_scraped})")

                # Check for last page
                total = data.get(SELECTORS["total_key"])
                if total and total_scraped >= total:
                    break
                if len(items) < PAGE_SIZE:
                    break

                page += 1
                limiter.wait(ajax=True)

    logger.info(f"Done. {total_scraped} records → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
```

---

## Gotchas

- **Session cookies required**: If bare `requests.get()` returns 403, the API needs browser-set
  cookies. Use `scraper-types/authenticated.md` to bootstrap, then continue with this template.
- **GraphQL**: POST to the endpoint with `{"query": "...", "variables": {...}}`. Cache the
  serialized request body as part of the cache key (append a hash of the variables to the URL).
- **Rate limit on API**: Some sites are more aggressive on API endpoints than HTML pages.
  Start at 1 req/s and watch for 429s before relaxing.
- **Cursor pagination**: Replace the `page` counter with the cursor token returned by each response.
