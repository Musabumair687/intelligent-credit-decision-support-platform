"""
query.py

Single unified entrypoint: lets the Orchestrator's IntentRouter decide
whether an incoming message is a decision follow-up, a what-if
simulation, a bank-policy knowledge question, or general small talk,
and runs the matching pipeline automatically.

This is THE endpoint the post-prediction "Ask AI" chat calls for
every message. It does not require the caller to know which pipeline
handles the question — only a session_id from a prior prediction (for
follow-ups), or a fresh `applicant` (for a brand-new decision inside
the same call).

The response's "intent" field is what the frontend uses to display,
e.g., "Identified: Simulation question" before rendering the answer —
see backend.schemas.AIResponse.

Author
------
Intelligent Credit Decision Support Platform
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.dependencies import get_orchestrator
from backend.schemas import AIResponse, QueryRequest
from backend.serializers import build_ai_response, dump_model

router = APIRouter(prefix="/api/v1", tags=["query"])
logger = logging.getLogger("backend.query")


@router.post(
    "/query",
    response_model=AIResponse,
    response_model_exclude_none=True,
    summary="Ask anything — intent is detected automatically",
)
def run_query(
    payload: QueryRequest,
    debug: bool = Query(
        False, description="Include the full internal LLM prompt in the response."
    ),
    orchestrator=Depends(get_orchestrator),
):
    applicant = dump_model(payload.applicant) if payload.applicant else None
    started = time.perf_counter()

    try:
        result = orchestrator.process_request(
            user_question=payload.question,
            applicant=applicant,
            simulation_changes=payload.changes,
            session_id=payload.session_id,
        )

    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    except Exception as error:
        logger.exception("Query failed")
        raise HTTPException(status_code=500, detail=f"Query failed: {error}")

    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "session=%s intent=%s elapsed_ms=%.1f",
        payload.session_id, result.get("intent"), elapsed_ms,
    )

    return build_ai_response(result, elapsed_ms, payload.session_id, debug)