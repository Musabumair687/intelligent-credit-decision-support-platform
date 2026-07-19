"""
dependencies.py

FastAPI dependency providers.

The Orchestrator is expensive to construct — it loads the
LightGBM model, label encoders, the full X_train.pkl, builds a
SHAP TreeExplainer, and initializes LLM/retriever clients — so it
must be built exactly once, at application startup, not per
request. main.py builds it in a lifespan handler and stores it on
app.state; get_orchestrator() below just hands back that shared
instance to each route.
"""

from fastapi import Request

from rag.decision_intelligence.orchestrator import Orchestrator


def get_orchestrator(request: Request) -> Orchestrator:
    orchestrator = getattr(request.app.state, "orchestrator", None)

    if orchestrator is None:
        raise RuntimeError(
            "Orchestrator is not initialized. This should only "
            "happen if a route is hit before application startup "
            "has completed."
        )

    return orchestrator