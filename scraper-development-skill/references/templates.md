# Web Scraper Code Templates

> **Note:** For full production templates with cache integration, rate limiting, and `make_record()`
> output, use the sub-skills in `references/scraper-types/`. The templates here are lightweight
> reference snippets for the common cross-cutting patterns.

---

## Context Setup (all scraper types)

```python
from bot_scraper_lib import build_context

# Core only (no image or video caching)
with build_context("my_scraper_name") as ctx:
    scrape(ctx)

# With image caching  (pip install "dwilson-bot-scraper-lib[images]")
with build_context("my_scraper_name", with_images=True) as ctx:
    scrape(ctx)

# With video caching  (pip install "dwilson-bot-scraper-lib[videos]")
with build_context("my_scraper_name", with_videos=True) as ctx:
    scrape(ctx)

# With both  (pip install "dwilson-bot-scraper-lib[images,videos]")
with build_context("my_scraper_name", with_images=True, with_videos=True) as ctx:
    scrape(ctx)
```

`client_name` is stored with every cache entry — use a stable, lowercase identifier per scraper.

---

## Cache-Check Pattern (mandatory before every fetch)

```python
# requests variant
def fetch_page(url: str, session, ctx) -> str:
    entry = ctx.web_cache.get(url)
    if entry:
        return entry["content"]
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    ctx.web_cache.store(url, resp.text, ctx.client_name)
    return resp.text

# Playwright variant
def fetch_page(url: str, page, ctx) -> str:
    entry = ctx.web_cache.get(url)
    if entry:
        return entry["content"]
    page.goto(url, wait_until="networkidle")
    html = page.content()
    ctx.web_cache.store(url, html, ctx.client_name)
    return html
```

---

## Incremental JSONL Save (mandatory)

Never accumulate records in memory and write at the end. Write and flush per record.

```python
from pathlib import Path
from datetime import datetime
import json

OUTPUT_FILE = Path(f"results_{datetime.now():%Y%m%d_%H%M%S}.jsonl")

with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
    for item in scrape_items():
        record = make_record("site_name", page_url, field1="...", field2="...")
        out.write(json.dumps(record.to_dict()) + "\n")
        out.flush()
```

JSONL (one JSON object per line) is preferred over a single JSON array — it supports streaming
reads and append without re-parsing the entire file.

---

## Image Caching Pattern

```python
def cache_image(image_url: str, ctx) -> str | None:
    if not ctx.img_cache or not image_url:
        return None
    meta = ctx.img_cache.lookup(image_url)
    if meta:
        return meta["content_hash"]
    try:
        import requests
        img_bytes = requests.get(image_url, timeout=15).content
        result = ctx.img_cache.store(image_url, img_bytes, ctx.client_name)
        return result["content_hash"]
    except Exception as e:
        logger.warning(f"Image cache failed for {image_url}: {e}")
        return None
```

---

## Video Caching Pattern

```python
def cache_video(video_url: str, ctx) -> str | None:
    if not ctx.vid_cache or not video_url:
        return None
    meta = ctx.vid_cache.lookup(video_url)
    if meta:
        return meta["content_hash"]
    try:
        import requests
        video_bytes = requests.get(video_url, timeout=60).content
        result = ctx.vid_cache.store(video_url, video_bytes, ctx.client_name)
        return result["content_hash"]
    except Exception as e:
        logger.warning(f"Video cache failed for {video_url}: {e}")
        return None
```

---

## 429 Backoff Pattern

```python
from pathlib import Path
from datetime import datetime, timezone
import json

BACKOFF_FILE = Path("backoff.json")

def check_backoff(domain: str) -> None:
    if BACKOFF_FILE.exists():
        state = json.loads(BACKOFF_FILE.read_text())
        if domain in state:
            raise SystemExit(f"[BACKOFF] {domain} banned at {state[domain]['banned_at']}. "
                             f"Remove from {BACKOFF_FILE} to resume.")

def record_ban(domain: str, retry_after=None) -> None:
    state = json.loads(BACKOFF_FILE.read_text()) if BACKOFF_FILE.exists() else {}
    state[domain] = {"banned_at": datetime.now(timezone.utc).isoformat(),
                     "retry_after": retry_after}
    BACKOFF_FILE.write_text(json.dumps(state, indent=2))
    raise SystemExit(f"[BACKOFF] 429 from {domain}. Cleared manually via {BACKOFF_FILE}.")
```

---

## Scraper Header Comment (required on every generated file)

```python
# Site: [Site Name]
# Strategy: [ajax-api | static-html | playwright-rendered | authenticated]
# Endpoint / Base URL: [URL]
# Last recon: [YYYY-MM-DD]
```

---

## Retry (transient errors only — not 429)

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.ConnectionError),
)
def fetch_with_retry(session, url):
    resp = session.get(url, timeout=30)
    if resp.status_code == 429:
        record_ban(urlparse(url).netloc)   # raises SystemExit — tenacity won't catch it
    resp.raise_for_status()
    return resp
```

---

## make_record / write_record Reference

```python
from bot_scraper_lib import make_record, write_record

record = make_record(
    "rockauto",                               # site — required
    "https://...",                            # source_url — required
    title="Brake Pad Set",
    sku="12345",
    price="29.99",
    availability="In Stock",
    image_content_hash="abc123...",           # from imgcache.store()  (requires with_images=True)
    video_content_hash="def456...",           # from vidcache.store()  (requires with_videos=True)
    # add any fields the site provides
)

write_record(record, out_file)  # writes JSONL line and flushes
```
