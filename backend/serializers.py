"""
serializers.py

Converts Orchestrator / PredictionService output into plain,
JSON-serializable Python structures.

Why this exists
----------------
Orchestrator results contain objects FastAPI's default encoder
cannot serialize on their own:

- shap.Explanation objects (prediction["shap_explanation"], and
  the same key inside the evidence dict)
- pandas.DataFrame (prediction["prepared_dataframe"])
- pandas.Series (explanation.data)
- numpy scalar types (np.int64, np.float64, ...) inside
  top_features
- LangChain-style Document objects inside retrieved_documents

to_jsonable() walks a result recursively, drops fields that are
only useful for internal reasoning between pipeline stages (the
raw dataframe and the SHAP explanation object itself — the
human-relevant SHAP numbers are already flattened into
"top_features" by FeatureSelector / PredictionService), and
converts every remaining object into a native, JSON-safe type.

Without this, returning an Orchestrator result directly from a
FastAPI route raises a 500 error the moment FastAPI tries to
encode a shap.Explanation or a pandas DataFrame.
"""

from typing import Any

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

    # Defensive fallback for any other custom object (e.g. a
    # shap.Explanation that slipped through under a different key
    # name than the ones excluded above).
    return str(value)


def dump_model(pydantic_model) -> dict:
    """
    Pydantic v1/v2 compatibility helper. Pydantic v2 renamed
    `.dict()` to `.model_dump()`; this works with either.
    """

    if hasattr(pydantic_model, "model_dump"):
        return pydantic_model.model_dump()

    return pydantic_model.dict()