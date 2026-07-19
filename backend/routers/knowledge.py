"""
knowledge.py

Runs the bank-policy / RAG question pipeline directly, bypassing
intent detection — use this when the frontend already knows the
user is asking a policy question (e.g. a dedicated "Ask about
policy" tab).
"""

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_orchestrator
from backend.schemas import KnowledgeRequest
from backend.serializers import to_jsonable

router = APIRouter(prefix="/api/v1", tags=["knowledge"])


@router.post("/knowledge")
def run_knowledge(payload: KnowledgeRequest, orchestrator=Depends(get_orchestrator)):

    try:

        result = orchestrator._run_knowledge_pipeline(
            question=payload.question,
            session_id=payload.session_id,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Knowledge pipeline failed: {error}",
        )

    return to_jsonable(result)