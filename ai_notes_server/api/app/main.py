import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .database import Base, engine
from .routers.notes import router
from . import embeddings

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    embeddings.load_model()
    yield


app = FastAPI(
    title="AI Notes Server",
    description="Lightweight knowledge persistence for AI agents",
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
<title>AI Notes Server — API Guide</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f9fafb; color: #111827;
         max-width: 860px; margin: 0 auto; padding: 2rem 1.5rem; line-height: 1.6; }
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
  .get  { background: #dbeafe; color: #1d4ed8; }
  .post { background: #d1fae5; color: #065f46; }
  .put  { background: #fef3c7; color: #92400e; }
  .del  { background: #fee2e2; color: #991b1b; }
  .ep   { margin: .75rem 0; padding: .75rem; background: #fff;
          border: 1px solid #e5e7eb; border-radius: 6px; }
  .ep code { font-size: .9rem; }
  ul { padding-left: 1.4rem; margin-bottom: .75rem; }
  li { margin-bottom: .25rem; }
  .tip { background: #eff6ff; border-left: 3px solid #3b82f6;
         padding: .6rem 1rem; margin: .5rem 0; border-radius: 0 4px 4px 0; }
  footer { margin-top: 3rem; font-size: .85rem; color: #9ca3af; }
</style>
</head>
<body>

<h1>AI Notes Server</h1>
<p>Lightweight knowledge persistence for AI agents. Store minimal, high-value notes that help future sessions avoid re-discovering known patterns and solutions.</p>

<h2>Purpose</h2>
<div class="tip">Before starting a task — search for relevant notes.<br>
After completing a task — save key findings as a note.</div>
<p>Notes are minimal prose: facts, gotchas, patterns. Not prescriptive strategy — just learnings that save time in future sessions.</p>

<h2>Note Structure</h2>
<pre>{
  "title":   "Short, descriptive title",
  "tags":    ["technology", "pattern", "site-name"],
  "content": "Minimal prose. Key facts. What worked. What didn't."
}</pre>

<h2>Endpoints</h2>

<h3>Create a note</h3>
<div class="ep"><span class="method post">POST</span><code>/notes</code></div>
<pre>curl -X POST http://localhost:8000/notes \\
  -H "Content-Type: application/json" \\
  -d '{"title": "WordPress AJAX pattern", "tags": ["wordpress","scraping"], "content": "..."}'</pre>

<h3>List notes (text search)</h3>
<div class="ep"><span class="method get">GET</span><code>/notes</code></div>
<p>Params: <code>q</code> (text search), <code>tags</code> (comma-separated, OR logic),
<code>archived</code> (default false), <code>limit</code> (default 50), <code>offset</code></p>
<pre>GET /notes?q=cloudflare
GET /notes?tags=scraping,wordpress
GET /notes?q=inventory&tags=wordpress&archived=false</pre>

<h3>Semantic search (meaning-based)</h3>
<div class="ep"><span class="method get">GET</span><code>/notes/search</code></div>
<p>Params: <code>q</code> (required), <code>tags</code>, <code>archived</code>, <code>limit</code> (default 10)</p>
<pre>GET /notes/search?q=how+to+bypass+cloudflare+protection&limit=5</pre>
<p>Returns: <code>[{"note": {...}, "score": 0.87}, ...]</code> — sorted by similarity.</p>

<h3>Get a note</h3>
<div class="ep"><span class="method get">GET</span><code>/notes/{id}</code></div>

<h3>Update a note</h3>
<div class="ep"><span class="method put">PUT</span><code>/notes/{id}</code></div>
<p>All fields optional — only include what's changing.</p>
<pre>curl -X PUT http://localhost:8000/notes/42 \\
  -H "Content-Type: application/json" \\
  -d '{"content": "Updated findings..."}'</pre>

<h3>Delete a note</h3>
<div class="ep"><span class="method del">DELETE</span><code>/notes/{id}</code></div>

<h3>Archive / unarchive a note</h3>
<div class="ep"><span class="method post">POST</span><code>/notes/{id}/archive</code></div>
<p>Toggle — calling again unarchives. Archived notes are excluded from default list/search.</p>

<h3>Export all notes</h3>
<div class="ep"><span class="method get">GET</span><code>/export</code></div>
<p>Returns a JSON array of all notes (including archived) as a downloadable file.</p>

<h3>Import notes</h3>
<div class="ep"><span class="method post">POST</span><code>/import</code></div>
<p>Body: JSON array. Appends to existing notes. Extra fields (e.g. <code>created_at</code>) are ignored.</p>
<pre>POST /import
[{"title": "...", "tags": ["..."], "content": "..."}, ...]</pre>

<h2>Agent Usage Tips</h2>
<ul>
  <li>Keep content under 400 words — one focused learning per note</li>
  <li>Use specific tags: technology, platform, site name, pattern type</li>
  <li>Prefer updating an existing note over creating a near-duplicate</li>
  <li>Semantic search works best for conceptual queries; text search for exact terms</li>
  <li>Archive notes that are outdated rather than deleting them</li>
</ul>

<h2>OpenAPI / Interactive Docs</h2>
<p><a href="/docs">Swagger UI — /docs</a> &nbsp;|&nbsp; <a href="/redoc">ReDoc — /redoc</a></p>

<footer>AI Notes Server &bull; SQLite + FastAPI + fastembed (BAAI/bge-small-en-v1.5)</footer>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/instructions", response_class=HTMLResponse, include_in_schema=False)
async def instructions():
    return INSTRUCTIONS_HTML
