"""
general.py

Runs the general/small-talk pipeline directly, bypassing intent
detection.

Author
------
Intelligent Credit Decision Support Platform
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.dependencies import get_orchestrator
from backend.schemas import AIResponse, GeneralRequest
from backend.serializers import build_ai_response

router = APIRouter(prefix="/api/v1", tags=["general"])
logger = logging.getLogger("backend.general")


@router.post(
    "/general",
    response_model=AIResponse,
    response_model_exclude_none=True,
    summary="Answer general small talk with no retrieval or prediction context",
)
def run_general(
    payload: GeneralRequest,
    debug: bool = Query(
        False, description="Include the full internal LLM prompt in the response."
    ),
    orchestrator=Depends(get_orchestrator),
):
    started = time.perf_counter()

    try:
        result = orchestrator._run_general_pipeline(
            question=payload.question,
            session_id=payload.session_id,
        )

    except Exception as error:
        logger.exception("General pipeline failed")
        raise HTTPException(
            status_code=500, detail=f"General pipeline failed: {error}"
        )

    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "session=%s intent=%s elapsed_ms=%.1f",
        payload.session_id, result.get("intent"), elapsed_ms,
    )

    return build_ai_response(result, elapsed_ms, payload.session_id, debug)