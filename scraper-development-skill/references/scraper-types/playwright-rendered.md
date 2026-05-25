# Scraper Type: Playwright (JS-Rendered Content)

Use when Phase 1 confirms the target data is only present after JavaScript executes — it appears
in `playwright_get_visible_html` but NOT in a raw `requests.get()` response.

**Decision criteria:**
- No usable JSON API endpoint found
- Content requires JS execution (React/Vue/Angular SPA, lazy-loaded sections)
- Pagination is click-based (button/link with no URL change)
- Heavy bot detection (Cloudflare, PerimeterX) requiring full browser fingerprint

**Optimization goal:** use Playwright to render pages and extract content, but check webcache
first on every `goto()` to avoid re-rendering pages already seen.

---

## Investigation Notes for This Type

During Phase 1, document before writing code:

- **Wait condition**: which selector signals the page is fully loaded? (`networkidle` is safe
  but slow; a specific selector is faster)
- **Pagination mechanism**: click a button, scroll, or URL param?
- **Items per page**: so you know when you've hit the last page
- **Stealth needed**: does the site serve a CAPTCHA or challenge page on first visit?

---

## Template

```python
#!/usr/bin/env python3
# Site: [Site Name]
# Strategy: playwright-rendered
# Base URL: [URL]
# Last recon: [YYYY-MM-DD]

import json
import logging
import time
import random
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout
from bot_scraper_lib import build_context, RateLimiter, make_record, write_record

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# --- Config ---
BASE_URL    = "https://example.com/parts"
DOMAIN      = urlparse(BASE_URL).netloc
OUTPUT_FILE = Path(f"results_{datetime.now():%Y%m%d_%H%M%S}.jsonl")

limiter = RateLimiter(DOMAIN)

SELECTORS = {
    "item_container": ".product-card",
    "part_number":    ".sku-value",
    "title":          ".product-title",
    "price":          "[data-price]",
    "condition":      "[data-condition]",
    "image":          "img.product-image",
    "next_page":      'button[aria-label="Next page"]',
    "wait_for":       ".product-card",   # selector that signals page is ready
}


def fetch_page_html(url: str, page: Page, ctx) -> str:
    """Check webcache first; render with Playwright on miss."""
    entry = ctx.web_cache.get(url)
    if entry:
        logger.debug(f"Cache hit: {url}")
        return entry["content"]

    page.goto(url, wait_until="networkidle", timeout=30_000)
    page.wait_for_selector(SELECTORS["wait_for"], timeout=10_000)
    html = page.content()
    ctx.web_cache.store(url, html, ctx.client_name)
    return html


def extract_items(page: Page) -> list[dict]:
    return page.evaluate(f"""() => {{
        return [...document.querySelectorAll('{SELECTORS["item_container"]}')].map(el => ({{
            part_number: el.querySelector('{SELECTORS["part_number"]}')?.textContent?.trim() ?? null,
            title:       el.querySelector('{SELECTORS["title"]}')?.textContent?.trim() ?? null,
            price:       el.querySelector('{SELECTORS["price"]}')?.getAttribute('data-price') ?? null,
            condition:   el.querySelector('{SELECTORS["condition"]}')?.getAttribute('data-condition') ?? 'new',
            image_url:   el.querySelector('{SELECTORS["image"]}')?.src ?? null,
            source_url:  window.location.href,
        }}));
    }}""")


def scrape(page: Page, ctx, out) -> int:
    total = 0
    page_num = 1

    fetch_page_html(BASE_URL, page, ctx)   # loads page into browser if not from cache

    while True:
        # If page was served from cache, we still need the browser state for pagination clicks.
        # On cache hit, navigate normally but we won't store again.
        try:
            page.wait_for_selector(SELECTORS["wait_for"], timeout=10_000)
        except PWTimeout:
            logger.warning(f"Timed out waiting for items on page {page_num}")
            break

        items = extract_items(page)
        if not items:
            logger.info(f"No items on page {page_num} — done.")
            break

        for raw in items:
            image_hash = None
            if raw.get("image_url") and ctx.img_cache:
                try:
                    meta = ctx.img_cache.lookup(raw["image_url"])
                    if meta:
                        image_hash = meta["content_hash"]
                    else:
                        import requests as req
                        img_bytes = req.get(raw["image_url"], timeout=15).content
                        result = ctx.img_cache.store(raw["image_url"], img_bytes, ctx.client_name)
                        image_hash = result["content_hash"]
                except Exception as e:
                    logger.warning(f"Image cache failed for {raw['image_url']}: {e}")

            record = make_record(
                DOMAIN,
                raw.get("source_url", BASE_URL),
                part_number=raw.get("part_number") or "",
                condition=raw.get("condition", "new"),
                title=raw.get("title"),
                price=raw.get("price"),
                image_url=raw.get("image_url"),
                image_content_hash=image_hash,
                # video_content_hash=video_hash,  # add when with_videos=True
            )
            write_record(record, out)
            total += 1

        logger.info(f"Page {page_num}: {len(items)} items (total: {total})")

        # Pagination
        try:
            next_btn = page.locator(SELECTORS["next_page"]).first
            if not next_btn.is_visible() or not next_btn.is_enabled():
                logger.info("No next page button — done.")
                break
            current_url = page.url
            next_btn.click()
            page.wait_for_load_state("networkidle")
            # Cache the new page
            if page.url != current_url:
                html = page.content()
                ctx.web_cache.store(page.url, html, ctx.client_name)
            page_num += 1
            limiter.wait()
        except PWTimeout:
            logger.info("Pagination timed out — assuming last page.")
            break

    return total


def main():
    limiter.check()

    with build_context("my_scraper", with_images=True) as ctx:
        # Add with_videos=True for scrapers that collect video files.
        with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    viewport={"width": 1280, "height": 900},
                )
                # Intercept 429s from the browser
                def handle_response(response):
                    if response.status == 429:
                        limiter.ban()
                context.on("response", handle_response)

                page = context.new_page()
                try:
                    total = scrape(page, ctx, out)
                finally:
                    browser.close()

    logger.info(f"Done. {total} records → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
```

---

## Infinite Scroll Variant

Replace the pagination block in `scrape()` with:

```python
def scroll_to_load_all(page: Page, item_selector: str, max_scrolls: int = 50) -> None:
    prev_count = 0
    for i in range(max_scrolls):
        count = page.locator(item_selector).count()
        if count == prev_count:
            break
        prev_count = count
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)
    logger.info(f"Scroll complete: {prev_count} items after {i+1} scrolls")
```

---

## Stealth Mode

If the site serves a Cloudflare or bot-detection challenge, add before `browser.new_context()`:

```python
# pip install playwright-stealth
from playwright_stealth import stealth_sync
# after page = context.new_page():
stealth_sync(page)
```

Or use Camoufox for stronger fingerprint masking:
```python
# pip install camoufox
from camoufox.sync_api import Camoufox
with Camoufox(headless=True) as browser:
    ...
```

---

## Gotchas

- **Cache hit but browser needs state**: when a page is served from cache, the browser still
  needs to navigate there for pagination clicks to work. Navigate normally — `web_cache.store()`
  is idempotent (server returns 200 if already exists, 201 if new).
- **Dynamic class names**: React/Next.js apps use hashed classes like `sc-abc123` that change
  on every deploy. Use `data-testid`, `aria-label`, or text-content selectors instead.
- **Session expiry on long runs**: add a session-age check and re-navigate to the seed URL to
  refresh cookies if the run is expected to take more than 30 minutes.
