"""
schemas.py

Pydantic request models for the FastAPI backend.

ApplicantIn mirrors the sample applicant dict used throughout
prediction_service.py's own __main__ test block. If your actual
trained model (models/lightgbm_model.pkl) expects a different or
larger feature set than this, either:

  (a) update the fields below to match, or
  (b) leave them as-is and just send whatever extra fields you
      need — `extra = "allow"` means anything you send is passed
      straight through to PredictionService, which already raises
      a clear ValueError listing anything still missing
      (see validate_input in prediction_service.py).

Author
------
Intelligent Credit Decision Support Platform
"""

from typing import Any, Dict, Optional

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


class DecisionRequest(BaseModel):
    applicant: ApplicantIn
    question: str = Field(..., examples=["Why was this applicant rejected?"])
    session_id: Optional[str] = None


class SimulationRequest(BaseModel):
    applicant: Optional[ApplicantIn] = Field(
        default=None,
        description=(
            "Full applicant. If omitted, the applicant already "
            "stored under session_id is reused — required for "
            "follow-up 'what if' questions in a chat flow."
        ),
    )
    changes: Dict[str, Any] = Field(
        ...,
        examples=[{"annual_inc": 95000, "dti": 8}],
        description=(
            "New values to apply on top of the applicant. Passed "
            "straight through to SimulationEngine.simulate()."
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