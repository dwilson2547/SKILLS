# Cache Integration

All scrapers must route page fetches through the webcache and image downloads through the imgcache.
Never fetch a URL without checking the cache first.

## Setup

```bash
pip install dwilson-bot-scraper-lib                        # core (webcache only)
pip install "dwilson-bot-scraper-lib[images]"              # + image caching
pip install "dwilson-bot-scraper-lib[videos]"              # + video caching
pip install "dwilson-bot-scraper-lib[images,videos]"       # + both
pip install "dwilson-bot-scraper-lib[playwright]"          # + Playwright bootstrap
```

`imgcache_client` and `vidcache_client` are optional extras. The library imports them lazily
and raises a clear `ImportError` with the correct `pip install` command if they are missing
and `with_images=True` / `with_videos=True` is requested.

## Scraper Context

Use `build_context()` from `bot_scraper_lib` to wire up both clients at once:

```python
from bot_scraper_lib import build_context

# Images only
with build_context("rockauto_parts", with_images=True) as ctx:
    # ctx.web_cache  → WebCacheClient
    # ctx.img_cache  → ImgCacheClient
    # ctx.vid_cache  → None
    scrape(ctx)

# Videos only
with build_context("youtube_archive", with_videos=True) as ctx:
    # ctx.web_cache  → WebCacheClient
    # ctx.img_cache  → None
    # ctx.vid_cache  → VidCacheClient
    scrape(ctx)

# Both
with build_context("media_site", with_images=True, with_videos=True) as ctx:
    scrape(ctx)
```

`client_name` must be a stable lowercase identifier for the scraper (e.g. `"rockauto_parts"`).
It is stored with every cache entry for attribution and debugging.

**Environment variables** (override defaults; or use a TOML file via `SCRAPER_CONFIG`):
- `WEBCACHE_URL` — default `http://localhost:8000`
- `IMGCACHE_URL` — default `http://localhost:8010`
- `VIDCACHE_URL` — default `http://localhost:8020`

**TOML config** (set `SCRAPER_CONFIG=/path/to/config.toml`):
```toml
[webcache]
url = "http://localhost:8000"

[imgcache]
url = "http://localhost:8010"

[vidcache]
url = "http://localhost:8020"
```

---

## WebCache — Page Content

### Mandatory check-before-fetch pattern

```python
def fetch_page(url: str, session, ctx) -> str:
    """Fetch a page, using the cache if available."""
    entry = ctx.web_cache.get(url)
    if entry:
        return entry["content"]
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    ctx.web_cache.store(url, resp.text, ctx.client_name)
    return resp.text
```

### Playwright variant

```python
async def fetch_page(url: str, page, ctx) -> str:
    entry = ctx.web_cache.get(url)
    if entry:
        return entry["content"]
    await page.goto(url, wait_until="networkidle")
    html = await page.content()   # rendered HTML, post-JS
    ctx.web_cache.store(url, html, ctx.client_name)
    return html
```

### Client API reference

| Method | Returns | Notes |
|--------|---------|-------|
| `ctx.web_cache.get(url)` | `dict` or `None` | `dict["content"]` is the full HTML string |
| `ctx.web_cache.store(url, html, client_name)` | metadata dict | 201 = new, 200 = duplicate |
| `ctx.web_cache.search(url_contains)` | list of metadata dicts | No content in results |
| `ctx.web_cache.get_by_hash(hash)` | `dict` or `None` | Retrieve by content hash |

Store **rendered HTML** (post-JS), not raw response bytes. For `requests`-based scrapers where
the content is static, `resp.text` is fine.

---

## ImgCache — Product Images

Only needed when the scraper collects product images. Pass `with_images=True` to `build_context()`.

```python
def cache_image(image_url: str, ctx) -> str:
    """Download and cache an image. Returns content_hash."""
    meta = ctx.img_cache.lookup(image_url)
    if meta:
        return meta["content_hash"]
    img_bytes = requests.get(image_url, timeout=30).content
    result = ctx.img_cache.store(image_url, img_bytes, ctx.client_name)
    return result["content_hash"]
```

Store the returned `content_hash` in the record (e.g. as `image_content_hash`). Do not store the
image URL as a durable reference — URLs break; the hash does not.

### Client API reference

| Method | Returns | Notes |
|--------|---------|-------|
| `ctx.img_cache.lookup(url)` | `dict` or `None` | Checks by source URL |
| `ctx.img_cache.store(url, bytes, client_name)` | metadata dict | Returns `content_hash` |
| `ctx.img_cache.get_bytes(content_hash)` | `bytes` | Retrieve raw image |
| `ctx.img_cache.similar(phash, max_hamming)` | list | Perceptual duplicate search |

The imgcache performs perceptual deduplication — identical or near-identical images from different
URLs will map to the same `content_hash`.

---

## VidCache — Video Files

Only needed when the scraper collects video files. Pass `with_videos=True` to `build_context()`.
Requires `pip install "dwilson-bot-scraper-lib[videos]"`.

```python
def cache_video(video_url: str, ctx) -> str:
    """Download and cache a video. Returns content_hash."""
    meta = ctx.vid_cache.lookup(video_url)
    if meta:
        return meta["content_hash"]
    video_bytes = requests.get(video_url, timeout=60).content
    result = ctx.vid_cache.store(video_url, video_bytes, ctx.client_name)
    return result["content_hash"]
```

Store the returned `content_hash` in the record (e.g. as `video_content_hash`). Do not store
the video URL as a durable reference — URLs break; the hash does not.

### Client API reference

| Method | Returns | Notes |
|--------|---------|-------|
| `ctx.vid_cache.lookup(url)` | `dict` or `None` | Checks by source URL |
| `ctx.vid_cache.store(url, bytes, client_name)` | metadata dict | Returns `content_hash` |
| `ctx.vid_cache.get_bytes(content_hash)` | `bytes` | Retrieve raw video |

Use a longer `timeout` for video downloads — large files can take several seconds. Apply the
same rate-limiting rules as image downloads: one at a time, no parallel fetches.
