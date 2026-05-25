---
name: web-scraper
description: >
  Build production-quality web scrapers by first using Playwright MCP to investigate a target site's
  structure, then selecting the right extraction strategy, then generating robust scraper code.
  Use this skill whenever the user wants to extract structured data from a website, scrape a URL,
  pull data from web pages, automate data collection from the web, or asks how to get data out of
  a site. Trigger even if the user just asks "how do I scrape X" or "can you get me the data from
  this page" — the investigation phase is always the right starting point, even for seemingly simple sites.
  This skill requires the Playwright MCP to be connected.

  Generated scrapers must: (1) use scrape-stack clients by default, (2) check the webcache before
  every target-site fetch, (3) route media through the scrape-stack cache layers, and (4) use
  request_auth_client permits around target-site requests so central rate limiting is observed.
  Cache-service calls stay outside permits, and scrapers should not implement competing local
  backoff logic. See references/ for the full doctrine on each.
---

# Web Scraper Development Skill

This skill guides a structured three-phase workflow: **investigate → strategize → implement**. The
investigation phase using Playwright MCP is non-negotiable — skipping it leads to brittle scrapers
that break on the first edge case.

---

## Non-negotiable Rules

These apply to every scraper regardless of type. Read `references/cache-integration.md` and
`references/rate-limiting.md` for full implementation details.

| Rule | Short form |
|------|-----------|
| **Scrape-stack first** | Default to `dwilson-cache-client` + `dwilson-request-auth-client`, not `bot_scraper_lib`. |
| **Cache before fetch** | Always call `WebCacheClient.get(url, max_age=...)` before any target-site request. Store on miss. |
| **Cache images** | Route image ingestion through `ImgCacheClient`; fetch source bytes under a request-auth permit. |
| **Cache videos/files** | Route larger media through `VidCacheClient` / `FileCacheClient` when needed. |
| **Request authorization** | Wrap target-site requests in `with request_auth.acquire(DOMAIN) as permit:` and report the real status code. |
| **Permit scope** | Request-auth wraps target-site requests only — not webcache/imgcache/vidcache/filecache calls. |
| **No local backoff layer** | Do not create `backoff.json` or a second rate-limiter that competes with request-auth. |
| **Incremental saves** | Write and flush each record as scraped. Never batch-write at the end. |

---

## Phase 1: Site Investigation with Playwright MCP

Before writing a single line of scraper code, use Playwright MCP to thoroughly understand the site.
**Playwright is always the starting point** — the question is whether you can simplify down to
`requests` after capturing a working browser request, not whether you need Playwright at all.

The goal is to answer five key questions:

1. What request loads the target data, and what does it look like exactly?
2. Can that request be replayed with `requests` using the captured headers/cookies?
3. What selectors reliably identify the target data?
4. How does pagination or infinite scroll work?
5. Are there auth, rate-limiting, or bot-detection mechanisms?

### Investigation Checklist

#### 1. Initial Navigation & Visual Inspection
```
playwright_navigate → {base_url}/robots.txt   (check Disallow rules first)
playwright_navigate → target URL
playwright_screenshot → capture the page state
playwright_get_visible_html → get the rendered DOM
```

Check `robots.txt` before anything else. If the target path is `Disallow`-ed, flag it to the user.

#### 2. Capture the Working Request via Network Interception

Don't guess whether `requests` will work — let the browser make the request first, then copy
it exactly. Set up interception **before** navigating so you catch the data request as it fires:

```javascript
// In playwright_evaluate — run this before the action that loads data
window.__captured = [];
const origOpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(method, url) {
  window.__captured.push({type: 'xhr', method, url});
  return origOpen.apply(this, arguments);
};
const origFetch = window.fetch;
window.fetch = function(url, opts) {
  window.__captured.push({type: 'fetch', url: url?.toString(), method: opts?.method || 'GET'});
  return origFetch.apply(this, arguments);
};
```

Then trigger the action that loads data (scroll, click pagination, submit search), and inspect:

```javascript
window.__captured
```

Also use the Playwright MCP network tab or `playwright_network_requests` if available — it gives
the full request including headers and response body without the JS monkey-patch.

Once you have the data request URL, extract the **complete** headers and cookies from the browser.

#### 3. Attempt requests Replay with Captured Headers

Take the exact URL, headers, and cookies captured in step 2 and replay with `requests`.

- **If replay returns the expected data** → use `requests` for the scraping loop (see Phase 2)
- **If replay returns 401/403** → run the cookie isolation sub-routine, then try again
- **If replay works with 0 cookies** → the endpoint is public; no session needed

#### 4. Cookie Isolation Sub-routine

When a replay fails authentication, binary-search for the minimal required cookie set.

#### 5. Selector Discovery

Prefer selectors in this stability order: `[data-testid]` > semantic tags > stable class names >
ID-based > structural (`div:nth-child(3)`). Avoid hashed CSS classes (`sc-abc123`) — they change
on every deploy.

#### 6. Pagination Analysis

Click through pagination and observe:

- URL changes (`?page=2`) → simple loop, no browser needed
- No URL change, new content loads → infinite scroll or AJAX pagination
- Hidden "next" button → Playwright click-based pagination

#### 7. Auth & Bot Detection Signals

Watch for:

- Login redirects → need cookie/session bootstrapping via Playwright
- CAPTCHAs → delays, stealth headers, or bypass service
- `403` / `429` → auth / rate-limit / bot block; see `references/rate-limiting.md`
- Cloudflare challenge pages → `playwright-stealth` or Camoufox

---

## Phase 2: Strategy Selection

Playwright is the default. The only reason to use `requests` is if the replay test in Phase 1
step 3 succeeded. Do not attempt `requests` without a confirmed working replay first.

| Phase 1 result | Strategy | Sub-skill |
|----------------|----------|-----------|
| Default (no confirmed replay) | Playwright | `scraper-types/playwright-rendered.md` |
| Replay succeeded — JSON API endpoint | `requests` + JSON | `scraper-types/ajax-api.md` |
| Replay succeeded — static HTML | `requests` + BS4 | `scraper-types/static-html.md` |
| Login required | Playwright bootstrap → `requests.Session` | `scraper-types/authenticated.md` |
| Cloudflare / heavy bot detection | Playwright + `playwright-stealth` | `scraper-types/playwright-rendered.md` |

Document your strategy decision with reasoning before generating code.

**Framework preference order:**
1. Playwright — always start here; it is the known-working baseline
2. `requests` + JSON — only if Phase 1 replay confirmed it works with captured headers
3. `requests` + BS4 — only if Phase 1 replay confirmed static HTML works
4. Selenium — legacy/fallback only, not worth building against

---

## Phase 3: Scraper Implementation

Read the appropriate sub-skill from `references/scraper-types/` based on Phase 2 selection.
Each sub-skill contains a complete, ready-to-adapt template that already integrates scrape-stack
cache clients and request-auth.

All generated scrapers share these structural requirements:

### Scraper Header (required)
```python
# Site: [Site Name]
# Strategy: [ajax-api | static-html | playwright-rendered | authenticated]
# Discovered endpoint / base URL: [URL]
# Last recon: [YYYY-MM-DD]
# Selectors / fields: see SELECTORS dict below
```

### SELECTORS Block (required)
Separate all selectors from logic. When a scraper breaks due to site redesign, only this
block needs updating.

### Client setup (required)
Generated scrapers should explicitly initialize scrape-stack clients:

```python
from cache_client import ImgCacheClient, WebCacheClient
from request_auth_client import RequestAuthClient

with WebCacheClient(WEBCACHE_URL) as web_cache, ImgCacheClient(IMGCACHE_URL) as img_cache:
    request_auth = RequestAuthClient(REQUEST_AUTH_SERVER_URL)
    try:
        scrape(web_cache=web_cache, img_cache=img_cache, request_auth=request_auth)
    finally:
        request_auth.close()
```

### Output Schema
Use plain dictionaries and write incrementally to JSONL (or the project's persistent store if the
scraper is being integrated into an existing ingestion pipeline):

```python
record = {
    "site": "example_site",
    "source_url": page_url,
    "scraped_at": datetime.utcnow().isoformat(),
    "title": "Widget",
    "price": "9.99",
    "sku": "W-123",
}
```

### Error Self-Classification
On exit, log the failure mode rather than just crashing:

| Error type | Cause | Repair action |
|------------|-------|---------------|
| Empty results, no HTTP error | Selector drift | Recon → selector patch |
| 403 / 429 | Auth / rate-limit / bot block | See rate-limiting.md and verify permit usage |
| CAPTCHA page | Bot detection | Stealth headers, delay increase |
| Schema mismatch | Output fields missing | Recon → field map update |
| Timeout | JS change / site slowdown | Wait condition update |

---

## Output Format

After completing all three phases, deliver:

1. **Investigation Summary** — answers to the 7 checklist items above, with selector output
   as evidence
2. **Strategy Decision** — which sub-skill and why, with trade-offs noted
3. **Complete Scraper Code** — runnable, using scrape-stack cache clients and request-auth by default
4. **Usage Instructions** — how to run it, output file produced, parameters to adjust

---

## Ethical & Legal Reminders

- Always check `robots.txt` first
- Don't scrape personal data without understanding GDPR/CCPA applicability
- Terms of Service may prohibit scraping — flag to user if ToS is restrictive
- Prefer official APIs over scraping when they exist
