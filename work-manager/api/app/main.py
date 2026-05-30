from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .database import Base, SessionLocal, engine
from .embeddings import load_model
from .otel import setup_otel
from .routers import briefs, design_docs, epics, issues, notes, projects, runbooks, subtasks, tasks, tool_docs
from .services.scheduler import scheduler, start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    load_model()
    setup_otel(app)
    start_scheduler(SessionLocal)
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title="work-manager", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(epics.router)
app.include_router(tasks.router)
app.include_router(subtasks.router)
app.include_router(notes.router)
app.include_router(design_docs.router)
app.include_router(tool_docs.router)
app.include_router(issues.router)
app.include_router(runbooks.router)
app.include_router(briefs.router)


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
      <head><title>work-manager API</title></head>
      <body style='font-family: sans-serif; max-width: 900px; margin: 2rem auto;'>
        <h1>work-manager API</h1>
        <p>Agent work management service for projects, epics, tasks, notes, design docs, issues, and runbooks.</p>
        <ul>
          <li><a href='/docs'>/docs</a> — interactive OpenAPI documentation</li>
          <li><a href='/health'>/health</a> — health endpoint</li>
        </ul>
        <h2>Examples</h2>
        <pre>curl -X POST /projects -H 'Content-Type: application/json' -d '{"title":"My Project","goal":"Ship it"}'</pre>
        <pre>curl /tasks/next?project=PROJECT-001</pre>
        <pre>curl /briefs/task/TASK-001/markdown</pre>
      </body>
    </html>
    """


@app.get("/health")
def health():
    return {"status": "ok"}
