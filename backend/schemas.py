"""
schemas.py

Pydantic request AND response models for the FastAPI backend.

Response envelope
------------------
Every AI-facing endpoint (decision, simulate, knowledge, general,
query) returns the SAME shape: AIResponse. This means a frontend can
use one response parser for all five endpoints, branching only on the
"intent" field, rather than needing five different parsers for five
different raw dict shapes. Fields that don't apply to a given intent
are simply omitted from the JSON (response_model_exclude_none=True is
set on every route), not sent as null.

ApplicantIn mirrors the sample applicant dict used throughout
prediction_service.py's own __main__ test block. If your actual
trained model expects a different or larger feature set, either
update the fields below to match, or leave them as-is — extra="allow"
means anything you send is passed straight through to
PredictionService, which already raises a clear ValueError listing
anything still missing.

Author
------
Intelligent Credit Decision Support Platform
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ApplicantIn(BaseModel):

    loan_amnt: float = Field(..., examples=[12000])
    term: int = Field(..., examples=[36])
    int_rate: float = Field(..., examples=[13.33])
    sub_grade: str = Field(..., examples=["B3"])
    emp_length: int = Field(..., examples=[7])
    home_ownership: str = Field(..., examples=["MORTGAGE"])
    verification_status: str = Field(..., examples=["Verified"])
    annual_inc: float = Field(..., examples=[71000])
    purpose: str = Field(..., examples=["debt_consolidation"])
    dti: float = Field(..., examples=[12])
    open_acc: int = Field(..., examples=[10])
    pub_rec: int = Field(..., examples=[0])
    revol_bal: float = Field(..., examples=[6000])
    revol_util: float = Field(..., examples=[41])
    total_acc: int = Field(..., examples=[28])
    initial_list_status: str = Field(..., examples=["w"])
    application_type: str = Field(..., examples=["INDIVIDUAL"])
    mort_acc: int = Field(..., examples=[2])
    pub_rec_bankruptcies: int = Field(..., examples=[0])

    # Allow extra fields through untouched, in case your real
    # feature_order (from X_train.pkl) differs from this sample.
    model_config = ConfigDict(extra="allow")


# ==========================================================
# Requests
# ==========================================================

class DecisionRequest(BaseModel):
    applicant: Optional[ApplicantIn] = Field(
        default=None,
        description=(
            "Full applicant to run a fresh prediction against. Omit this "
            "for a follow-up question about the applicant already on file "
            "for session_id — no re-prediction, no model call, just a new "
            "answer using the existing decision context."
        ),
    )
    question: str = Field(..., examples=["Why was this applicant rejected?"])
    session_id: Optional[str] = None


class SimulationRequest(BaseModel):
    applicant: Optional[ApplicantIn] = Field(
        default=None,
        description=(
            "Full applicant. If omitted, the applicant already stored "
            "under session_id is reused — required for follow-up 'what "
            "if' questions in a chat flow."
        ),
    )
    changes: Optional[Dict[str, Any]] = Field(
        default=None,
        examples=[{"annual_inc": 95000, "dti": 8}],
        description=(
            "Explicit field->new-value changes. Optional — if omitted, "
            "the question text itself is parsed for what to change "
            "(e.g. 'what if annual income increases to 150000?')."
        ),
    )
    question: str = Field(
        ..., examples=["What if annual income increases to 95000?"]
    )
    session_id: Optional[str] = None


class KnowledgeRequest(BaseModel):
    question: str = Field(..., examples=["What is the maximum allowed DTI?"])
    session_id: Optional[str] = None


class GeneralRequest(BaseModel):
    question: str = Field(..., examples=["Hello, what can you help me with?"])
    session_id: Optional[str] = None


class QueryRequest(BaseModel):
    """
    Unified entrypoint. Send every chat message here and let the
    Orchestrator's IntentRouter decide which pipeline handles it.
    """

    question: str
    applicant: Optional[ApplicantIn] = None
    changes: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


# ==========================================================
# Response envelope — shared by every AI-facing endpoint
# ==========================================================

class AIResponse(BaseModel):
    """
    Uniform response shape for /decision, /simulate, /knowledge,
    /general, and /query. Only the fields relevant to the detected
    intent are populated; the rest are omitted from the JSON output
    (see response_model_exclude_none=True on each route).
    """

    intent: str = Field(
        ..., examples=["DECISION", "SIMULATION", "KNOWLEDGE", "GENERAL"],
        description="Which pipeline actually produced this response.",
    )
    answer: str = Field(..., description="The natural-language explanation.")
    session_id: Optional[str] = None
    elapsed_ms: Optional[float] = Field(
        default=None, description="Server-side processing time in milliseconds."
    )

    # Populated only for intent == DECISION
    prediction: Optional[Dict[str, Any]] = None
    evidence: Optional[Dict[str, Any]] = None

    # Populated only for intent == SIMULATION
    simulation: Optional[Dict[str, Any]] = None

    # Populated only for intent == KNOWLEDGE (and present inside
    # `evidence` for DECISION — see docstring in routers/decision.py)
    retrieved_documents: Optional[List[Dict[str, Any]]] = None

    # Only included when the request was made with ?debug=true
    prompt: Optional[str] = Field(
        default=None,
        description="The full internal LLM prompt. Only present when ?debug=true.",
    )

    model_config = ConfigDict(extra="ignore")