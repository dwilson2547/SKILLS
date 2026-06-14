import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .database import Base, engine
from .routers.sources import router as sources_router
from .routers.docs import router as docs_router
from . import embeddings, scheduler

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    embeddings.load_model()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="AI Tool Docs Server",
    description="Local documentation index — query GitHub-sourced docs with semantic search",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/swagger",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources_router)
app.include_router(docs_router)


# ── Instructions page ─────────────────────────────────────────────────────────

INSTRUCTIONS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Tool Docs Server — API Guide</title>
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

<h1>AI Tool Docs Server</h1>
<p>Local documentation index for AI agents. Pull markdown docs from GitHub repositories,
index them with semantic search, and query them without leaving your context window.</p>

<h2>Quick Start (CLI)</h2>
<pre>docs search "how to configure authentication"
docs sources
docs add "mylib" --repo owner/repo --folders docs
docs sync 1</pre>

<h2>Sources API</h2>

<div class="ep"><span class="method get">GET</span><code>/sources</code>
— List all configured doc sources with section counts and sync status.</div>

<div class="ep"><span class="method post">POST</span><code>/sources</code>
— Add a new source.
<pre>{ "name": "mylib", "repo": "owner/repo", "branch": "main",
  "docs_folders": ["docs", "guides"], "file_glob": "*.md" }</pre></div>

<div class="ep"><span class="method get">GET</span><code>/sources/{id}</code>
— Get a single source by ID.</div>

<div class="ep"><span class="method put">PUT</span><code>/sources/{id}</code>
— Update source config. Changing <code>repo</code>, <code>branch</code>, <code>docs_folders</code>,
or <code>file_glob</code> resets the commit SHA so the next sync re-indexes everything.</div>

<div class="ep"><span class="method del">DELETE</span><code>/sources/{id}</code>
— Delete a source and all its indexed sections.</div>

<div class="ep"><span class="method post">POST</span><code>/sources/{id}/sync</code>
— Trigger an immediate sync in the background. Returns <code>202</code> immediately.</div>

<div class="ep"><span class="method get">GET</span><code>/sources/{id}/files</code>
— List all indexed file paths for a source.</div>

<h2>Docs API</h2>

<div class="ep"><span class="method get">GET</span><code>/docs/search?q=…&amp;source_id=…&amp;limit=10</code>
— Semantic search across all indexed doc sections (or filter by <code>source_id</code>).
Returns sections ranked by cosine similarity.</div>

<div class="ep"><span class="method get">GET</span><code>/docs?source_id=…&amp;file_path=…</code>
— List doc sections. Filter by source or specific file.</div>

<div class="ep"><span class="method get">GET</span><code>/docs/{id}</code>
— Get a single doc section by ID.</div>

<div class="ep"><span class="method get">GET</span><code>/stats</code>
— Return aggregate counts: sources, sections, indexed files.</div>

<h2>Sync Behaviour</h2>
<ul>
  <li>On <code>POST /sources/{id}/sync</code> the API fetches the latest commit SHA from GitHub.</li>
  <li>If the SHA matches the stored SHA, the sync is a no-op (nothing changed).</li>
  <li>Changed or new files are re-indexed section-by-section. Removed files are purged.</li>
  <li>A background scheduler re-checks all sources every <strong>24 hours</strong>.</li>
</ul>
<div class="tip">Set <code>GITHUB_TOKEN</code> env var to raise the GitHub API rate limit
from 60 to 5,000 req/hr and access private repos.</div>

<h2>Agent Workflow</h2>
<pre>docs search "query"                    # semantic search — start here
docs sources                           # see what's indexed
docs sync &lt;id&gt;                         # force re-index if docs were updated</pre>

<footer>AI Tool Docs Server · <a href="/docs">Swagger UI</a> · <a href="/redoc">ReDoc</a></footer>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def instructions():
    return INSTRUCTIONS_HTML
