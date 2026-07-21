"""
simulation.py

Runs a What-If simulation. Accepts EITHER structured `changes`
(explicit field -> new-value mapping, used by the Simulation page's
form), OR free text within `question` alone — if `changes` is empty
or omitted, Orchestrator now parses the question itself (a fast
regex/synonym heuristic first, an LLM extraction fallback second) to
determine what to change. This is what powers a chat-typed "what if
annual income increases to 150000?" without the frontend needing to
parse anything itself.

Author
------
Intelligent Credit Decision Support Platform
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.dependencies import get_orchestrator
from backend.schemas import AIResponse, SimulationRequest
from backend.serializers import build_ai_response, dump_model

router = APIRouter(prefix="/api/v1", tags=["simulation"])
logger = logging.getLogger("backend.simulation")


@router.post(
    "/simulate",
    response_model=AIResponse,
    response_model_exclude_none=True,
    summary="Run a what-if simulation, with structured or free-text changes",
)
def run_simulation(
    payload: SimulationRequest,
    debug: bool = Query(
        False, description="Include the full internal LLM prompt in the response."
    ),
    orchestrator=Depends(get_orchestrator),
):
    applicant = dump_model(payload.applicant) if payload.applicant else None
    started = time.perf_counter()

    try:
        result = orchestrator._run_simulation_pipeline(
            question=payload.question,
            applicant=applicant,
            simulation_changes=payload.changes,
            session_id=payload.session_id,
        )

    except ValueError as error:
        # Covers: no applicant + no session to fall back on, and
        # "could not identify what to change from that question".
        raise HTTPException(status_code=422, detail=str(error))

    except Exception as error:
        logger.exception("Simulation pipeline failed")
        raise HTTPException(
            status_code=500, detail=f"Simulation pipeline failed: {error}"
        )

    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "session=%s intent=%s elapsed_ms=%.1f",
        payload.session_id, result.get("intent"), elapsed_ms,
    )

    return build_ai_response(result, elapsed_ms, payload.session_id, debug)