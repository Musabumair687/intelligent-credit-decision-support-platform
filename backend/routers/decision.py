"""
decision.py

Runs the full ML prediction + evidence retrieval + LLM
explanation pipeline for a single applicant (Orchestrator.explain).
Use this endpoint when you already know the user wants a decision
explanation — e.g. the frontend's "Predict & Explain" button.
"""

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_orchestrator
from backend.schemas import DecisionRequest
from backend.serializers import dump_model, to_jsonable

router = APIRouter(prefix="/api/v1", tags=["decision"])


@router.post("/decision")
def run_decision(payload: DecisionRequest, orchestrator=Depends(get_orchestrator)):

    try:

        result = orchestrator.explain(
            applicant=dump_model(payload.applicant),
            user_question=payload.question,
            session_id=payload.session_id,
        )

    except ValueError as error:
        # Missing features / unrecognized categorical values raise
        # ValueError inside PredictionService.validate_input /
        # encode_features — these are client input errors, not
        # server errors.
        raise HTTPException(status_code=422, detail=str(error))

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Decision pipeline failed: {error}",
        )

    return to_jsonable(result)