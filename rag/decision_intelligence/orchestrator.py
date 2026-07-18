"""
orchestrator.py

Purpose
-------
Central coordinator for the Decision Intelligence module.

The Orchestrator is responsible for directing every
user request to the correct pipeline.

It DOES NOT:

- perform ML prediction
- retrieve documents
- build prompts
- call the LLM directly

Instead, it coordinates the specialized modules.

Pipelines
---------

Decision Pipeline

Prediction
    ↓
Feature Selection
    ↓
Query Generation
    ↓
Retrieval
    ↓
Evidence Builder
    ↓
Decision Prompt
    ↓
Response Generator

-----------------------------------------

Simulation Pipeline

Simulation Engine
      ↓
Simulation Prompt
      ↓
Response Generator

-----------------------------------------

General Pipeline

General Prompt
      ↓
Response Generator
"""

from typing import Optional

# ==========================================================
# Managers
# ==========================================================

from rag.decision_intelligence.managers.context_manager import (
    ContextManager,
)

from rag.decision_intelligence.managers.session_manager import (
    SessionManager,
)

# ==========================================================
# Routing
# ==========================================================

from rag.decision_intelligence.routing.intent_router import (
    IntentRouter,
)

# ==========================================================
# ML
# ==========================================================

from ml.prediction_service import PredictionService

# ==========================================================
# Evidence
# ==========================================================

from rag.decision_intelligence.evidence.feature_selector import (
    FeatureSelector,
)

from rag.decision_intelligence.evidence.query_generator import (
    QueryGenerator,
)

from rag.decision_intelligence.evidence.evidence_builder import (
    EvidenceBuilder,
)

# ==========================================================
# Retrieval
# ==========================================================

from rag.decision_intelligence.retrieval.retrieval_engine import (
    RetrievalEngine,
)

# ==========================================================
# Prompt Builders
# ==========================================================

from rag.decision_intelligence.prompt.decision_prompt import (
    DecisionPrompt,
)

from rag.decision_intelligence.prompt.simulation_prompt import (
    SimulationPrompt,
)

from rag.decision_intelligence.prompt.general_prompt import (
    GeneralPrompt,
)

# ==========================================================
# Simulation
# ==========================================================

from rag.decision_intelligence.simulation.simulation_engine import (
    SimulationEngine,
)

# ==========================================================
# Generator
# ==========================================================

from rag.decision_intelligence.generator.response_generator import (
    ResponseGenerator,
)


class Orchestrator:
    """
    Coordinates the complete Decision Intelligence workflow.
    """

    def __init__(self):
        """
        Initialize every module required by the system.
        """

        # ---------------------------------------------
        # Managers
        # ---------------------------------------------

        self.context_manager = ContextManager()

        self.session_manager = SessionManager()

        # ---------------------------------------------
        # Routing
        # ---------------------------------------------

        self.intent_router = IntentRouter()

        # ---------------------------------------------
        # ML
        # ---------------------------------------------

        self.prediction_service = PredictionService()

        # ---------------------------------------------
        # Evidence
        # ---------------------------------------------

        self.feature_selector = FeatureSelector()

        self.query_generator = QueryGenerator()

        self.evidence_builder = EvidenceBuilder()

        # ---------------------------------------------
        # Retrieval
        # ---------------------------------------------

        self.retrieval_engine = RetrievalEngine()

        # ---------------------------------------------
        # Prompt Builders
        # ---------------------------------------------

        self.decision_prompt = DecisionPrompt()

        self.simulation_prompt = SimulationPrompt()

        self.general_prompt = GeneralPrompt()

        # ---------------------------------------------
        # Simulation
        # ---------------------------------------------

        self.simulation_engine = SimulationEngine()

        # ---------------------------------------------
        # Response Generator
        # ---------------------------------------------

        self.response_generator = ResponseGenerator()

    # ======================================================
    # Public Entry Point
    # ======================================================

    def process_request(
        self,
        user_question: str,
        applicant: Optional[dict] = None,
        simulation_changes: Optional[dict] = None,
        session_id: Optional[str] = None,
    ):
        """
        Main entry point of the Decision Intelligence system.

        Every frontend request should enter the system
        through this function.

        Parameters
        ----------
        user_question : str

        applicant : dict | None

        simulation_changes : dict | None

        session_id : str | None

        Returns
        -------
        dict
        """

        # ---------------------------------------------
        # Detect Intent
        # ---------------------------------------------

        intent = self.intent_router.route(
            question=user_question,
        )

        # ---------------------------------------------
        # Decision Pipeline
        # ---------------------------------------------

        if intent == "decision":

            return self._run_decision_pipeline(
                question=user_question,
                applicant=applicant,
                session_id=session_id,
            )

        # ---------------------------------------------
        # Simulation Pipeline
        # ---------------------------------------------

        elif intent == "simulation":

            return self._run_simulation_pipeline(
                question=user_question,
                applicant=applicant,
                simulation_changes=simulation_changes,
                session_id=session_id,
            )

        # ---------------------------------------------
        # General Pipeline
        # ---------------------------------------------

        return self._run_general_pipeline(
            question=user_question,
            session_id=session_id,
        )

    # ---------------------------------------------------------

    def explain(
        self,
        applicant: dict,
        user_question: str,
    ) -> dict:
        """
        Complete Decision Intelligence pipeline.

        Parameters
        ----------
        applicant : dict

        user_question : str

        Returns
        -------
        dict
        """

        # -------------------------------------------------
        # Step 1
        # ML Prediction
        # -------------------------------------------------

        prediction = self.prediction_service.predict(
            applicant
        )

        # -------------------------------------------------
        # Step 2
        # Build Context
        # -------------------------------------------------

        context = {

        "applicant": applicant,

        "prediction": prediction["prediction"],
 
        "probability": prediction["default_probability"],

        "shap_explanation": prediction["shap_explanation"],

}

        # -------------------------------------------------
        # Step 3
        # Build Evidence
        # -------------------------------------------------

        evidence = self.evidence_builder.build(
         context
           )

        # -------------------------------------------------
        # Step 4
        # Retrieve Documents
        # -------------------------------------------------

        evidence = self.retrieval_engine.retrieve(
            evidence
        )

        # -------------------------------------------------
        # Step 5
        # Build Prompt
        # -------------------------------------------------

        prompt = self.decision_prompt.build(

        user_question=user_question,

        evidence=evidence,

        )

        # -------------------------------------------------
        # Step 6
        # Generate Response
        # -------------------------------------------------

        answer = self.response_generator.generate(
            prompt
        )

        # -------------------------------------------------
        # Step 7
        # Final Package
        # -------------------------------------------------

        return {

            "prediction": prediction,

            "evidence": evidence,

            "prompt": prompt,

            "answer": answer,

        }
    # ======================================================
    # Internal Pipelines
    # ======================================================

    def _run_decision_pipeline(
        self,
        question: str,
        applicant: dict,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Execute the complete Decision pipeline.
        """

        result = self.explain(

            applicant=applicant,

            user_question=question,

        )

        if session_id is not None:

            self.session_manager.save(

                session_id=session_id,

                interaction=result,

            )

        return result

    # ---------------------------------------------------------

    def _run_simulation_pipeline(
        self,
        question: str,
        applicant: dict,
        simulation_changes: dict,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Execute the complete Simulation pipeline.
        """

        simulation = self.simulation_engine.simulate(

            applicant=applicant,

            changes=simulation_changes,

        )

        prompt = self.simulation_prompt.build(

            user_question=question,

            simulation=simulation,

        )

        answer = self.response_generator.generate(

            prompt

        )

        result = {

            "simulation": simulation,

            "prompt": prompt,

            "answer": answer,

        }

        if session_id is not None:

            self.session_manager.save(

                session_id=session_id,

                interaction=result,

            )

        return result

    # ---------------------------------------------------------

    def _run_general_pipeline(
        self,
        question: str,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Execute the General Question pipeline.
        """

        prompt = self.general_prompt.build(

            question

        )

        answer = self.response_generator.generate(

            prompt

        )

        result = {

            "prompt": prompt,

            "answer": answer,

        }

        if session_id is not None:

            self.session_manager.save(

                session_id=session_id,

                interaction=result,

            )

        return result


# ==========================================================
# Testing
# ==========================================================

if __name__ == "__main__":

    orchestrator = Orchestrator()

    applicant = {

        "loan_amnt": 12000,

        "term": 36,

        "int_rate": 13.33,

        "sub_grade": "B3",

        "emp_length": 7,

        "home_ownership": "MORTGAGE",

        "verification_status": "Verified",

        "annual_inc": 71000,

        "purpose": "debt_consolidation",

        "dti": 12,

        "open_acc": 10,

        "pub_rec": 0,

        "revol_bal": 6000,

        "revol_util": 41,

        "total_acc": 28,

        "initial_list_status": "w",

        "application_type": "INDIVIDUAL",

        "mort_acc": 2,

        "pub_rec_bankruptcies": 0,

    }

    question = "Why was this applicant rejected?"

    result = orchestrator.explain(

        applicant=applicant,

        user_question=question,

    )

    print("=" * 80)
    print("ORCHESTRATOR TEST")
    print("=" * 80)

    print("\nPrediction")
    print("-" * 80)
    print(result["prediction"]["prediction"])

    print("\nRepayment Probability")
    print("-" * 80)
    print(
        result["prediction"]["repayment_probability"]
    )

    print("\nDefault Probability")
    print("-" * 80)
    print(
        result["prediction"]["default_probability"]
    )

    print("\nTop SHAP Features")
    print("-" * 80)

    for feature in result["evidence"]["top_features"]:

        print(
            f"{feature['feature']} "
            f"(Importance: {feature['importance']:.4f})"
        )

    print("\nRetrieved Documents")
    print("-" * 80)

    print(
        len(
            result["evidence"]["retrieved_documents"]
        )
    )

    print("\nPrompt Preview")
    print("-" * 80)

    print(result["prompt"][:1000])

    print("\nFinal AI Response")
    print("-" * 80)

    print(result["answer"])