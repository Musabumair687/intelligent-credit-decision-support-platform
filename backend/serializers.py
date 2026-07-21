"""
serializers.py

Converts Orchestrator / PredictionService output into plain,
JSON-serializable Python structures, and packages it into the shared
AIResponse envelope used by every AI-facing endpoint.

Why to_jsonable() exists
------------------------
Orchestrator results contain objects FastAPI's default encoder cannot
serialize on their own: shap.Explanation objects, pandas DataFrames,
numpy scalar types, and LangChain-style Document objects. to_jsonable()
walks a result recursively, drops fields only useful for internal
reasoning between pipeline stages (the raw dataframe and the SHAP
explanation object itself — the human-relevant SHAP numbers are
already flattened into "top_features" upstream), and converts
everything else into a native, JSON-safe type.

Why build_ai_response() exists
-------------------------------
Different pipelines (_run_decision_pipeline, _run_simulation_pipeline,
_run_knowledge_pipeline, _run_general_pipeline) return different raw
dict shapes internally. build_ai_response() maps whichever shape came
back into the single, uniform AIResponse envelope every route in this
API now returns, and strips the internal "prompt" field unless the
caller explicitly asked for it via ?debug=true.

Author
------
Intelligent Credit Decision Support Platform
"""

from typing import Any, Optional

import numpy as np
import pandas as pd

# Keys that are only meaningful for internal reasoning between
# pipeline stages and should never be sent to an API consumer.
_EXCLUDED_KEYS = {"prepared_dataframe", "shap_explanation"}


def to_jsonable(value: Any) -> Any:
    """
    Recursively convert a value into something FastAPI's default
    JSON encoder can handle without errors.
    """

    if isinstance(value, dict):
        return {
            key: to_jsonable(val)
            for key, val in value.items()
            if key not in _EXCLUDED_KEYS
        }

    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        return float(value)

    if isinstance(value, np.ndarray):
        return to_jsonable(value.tolist())

    if isinstance(value, pd.Series):
        return to_jsonable(value.to_dict())

    if isinstance(value, pd.DataFrame):
        return to_jsonable(value.to_dict(orient="records"))

    # LangChain-style Document objects — duck-typed so this works
    # regardless of which langchain package/version is installed.
    if hasattr(value, "page_content") and hasattr(value, "metadata"):
        return {
            "content": value.page_content,
            "metadata": to_jsonable(value.metadata),
        }

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    # Defensive fallback for any other custom object.
    return str(value)


def dump_model(pydantic_model) -> dict:
    """
    Pydantic v1/v2 compatibility helper. Pydantic v2 renamed
    `.dict()` to `.model_dump()`; this works with either.
    """

    if hasattr(pydantic_model, "model_dump"):
        return pydantic_model.model_dump()

    return pydantic_model.dict()


def build_ai_response(
    result: dict,
    elapsed_ms: float,
    session_id: Optional[str],
    debug: bool = False,
) -> dict:
    """
    Map any pipeline's raw result dict into the shared AIResponse
    envelope.

    Parameters
    ----------
    result : dict
        Raw dict returned by one of the Orchestrator's
        _run_*_pipeline methods. Must contain at least "intent" and
        "answer" (every pipeline sets both as of this version).

    elapsed_ms : float
        Server-side processing time, already measured by the caller.

    session_id : str | None
        Echoed back so the frontend can confirm which session the
        response belongs to.

    debug : bool
        When True, the full internal LLM prompt is included under
        the "prompt" key. When False (the default), it is stripped —
        a production frontend never needs it, and it's a meaningful
        amount of extra text to serialize and transmit for nothing.

    Returns
    -------
    dict
        Shaped to match backend.schemas.AIResponse. FastAPI's
        response_model validation/filtering handles the rest.
    """

    clean = to_jsonable(result)

    envelope = {
        "intent": clean.get("intent", "UNKNOWN"),
        "answer": clean.get("answer", ""),
        "session_id": session_id,
        "elapsed_ms": round(elapsed_ms, 1),
        "prediction": clean.get("prediction"),
        "evidence": clean.get("evidence"),
        "simulation": clean.get("simulation"),
        "retrieved_documents": clean.get("retrieved_documents"),
    }

    if debug:
        envelope["prompt"] = clean.get("prompt")

    return envelope