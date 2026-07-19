"""
simulation.py

Runs a What-If simulation via Orchestrator's internal simulation
pipeline. Note: this calls the "private" _run_simulation_pipeline
method directly rather than going through process_request(),
because this endpoint is explicitly for simulation requests —
there's no need to spend an LLM call re-detecting intent when the
caller already knows what they want. (The leading underscore on
that method is just a Python convention; it's not access-controlled.)
"""

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_orchestrator
from backend.schemas import SimulationRequest
from backend.serializers import dump_model, to_jsonable

router = APIRouter(prefix="/api/v1", tags=["simulation"])


@router.post("/simulate")
def run_simulation(payload: SimulationRequest, orchestrator=Depends(get_orchestrator)):

    applicant = dump_model(payload.applicant) if payload.applicant else None

    try:

        result = orchestrator._run_simulation_pipeline(
            question=payload.question,
            applicant=applicant,
            simulation_changes=payload.changes,
            session_id=payload.session_id,
        )

    except ValueError as error:
        # Raised when no applicant is supplied AND no session
        # exists to fall back on (see orchestrator.py), or from
        # PredictionService validation inside SimulationEngine.
        raise HTTPException(status_code=422, detail=str(error))

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Simulation pipeline failed: {error}",
        )

    return to_jsonable(result)