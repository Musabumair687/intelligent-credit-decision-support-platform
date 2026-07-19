"""
session.py

Lets a frontend inspect or clear the server-side session state
(applicant, prediction, SHAP data, conversation history) tracked
by SessionManager for a given session_id.
"""

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_orchestrator
from backend.serializers import to_jsonable

router = APIRouter(prefix="/api/v1", tags=["session"])


@router.get("/session/{session_id}")
def get_session(session_id: str, orchestrator=Depends(get_orchestrator)):

    session = orchestrator.session_manager.get_session(session_id=session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"No session found for '{session_id}'.",
        )

    return to_jsonable(session)


@router.delete("/session/{session_id}")
def clear_session(session_id: str, orchestrator=Depends(get_orchestrator)):

    orchestrator.session_manager.clear_session(session_id=session_id)

    return {"status": "cleared", "session_id": session_id}