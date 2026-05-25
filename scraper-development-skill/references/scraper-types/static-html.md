# Scraper Type: Static HTML (requests + BeautifulSoup)

Use only after Phase 1 step 3 (replay test) confirmed that a plain `requests.get()` with the
browser's captured headers returns the full page content including the target data.

**Do not attempt this template without running the replay test first.** Many sites that appear
to serve static HTML still require session cookies, CSRF tokens, or specific headers set by JS
on first visit. If the replay hasn't been verified, default to `scraper-types/playwright-rendered.md`.

This is the lightest-weight scraper type when it works — pagination via URL params and no browser
overhead per page.

---

## Investigation Notes for This Type

During Phase 1, verify:
- Key data fields appear in `view-source:` or raw `requests.get()` response
- Pagination links are in the HTML (not injected by JS)
- No CSRF token required for page navigation
- robots.txt allows the target paths

---

## Template

```python
#!/usr/bin/env python3
# Site: [Site Name]
# Strategy: static-html
# Base URL: [URL]
# Last recon: [YYYY-MM-DD]

import json
import logging
import time
import random
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
from bot_scraper_lib import build_context, RateLimiter, make_record, write_record

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# --- Config ---
BASE_URL    = "https://example.com/parts"
DOMAIN      = urlparse(BASE_URL).netloc
OUTPUT_FILE = Path(f"results_{datetime.now():%Y%m%d_%H%M%S}.jsonl")
HEADERS     = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

limiter = RateLimiter(DOMAIN)

SELECTORS = {
    "item_container": ".product-card",
    "part_number":    ".sku-value",
    "title":          ".product-title",
    "price":          "[data-price]",
    "condition":      "[data-condition]",
    "image":          "img.product-image",
    "next_page":      'a[rel="next"], .pagination .next:not(.disabled)',
}


def fetch_page(url: str, session: requests.Session, ctx) -> str:
    entry = ctx.web_cache.get(url)
    if entry:
        logger.debug(f"Cache hit: {url}")
        return entry["content"]

    resp = session.get(url, headers=HEADERS, timeout=30)
    if resp.status_code == 429:
        limiter.ban(resp.headers.get("Retry-After"))
    resp.raise_for_status()
    ctx.web_cache.store(url, resp.text, ctx.client_name)
    return resp.text


def get_next_url(soup: BeautifulSoup, current_url: str) -> str | None:
    el = soup.select_one(SELECTORS["next_page"])
    if el and el.get("href"):
        return urljoin(current_url, el["href"])
    return None


def parse_items(soup: BeautifulSoup, page_url: str, ctx) -> list[dict]:
    records = []
    for card in soup.select(SELECTORS["item_container"]):
        part_el  = card.select_one(SELECTORS["part_number"])
        title_el = card.select_one(SELECTORS["title"])
        price_el = card.select_one(SELECTORS["price"])
        cond_el  = card.select_one(SELECTORS["condition"])
        img_el   = card.select_one(SELECTORS["image"])

        image_url  = img_el["src"] if img_el and img_el.get("src") else None
        image_hash = None
        if image_url and ctx.img_cache:
            try:
                meta = ctx.img_cache.lookup(image_url)
                if meta:
                    image_hash = meta["content_hash"]
                else:
                    img_bytes = requests.get(image_url, timeout=15).content
                    result = ctx.img_cache.store(image_url, img_bytes, ctx.client_name)
                    image_hash = result["content_hash"]
            except Exception as e:
                logger.warning(f"Image cache failed for {image_url}: {e}")

        records.append(make_record(
            DOMAIN,
            page_url,
            part_number=(part_el.get_text(strip=True) if part_el else "") or "",
            condition=cond_el.get("data-condition", "new") if cond_el else "new",
            title=title_el.get_text(strip=True) if title_el else None,
            price=price_el.get("data-price") if price_el else None,
            image_url=image_url,
            image_content_hash=image_hash,
            # video_content_hash=video_hash,  # add when with_videos=True
        ))
    return records


def main():
    limiter.check()

    with build_context("my_scraper", with_images=True) as ctx:
        # Add with_videos=True for scrapers that collect video files.
        session = requests.Session()
        url = BASE_URL
        page_num = 1
        total = 0

        with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
            while url:
                logger.info(f"Scraping page {page_num}: {url}")
                html = fetch_page(url, session, ctx)
                soup = BeautifulSoup(html, "lxml")

                records = parse_items(soup, url, ctx)
                if not records:
                    logger.info("No items on this page — stopping.")
                    break

                for record in records:
                    write_record(record, out)
                    total += 1

                logger.info(f"  → {len(records)} items (total: {total})")

                url = get_next_url(soup, url)
                page_num += 1
                if url:
                    limiter.wait()

    logger.info(f"Done. {total} records → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
```

---

## Gotchas

- **Relative vs absolute URLs in `href`**: always use `urljoin(current_url, href)` — never
  concatenate strings.
- **Content verified as static, then it wasn't**: some sites serve different HTML to bots. If
  results come back empty, verify with `curl -A "Mozilla/5.0..." <url>` — if that also returns
  empty content, the site is doing JS rendering for non-bot User-Agents.
- **Session cookies for pagination**: some sites set a session cookie on first visit that's
  required for subsequent pages. Always use `requests.Session()`, not bare `requests.get()`.
