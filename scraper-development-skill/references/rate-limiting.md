# Rate Limiting Doctrine

All new scrapers should use **request-auth** as the primary rate-limiting mechanism.

The old local doctrine (`RateLimiter`, randomized sleeps, `backoff.json`, permanent local bans)
is obsolete for this skill. The goal is **centralized**, server-observed rate limiting so every
scraper in the cluster behaves consistently.

---

## Core rules

1. **Every target-site request needs a permit**
   - `requests.get(...)`
   - `requests.post(...)`
   - Playwright `page.goto(...)`
   - Playwright `page.evaluate(fetch(...))`
   - direct media downloads before storing in imgcache / vidcache / filecache

2. **Cache-service calls do not need permits**
   - `web_cache.get(...)`
   - `web_cache.store(...)`
   - `img_cache.lookup(...)`
   - `img_cache.store(...)`
   - `vid_cache.*`
   - `file_cache.*`

3. **Report the real response status back to request-auth**
   - call `permit.set_status(resp.status_code)` on success
   - let the context manager auto-release with status `0` on exceptions

4. **Do not create local rate-limit state**
   - no `backoff.json`
   - no per-scraper ban registry
   - no local 429 cooldown logic that competes with request-auth

5. **Stop the current run on repeated or terminal rate-limiting signals if appropriate**
   - but treat that as a scraper/runtime decision, not a second local rate-limiter
   - request-auth should remain the source of truth for global pacing/backoff

---

## Standard pattern

```python
from request_auth_client import RequestAuthClient

request_auth = RequestAuthClient(REQUEST_AUTH_SERVER_URL)

try:
    with request_auth.acquire(DOMAIN) as permit:
        resp = session.get(url, timeout=30)
        permit.set_status(resp.status_code)
        resp.raise_for_status()
finally:
    request_auth.close()
```

This is the preferred pattern because exceptions automatically release the permit with status `0`.

---

## Playwright pattern

```python
with request_auth.acquire(DOMAIN) as permit:
    response = page.goto(url, wait_until="networkidle", timeout=30_000)
    permit.set_status(response.status if response else 0)
```

Or for an intercepted browser fetch:

```python
with request_auth.acquire(DOMAIN) as permit:
    status_code, html = page.evaluate(
        """async (url) => {
            const r = await fetch(url, {headers: {"x-requested-with": "XMLHttpRequest"}});
            return [r.status, await r.text()];
        }""",
        url,
    )
    permit.set_status(status_code)
```

---

## 429 handling

When a scraper receives a 429:

- report `429` back through `permit.set_status(429)`
- surface the failure clearly in logs / the scraper result
- stop or abort the current run if continuing would be wasteful
- **do not** write a local ban file or invent a separate retry schedule

Example:

```python
with request_auth.acquire(DOMAIN) as permit:
    resp = session.get(url, timeout=30)
    permit.set_status(resp.status_code)
    if resp.status_code == 429:
        raise SystemExit(f"429 from {DOMAIN}; request-auth has been informed")
    resp.raise_for_status()
```

---

## Local sleeps

Do **not** add routine randomized sleeps as a substitute for request-auth.

Small waits may still be useful for:

- UI synchronization in Playwright
- deliberate pacing for browser interactions on fragile sites
- site-specific requirements the user explicitly wants

But for ordinary HTTP pacing, request-auth should be the default mechanism.
