# Scraper Type: Authenticated Session

Use when the target data requires login, or when an API endpoint requires browser-set session
cookies that cannot be reproduced without a real browser visit.

**Decision criteria:**
- Login redirect when accessing target pages without a session
- API returns 401/403 without specific cookies that the browser sets via JS on first visit
- CSRF tokens required in POST requests
- Investigated via `scraper-types/ajax-api.md` but bare replay fails authentication

**Strategy:** Use Playwright to navigate naturally (letting JS set all session/fingerprint
cookies), then clone the full cookie jar into a `requests.Session`. Pay the browser cost once
at startup, then use `requests` for the high-volume scraping loop.

---

## Investigation Notes for This Type

During Phase 1, determine:
- **Login flow**: POST credentials to a form URL, or OAuth/SSO redirect?
- **CSRF token**: is there a hidden `_token` or `csrf` input in the login form?
- **Session lifetime**: how long does the session stay valid? Plan for re-auth if scraping > 1hr.
- **Minimal cookie set**: which cookies are actually required? Run the isolation sub-routine.
- **Success indicator**: how do you detect a successful login? (`/dashboard` in redirect URL,
  presence of a "logout" link, etc.)

---

## Template

```python
#!/usr/bin/env python3
# Site: [Site Name]
# Strategy: authenticated (Playwright bootstrap → requests session)
# Login URL: [URL]
# Target URL: [URL]
# Last recon: [YYYY-MM-DD]

import json
import logging
import os
import time
import random
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from playwright.sync_api import sync_playwright
from bot_scraper_lib import build_context, RateLimiter, bootstrap_session, make_record, write_record

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# --- Config ---
SEED_URL    = "https://example.com/"          # page that sets fingerprint/session cookies
LOGIN_URL   = "https://example.com/login"
TARGET_URL  = "https://example.com/parts"
DOMAIN      = urlparse(TARGET_URL).netloc
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
    "next_page":      'a[rel="next"]',
    "wait_for":       ".product-card",
}


def login_and_bootstrap() -> requests.Session:
    """Use Playwright to log in, then hand off to requests via bootstrap_session()."""
    email    = os.environ["SCRAPER_EMAIL"]
    password = os.environ["SCRAPER_PASSWORD"]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            viewport={"width": 1280, "height": 900},
        ).new_page()

        # Seed URL sets fingerprint/session cookies before login
        page.goto(LOGIN_URL, wait_until="networkidle")
        page.fill('input[name="email"], input[type="email"]', email)
        page.fill('input[name="password"], input[type="password"]', password)
        page.click('button[type="submit"], input[type="submit"]')
        page.wait_for_load_state("networkidle")

        if LOGIN_URL in page.url and "error" in page.content().lower():
            raise RuntimeError("Login failed — check credentials")
        logger.info(f"Login succeeded, landed at: {page.url}")

        # bootstrap_session transfers all cookies to a requests.Session
        session = bootstrap_session(page, page.url, headers=HEADERS)
        browser.close()

    return session


def fetch_page(url: str, session: requests.Session, ctx) -> str:
    entry = ctx.web_cache.get(url)
    if entry:
        logger.debug(f"Cache hit: {url}")
        return entry["content"]

    resp = session.get(url, timeout=30)
    if resp.status_code == 429:
        limiter.ban(resp.headers.get("Retry-After"))
    if resp.status_code in (401, 403):
        raise RuntimeError(f"Auth failure on {url} — session may have expired")
    resp.raise_for_status()
    ctx.web_cache.store(url, resp.text, ctx.client_name)
    return resp.text


def main():
    limiter.check()

    session = login_and_bootstrap()

    with build_context("my_scraper", with_images=False) as ctx:
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin

        url = TARGET_URL
        page_num = 1
        total = 0

        with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
            while url:
                logger.info(f"Scraping page {page_num}: {url}")
                html = fetch_page(url, session, ctx)
                soup = BeautifulSoup(html, "lxml")

                for card in soup.select(SELECTORS["item_container"]):
                    part_el  = card.select_one(SELECTORS["part_number"])
                    title_el = card.select_one(SELECTORS["title"])
                    price_el = card.select_one(SELECTORS["price"])

                    record = make_record(
                        DOMAIN,
                        url,
                        part_number=(part_el.get_text(strip=True) if part_el else "") or "",
                        title=title_el.get_text(strip=True) if title_el else None,
                        price=price_el.get("data-price") if price_el else None,
                    )
                    write_record(record, out)
                    total += 1

                logger.info(f"  → {total} records total")

                next_el = soup.select_one(SELECTORS["next_page"])
                url = urljoin(url, next_el["href"]) if next_el and next_el.get("href") else None
                page_num += 1
                if url:
                    limiter.wait()

    logger.info(f"Done. {total} records → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
```

---

## Minimal Cookie Isolation Sub-routine

If the bootstrapped session still gets 403s on certain API calls, find the minimal required
cookie set (at most N requests, not 2^N):

```python
def find_required_cookies(session: requests.Session, test_url: str) -> list[str]:
    """Returns the names of cookies required to get a 200 from test_url."""
    all_cookies = list(session.cookies.items())
    required = []

    for name, value in all_cookies:
        test_session = requests.Session()
        test_session.headers.update(HEADERS)
        for n, v in required + [(name, value)]:
            test_session.cookies.set(n, v)
        resp = test_session.get(test_url, timeout=10)
        if resp.status_code == 200:
            required.append((name, value))
        time.sleep(0.5)

    logger.info(f"Minimal cookie set: {[n for n, _ in required]}")
    return required
```

---

## Gotchas

- **Credentials in env vars only**: never hardcode credentials. Always use `os.environ`.
- **Session expiry**: if the scrape is long, check for 401/403 responses mid-run and call
  `bootstrap_session()` again to refresh before continuing.
- **CSRF in POST requests**: if the site uses CSRF tokens in forms, extract the token from
  the page before POSTing. See `references/templates.md` Template 4 for the pattern.
- **2FA**: if the account has two-factor authentication enabled, Playwright interactive login
  will hang waiting for the OTP. Disable 2FA on the scraper account or use a dedicated account.
