from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(request: Request):
    """
    Basic readiness probe. Returns model_loaded = False only in
    the brief window before the startup lifespan handler finishes
    (or if it failed).
    """

    orchestrator = getattr(request.app.state, "orchestrator", None)

    return {
        "status": "ok" if orchestrator is not None else "not_ready",
        "model_loaded": orchestrator is not None,
    }