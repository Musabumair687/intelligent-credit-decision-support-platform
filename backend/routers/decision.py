"""
decision.py

Runs the full ML prediction + evidence retrieval + LLM explanation
pipeline for a fresh applicant, OR — if `applicant` is omitted —
answers a follow-up question about the applicant already on file for
the given session_id, with no re-prediction and no model call.

Fix applied in this version
----------------------------
Previously this route called orchestrator.explain() directly, which
meant two things: (1) it required a full applicant every time, so it
could never be used for a lightweight follow-up, and (2) it bypassed
Orchestrator's own session-interaction logging (_run_decision_pipeline
calls session_manager.save(); explain() alone does not), so /decision
calls never showed up in a session's interaction history the way
/query calls did. This route now calls _run_decision_pipeline(), the
same method /api/v1/query dispatches to once the Intent Router
classifies a question as DECISION — so both paths now behave
identically, and /decision also gains the lightweight-followup
capability for free.

Author
------
Intelligent Credit Decision Support Platform
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.dependencies import get_orchestrator
from backend.schemas import AIResponse, DecisionRequest
from backend.serializers import build_ai_response, dump_model

router = APIRouter(prefix="/api/v1", tags=["decision"])
logger = logging.getLogger("backend.decision")


@router.post(
    "/decision",
    response_model=AIResponse,
    response_model_exclude_none=True,
    summary="Run a prediction, or answer a follow-up about the last one",
)
def run_decision(
    payload: DecisionRequest,
    debug: bool = Query(
        False, description="Include the full internal LLM prompt in the response."
    ),
    orchestrator=Depends(get_orchestrator),
):
    applicant = dump_model(payload.applicant) if payload.applicant else None
    started = time.perf_counter()

    try:
        result = orchestrator._run_decision_pipeline(
            question=payload.question,
            applicant=applicant,
            session_id=payload.session_id,
        )

    except ValueError as error:
        # Missing applicant fields, unrecognized categorical values, or
        # "no session exists yet for a follow-up" — all client errors.
        raise HTTPException(status_code=422, detail=str(error))

    except Exception as error:
        logger.exception("Decision pipeline failed")
        raise HTTPException(
            status_code=500, detail=f"Decision pipeline failed: {error}"
        )

    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "session=%s intent=%s elapsed_ms=%.1f",
        payload.session_id, result.get("intent"), elapsed_ms,
    )

    return build_ai_response(result, elapsed_ms, payload.session_id, debug)