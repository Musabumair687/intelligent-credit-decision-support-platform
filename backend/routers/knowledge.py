"""
knowledge.py

Runs the bank-policy / RAG question pipeline directly, bypassing
intent detection — use this for the standalone Policy Knowledge page,
where every question is a plain policy lookup with no prediction
context involved.

Author
------
Intelligent Credit Decision Support Platform
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.dependencies import get_orchestrator
from backend.schemas import AIResponse, KnowledgeRequest
from backend.serializers import build_ai_response

router = APIRouter(prefix="/api/v1", tags=["knowledge"])
logger = logging.getLogger("backend.knowledge")


@router.post(
    "/knowledge",
    response_model=AIResponse,
    response_model_exclude_none=True,
    summary="Ask a standalone bank-policy question (no prediction context)",
)
def run_knowledge(
    payload: KnowledgeRequest,
    debug: bool = Query(
        False, description="Include the full internal LLM prompt in the response."
    ),
    orchestrator=Depends(get_orchestrator),
):
    started = time.perf_counter()

    try:
        result = orchestrator._run_knowledge_pipeline(
            question=payload.question,
            session_id=payload.session_id,
        )

    except Exception as error:
        logger.exception("Knowledge pipeline failed")
        raise HTTPException(
            status_code=500, detail=f"Knowledge pipeline failed: {error}"
        )

    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "session=%s intent=%s elapsed_ms=%.1f",
        payload.session_id, result.get("intent"), elapsed_ms,
    )

    return build_ai_response(result, elapsed_ms, payload.session_id, debug)