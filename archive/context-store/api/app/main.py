import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .database import Base, engine
from .routers.documents import router
from . import embeddings

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    embeddings.load_model()
    yield


app = FastAPI(
    title="Context Store",
    description="Structured reference documents for AI agents",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# ── Instructions page ─────────────────────────────────────────────────────────

INSTRUCTIONS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Context Store — API Guide</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f9fafb; color: #111827;
         max-width: 900px; margin: 0 auto; padding: 2rem 1.5rem; line-height: 1.6; }
  h1 { font-size: 1.75rem; margin-bottom: .25rem; }
  h2 { font-size: 1.2rem; margin: 2rem 0 .75rem; padding-bottom: .35rem;
       border-bottom: 1px solid #e5e7eb; }
  h3 { font-size: 1rem; margin: 1.25rem 0 .4rem; color: #374151; }
  p  { margin-bottom: .75rem; }
  pre { background: #1e293b; color: #e2e8f0; padding: 1rem; border-radius: 6px;
        overflow-x: auto; font-size: .85rem; margin: .5rem 0 1rem; }
  code { background: #f1f5f9; padding: 1px 5px; border-radius: 3px;
         font-family: 'Courier New', monospace; font-size: .9em; color: #0f172a; }
  .method { display: inline-block; padding: 2px 8px; border-radius: 4px;
            font-weight: 700; font-size: .8rem; margin-right: .4rem; }
  .get    { background: #dbeafe; color: #1d4ed8; }
  .post   { background: #d1fae5; color: #065f46; }
  .put    { background: #fef3c7; color: #92400e; }
  .patch  { background: #ede9fe; color: #5b21b6; }
  .del    { background: #fee2e2; color: #991b1b; }
  .ep     { margin: .75rem 0; padding: .75rem; background: #fff;
            border: 1px solid #e5e7eb; border-radius: 6px; }
  .ep code { font-size: .9rem; }
  ul { padding-left: 1.4rem; margin-bottom: .75rem; }
  li { margin-bottom: .25rem; }
  .tip { background: #eff6ff; border-left: 3px solid #3b82f6;
         padding: .6rem 1rem; margin: .5rem 0; border-radius: 0 4px 4px 0; }
  .warn { background: #fffbeb; border-left: 3px solid #f59e0b;
          padding: .6rem 1rem; margin: .5rem 0; border-radius: 0 4px 4px 0; }
  footer { margin-top: 3rem; font-size: .85rem; color: #9ca3af; }
</style>
</head>
<body>

<h1>Context Store</h1>
<p>Structured reference documents for AI agents. Where notes are minimal one-off facts,
context documents are multi-section documents — plans, strategies, procedures — that agents author
once and retrieve selectively across sessions.</p>

<h2>Notes vs Context docs</h2>
<div class="tip">
  <strong>Notes</strong> — what agents have learned (minimal, lookup-optimised, one fact per note)<br>
  <strong>Context docs</strong> — reference material agents consult (structured, section-retrievable, multi-step)
</div>
<p>If it needs headers, it's a context document. Keep notes as the single entry point — save a pointer
note after ingesting a context doc: <em>"auth strategy documented — see context slug: junkyard-scraper/auth"</em></p>

<h2>Agent Workflow</h2>
<div class="warn"><strong>Before ingesting:</strong> run <code>GET /slugs</code> to check what already exists.
If a related document exists, consider whether this extends it or replaces it (<code>supersedes</code>).</div>
<div class="tip"><strong>Retrieval order:</strong> check notes for slug pointer → <code>POST /context/search</code>
to find sections → <code>/toc</code> to review structure → pull only the section(s) needed.</div>

<h2>Slug Rules</h2>
<ul>
  <li>Lowercase, hyphen-separated words — e.g. <code>junkyard-scraper/auth</code></li>
  <li><code>/</code> as hierarchy separator, max 4 levels</li>
  <li>No spaces, no special characters beyond <code>-</code> and <code>/</code></li>
</ul>

<h2>Endpoints</h2>

<h3>Check existing slugs</h3>
<div class="ep"><span class="method get">GET</span><code>/slugs</code></div>
<p>Params: <code>scope</code> (slug prefix), <code>status</code> (default: all). Returns string array.</p>
<pre>GET /slugs
GET /slugs?scope=junkyard-scraper</pre>

<h3>List documents</h3>
<div class="ep"><span class="method get">GET</span><code>/context</code></div>
<p>Params: <code>tags</code> (comma-separated AND), <code>scope</code> (slug prefix), <code>status</code> (active/stale/all, default: active), <code>session_id</code></p>
<pre>GET /context?scope=junkyard-scraper&amp;status=active</pre>

<h3>Ingest a document</h3>
<div class="ep"><span class="method post">POST</span><code>/context</code></div>
<p>Returns <code>409</code> if slug exists — use PUT to update. If <code>supersedes</code> is set, the referenced document is marked stale.</p>
<pre>curl -X POST http://localhost:8001/context \\
  -H "Content-Type: application/json" \\
  -d '{"slug": "junkyard-scraper/auth", "title": "Auth Strategy",
       "content": "# Auth Strategy\\n\\n## Overview\\n...",
       "tags": "scraper,auth,junkyard", "supersedes": null}'</pre>

<h3>Semantic search</h3>
<div class="ep"><span class="method post">POST</span><code>/context/search</code></div>
<p>Searches section embeddings. Returns sections with parent document context.</p>
<pre>curl -X POST http://localhost:8001/context/search \\
  -H "Content-Type: application/json" \\
  -d '{"query": "OAuth token refresh", "scope": "junkyard-scraper", "limit": 5}'</pre>

<h3>Get table of contents</h3>
<div class="ep"><span class="method get">GET</span><code>/context/{slug}/toc</code></div>
<p>Returns section map without content. Use this before deciding which section to retrieve.</p>
<pre>GET /context/junkyard-scraper/auth/toc</pre>

<h3>Get a section</h3>
<div class="ep"><span class="method get">GET</span><code>/context/{slug}/sections/{heading_slug}</code></div>
<p>Returns content of a single section. <code>heading_slug</code> is the URL-safe heading (from TOC).</p>
<pre>GET /context/junkyard-scraper/auth/sections/oauth-flow</pre>

<h3>Get full document</h3>
<div class="ep"><span class="method get">GET</span><code>/context/{slug}</code></div>
<p>Returns full content. Use sparingly — prefer section retrieval to save tokens.</p>

<h3>Update document</h3>
<div class="ep"><span class="method put">PUT</span><code>/context/{slug}</code></div>
<p>Replaces content and re-parses all sections. Only include fields to change.</p>

<h3>Set status</h3>
<div class="ep"><span class="method patch">PATCH</span><code>/context/{slug}/status</code></div>
<pre>curl -X PATCH http://localhost:8001/context/junkyard-scraper/auth/status \\
  -H "Content-Type: application/json" \\
  -d '{"status": "stale"}'</pre>

<h3>Children</h3>
<div class="ep"><span class="method get">GET</span><code>/context/{slug}/children</code></div>
<p>Returns immediate child documents in the slug hierarchy.</p>
<pre>GET /context/junkyard-scraper/children
# returns: junkyard-scraper/auth, junkyard-scraper/sites  (not junkyard-scraper/sites/lkq)</pre>

<h3>Delete document</h3>
<div class="ep"><span class="method del">DELETE</span><code>/context/{slug}</code></div>
<p>Hard delete. Prefer <code>PATCH /status</code> with <code>stale</code> for soft deprecation.</p>

<h2>OpenAPI / Interactive Docs</h2>
<p><a href="/docs">Swagger UI — /docs</a> &nbsp;|&nbsp; <a href="/redoc">ReDoc — /redoc</a></p>

<footer>Context Store &bull; SQLite + FastAPI + fastembed (BAAI/bge-small-en-v1.5)</footer>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/instructions", response_class=HTMLResponse, include_in_schema=False)
async def instructions():
    return INSTRUCTIONS_HTML
