# Rate Limiting Doctrine

These rules are non-negotiable. This machine has no proxy or VPN during development.
A ban affects every scraper running from this IP.

---

## Request Delays

**HTML page fetches:** 1.0–2.5 seconds between requests.
```python
import time, random
time.sleep(random.uniform(1.0, 2.5))
```

**AJAX / JSON API endpoints:** 0.5–1.0 seconds between requests.
```python
time.sleep(random.uniform(0.5, 1.0))
```

Randomize the delay — fixed intervals are easier for bot-detection heuristics to flag.

---

## Sequential Only

Never fire requests in parallel batches. All scraping loops must be sequential:

- No `asyncio.gather()` over multiple URLs
- No `ThreadPoolExecutor` / `ProcessPoolExecutor` for fetches
- Playwright: one page at a time, not a pool

Parallelism saves maybe 30% wall time and risks a permanent ban. It is never worth it.

---

## 429 Handling — Permanent Backoff

A 429 means stop immediately. Do not auto-retry with a sleep. Write the ban to disk and raise
`SystemExit` so the scraper halts cleanly. Future runs check this file at startup.

```python
import json
from pathlib import Path
from datetime import datetime, timezone

BACKOFF_FILE = Path("backoff.json")

def load_backoff() -> dict:
    if BACKOFF_FILE.exists():
        return json.loads(BACKOFF_FILE.read_text())
    return {}

def check_backoff(domain: str) -> None:
    """Call at scraper startup. Aborts if this domain is in backoff state."""
    state = load_backoff()
    if domain in state:
        info = state[domain]
        raise SystemExit(
            f"[BACKOFF] {domain} was rate-limited at {info['banned_at']}. "
            f"Remove this entry from {BACKOFF_FILE} to resume."
        )

def record_ban(domain: str, retry_after: str | None = None) -> None:
    """Call when a 429 is received. Always raises SystemExit."""
    state = load_backoff()
    state[domain] = {
        "banned_at": datetime.now(timezone.utc).isoformat(),
        "retry_after": retry_after,
    }
    BACKOFF_FILE.write_text(json.dumps(state, indent=2))
    raise SystemExit(
        f"[BACKOFF] 429 received from {domain}. Written to {BACKOFF_FILE}. "
        f"Do not resume until manually cleared."
    )
```

### Usage in generated scrapers

```python
from urllib.parse import urlparse

DOMAIN = urlparse(BASE_URL).netloc  # e.g. "www.rockauto.com"

def main():
    check_backoff(DOMAIN)   # abort if previously banned
    # ... scraping loop ...

# In your fetch function:
try:
    resp = session.get(url, timeout=30)
    if resp.status_code == 429:
        retry_after = resp.headers.get("Retry-After")
        record_ban(DOMAIN, retry_after)  # raises SystemExit
    resp.raise_for_status()
except requests.HTTPError as e:
    if e.response.status_code == 429:
        record_ban(DOMAIN)
    raise
```

`backoff.json` is a local file in the scraper's working directory. To resume after a ban, delete
the relevant domain key from `backoff.json` (or delete the file entirely). There is no automatic
clearance — the intent is that a human decides when it is safe to resume.

---

## Retry Logic (non-429 errors)

For transient errors (500, timeout, connection reset), retry with exponential backoff. Do NOT
apply this to 429s — those go through `record_ban()` instead.

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.ConnectionError),
)
def fetch_with_retry(session, url):
    resp = session.get(url, timeout=30)
    if resp.status_code == 429:
        record_ban(urlparse(url).netloc)  # raises SystemExit — tenacity won't catch it
    resp.raise_for_status()
    return resp
```
