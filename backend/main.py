"""
main.py

FastAPI application entrypoint for the Intelligent Credit
Decision Support Platform.

Run with (from the project root):

    uvicorn backend.main:app --reload --port 8000

Then open http://localhost:8000/docs for interactive Swagger docs.

This wraps the existing Orchestrator
(rag/decision_intelligence/orchestrator.py) in a REST API so any
frontend — Streamlit, React, mobile, whatever — can talk to it
over HTTP instead of importing the Python classes directly.

The Orchestrator is expensive to construct (loads the LightGBM
model, label encoders, the full X_train.pkl, builds a SHAP
TreeExplainer, and sets up the LLM/retriever clients), so it is
built exactly once at startup and stored on app.state, not
per-request — see the lifespan handler below.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rag.decision_intelligence.orchestrator import Orchestrator

from backend.routers import (
    decision,
    general,
    health,
    knowledge,
    query,
    session,
    simulation,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info(
        "Loading Orchestrator (model, encoders, retrievers, LLM client)..."
    )

    try:
        app.state.orchestrator = Orchestrator()
    except Exception:
        logger.exception("Failed to initialize Orchestrator.")
        app.state.orchestrator = None
        raise

    logger.info("Orchestrator ready.")

    yield

    logger.info("Shutting down.")
    app.state.orchestrator = None


app = FastAPI(
    title="Intelligent Credit Decision Support Platform API",
    description="REST backend around the Decision Intelligence Orchestrator.",
    version="1.0.0",
    lifespan=lifespan,
)

# NOTE: "*" is fine for local development. Restrict this to your
# actual frontend origin(s) (e.g. ["http://localhost:8501"] for
# Streamlit, or your deployed React URL) before shipping this
# anywhere real.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(decision.router)
app.include_router(simulation.router)
app.include_router(knowledge.router)
app.include_router(general.router)
app.include_router(query.router)
app.include_router(session.router)


@app.get("/")
def root():
    return {
        "service": "Intelligent Credit Decision Support Platform API",
        "docs": "/docs",
        "endpoints": [
            "GET  /health",
            "POST /api/v1/decision",
            "POST /api/v1/simulate",
            "POST /api/v1/knowledge",
            "POST /api/v1/general",
            "POST /api/v1/query",
            "GET  /api/v1/session/{session_id}",
            "DELETE /api/v1/session/{session_id}",
        ],
    }