"""
general.py

Runs the general/small-talk pipeline directly, bypassing intent
detection.
"""

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_orchestrator
from backend.schemas import GeneralRequest
from backend.serializers import to_jsonable

router = APIRouter(prefix="/api/v1", tags=["general"])


@router.post("/general")
def run_general(payload: GeneralRequest, orchestrator=Depends(get_orchestrator)):

    try:

        result = orchestrator._run_general_pipeline(
            question=payload.question,
            session_id=payload.session_id,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"General pipeline failed: {error}",
        )

    return to_jsonable(result)