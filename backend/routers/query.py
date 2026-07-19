"""
query.py

Single unified entrypoint: lets the Orchestrator's IntentRouter
decide whether an incoming message is a decision / simulation /
knowledge / general question, and runs the matching pipeline.

This is the endpoint a chat-style frontend should call for every
message in a conversation — it's the closest match to
Orchestrator.process_request(), the method your own architecture
diagram shows as the single entrypoint beneath the frontend.
"""

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_orchestrator
from backend.schemas import QueryRequest
from backend.serializers import dump_model, to_jsonable

router = APIRouter(prefix="/api/v1", tags=["query"])


@router.post("/query")
def run_query(payload: QueryRequest, orchestrator=Depends(get_orchestrator)):

    applicant = dump_model(payload.applicant) if payload.applicant else None

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
        raise HTTPException(status_code=500, detail=f"Query failed: {error}")

    return to_jsonable(result)