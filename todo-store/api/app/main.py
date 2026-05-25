import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .database import Base, engine
from .routers.todos import router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Todo Store",
    description="Shared todo capture and tracking for AI agents",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

INSTRUCTIONS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Todo Store — API Guide</title>
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

<h1>Todo Store</h1>
<p>Central todo capture for AI agents. Use it for bugs, follow-ups, and loose work items that
should survive past the current debugging or triage session.</p>

<h2>When to Use</h2>
<div class="tip">
  <strong>Use Todo Store</strong> for work items you intend to act on later.<br>
  <strong>Use Notes / Context Store</strong> for knowledge you want agents to remember or retrieve.
</div>

<h2>Defaults</h2>
<ul>
  <li>Status values: <code>open</code>, <code>in_progress</code>, <code>blocked</code>, <code>done</code></li>
  <li>Priority values: <code>low</code>, <code>medium</code>, <code>high</code>, <code>urgent</code></li>
  <li>Completion supports an optional <code>completion_description</code></li>
  <li>JSON is the canonical import/export format</li>
</ul>

<h2>Endpoints</h2>

<h3>Health check</h3>
<div class="ep"><span class="method get">GET</span><code>/health</code></div>

<h3>List todos</h3>
<div class="ep"><span class="method get">GET</span><code>/todos</code></div>
<p>Optional query params: <code>status</code>, <code>priority</code>, <code>tags</code>, <code>q</code>.</p>
<pre>GET /todos?status=open&amp;priority=high
GET /todos?tags=bug,triage&amp;q=inventory</pre>

<h3>Create a todo</h3>
<div class="ep"><span class="method post">POST</span><code>/todos</code></div>
<pre>curl -X POST http://localhost:8003/todos \\
  -H "Content-Type: application/json" \\
  -d '{"title": "Investigate flaky yard sync", "tags": "bug,triage",
       "description": "Saw it while debugging importer retries",
       "priority": "high", "status": "open"}'</pre>

<h3>Get one todo</h3>
<div class="ep"><span class="method get">GET</span><code>/todos/{id}</code></div>

<h3>Update a todo</h3>
<div class="ep"><span class="method put">PUT</span><code>/todos/{id}</code></div>

<h3>Complete a todo</h3>
<div class="ep"><span class="method patch">PATCH</span><code>/todos/{id}/complete</code></div>
<pre>curl -X PATCH http://localhost:8003/todos/42/complete \\
  -H "Content-Type: application/json" \\
  -d '{"completion_description": "Fixed while working on retry handling"}'</pre>

<h3>Delete a todo</h3>
<div class="ep"><span class="method del">DELETE</span><code>/todos/{id}</code></div>

<h3>Export todos</h3>
<div class="ep"><span class="method get">GET</span><code>/todos/export</code></div>

<h3>Import todos</h3>
<div class="ep"><span class="method post">POST</span><code>/todos/import</code></div>
<p>JSON import supports <code>merge</code> and <code>replace</code> modes.</p>

<h2>OpenAPI / Interactive Docs</h2>
<p><a href="/docs">Swagger UI — /docs</a> &nbsp;|&nbsp; <a href="/redoc">ReDoc — /redoc</a></p>

<footer>Todo Store &bull; SQLite + FastAPI + Alpine.js</footer>
</body>
</html>"""


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/instructions", response_class=HTMLResponse, include_in_schema=False)
async def instructions():
    return INSTRUCTIONS_HTML
