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

Prediction -> Feature Selection -> Query Generation ->
Retrieval -> Evidence Builder -> Decision Prompt ->
Response Generator

Simulation Pipeline

Simulation Engine -> Simulation Prompt -> Response Generator

General / Knowledge Pipeline

Retrieval -> General Prompt -> Response Generator

Fixes applied in this version
------------------------------
1. intent_router.classify(...) is now called correctly
   (the method is `classify`, not `route`), and its return
   value (a dict containing an Intent enum) is unpacked and
   compared against Intent members instead of raw strings.

2. simulation_prompt.build_prompt(...) is now called with
   the correct method name and keyword arguments (the method
   was `build_prompt`, not `build`, and its second argument
   is `simulation_result`, not `simulation`).

3. The general pipeline now performs retrieval before calling
   general_prompt.build(), since GeneralPrompt.build() requires
   retrieved_documents and previously received none.

4. Session handling now goes through SessionManager.create_session
   / update_session / save (save previously did not exist), and
   a single shared SessionManager + ContextManager instance is
   used consistently instead of ContextManager silently owning
   its own, disconnected SessionManager.

5. Conversation history is now passed into intent classification
   so multi-turn "what if" follow-ups have context.

Author
------
Intelligent Credit Decision Support Platform
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

from rag.decision_intelligence.routing.intent_schema import (
    Intent,
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
        # Shared state (single SessionManager instance,
        # used by both the Orchestrator directly and by
        # ContextManager, so they never disagree about
        # what "the current session" is).
        # ---------------------------------------------

        self.session_manager = SessionManager()

        self.context_manager = ContextManager(
            session_manager=self.session_manager,
        )

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
    ) -> dict:
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
        # Pull existing conversation history (if any) so
        # the router has multi-turn context available.
        # ---------------------------------------------

        existing_session = self.session_manager.get_session(
            session_id=session_id,
        )

        conversation_history = (
            existing_session["conversation_history"]
            if existing_session
            else []
        )

        # ---------------------------------------------
        # Detect Intent
        # ---------------------------------------------

        routing_result = self.intent_router.classify(
            current_query=user_question,
            conversation_history=conversation_history,
        )

        intent = routing_result["intent"]

        # ---------------------------------------------
        # Decision Pipeline
        # ---------------------------------------------

        if intent == Intent.DECISION:

            return self._run_decision_pipeline(
                question=user_question,
                applicant=applicant,
                session_id=session_id,
            )

        # ---------------------------------------------
        # Simulation Pipeline
        # ---------------------------------------------

        if intent == Intent.SIMULATION:

            return self._run_simulation_pipeline(
                question=user_question,
                applicant=applicant,
                simulation_changes=simulation_changes,
                session_id=session_id,
            )

        # ---------------------------------------------
        # Knowledge Pipeline (bank policy / RAG questions)
        # ---------------------------------------------

        if intent == Intent.KNOWLEDGE:

            return self._run_knowledge_pipeline(
                question=user_question,
                session_id=session_id,
            )

        # ---------------------------------------------
        # General / Unknown -> General Pipeline
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
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Complete Decision Intelligence pipeline: predict,
        build evidence, retrieve policy support, and explain.

        Parameters
        ----------
        applicant : dict

        user_question : str

        session_id : str | None

        Returns
        -------
        dict
        """

        # -------------------------------------------------
        # Step 1 — ML Prediction
        # -------------------------------------------------

        prediction = self.prediction_service.predict(applicant)

        # -------------------------------------------------
        # Step 2 — Persist session so ContextManager and
        # any downstream "what-if" request can find it.
        # -------------------------------------------------

        self.session_manager.create_session(
            applicant=applicant,
            prediction=prediction["prediction"],
            repayment_probability=prediction["repayment_probability"],
            default_probability=prediction["default_probability"],
            shap_explanation=prediction["shap_explanation"],
            session_id=session_id,
        )

        self.session_manager.add_message(
            role="user",
            message=user_question,
            session_id=session_id,
        )

        # -------------------------------------------------
        # Step 3 — Build Context (now actually used)
        # -------------------------------------------------

        prediction_context = self.context_manager.build_prediction_context(
            session_id=session_id,
        )

        evidence_input = {
            "applicant": prediction_context["applicant"],
            "prediction": prediction_context["prediction"],
            "repayment_probability": prediction_context["repayment_probability"],
            "default_probability": prediction_context["default_probability"],
            "shap_explanation": prediction_context["shap_explanation"],
        }

        # -------------------------------------------------
        # Step 4 — Build Evidence
        # -------------------------------------------------

        evidence = self.evidence_builder.build(evidence_input)

        # -------------------------------------------------
        # Step 5 — Retrieve Documents
        # -------------------------------------------------

        evidence = self.retrieval_engine.retrieve(evidence)

        self.session_manager.update_session(
            key="retrieved_documents",
            value=evidence["retrieved_documents"],
            session_id=session_id,
        )

        # -------------------------------------------------
        # Step 6 — Build Prompt
        # -------------------------------------------------

        prompt = self.decision_prompt.build(
            user_question=user_question,
            evidence=evidence,
        )

        # -------------------------------------------------
        # Step 7 — Generate Response
        # -------------------------------------------------

        answer = self.response_generator.generate(prompt)

        self.session_manager.add_message(
            role="assistant",
            message=answer,
            session_id=session_id,
        )

        # -------------------------------------------------
        # Step 8 — Final Package
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
            session_id=session_id,
        )

        self.session_manager.save(
            interaction={"type": "decision", **result},
            session_id=session_id,
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

        # If the caller didn't pass an applicant explicitly,
        # fall back to the applicant already on file for this
        # session (typical for a follow-up "what if" question).

        if applicant is None:

            session = self.session_manager.get_session(
                session_id=session_id,
            )

            if session is None:
                raise ValueError(
                    "No applicant supplied and no active session "
                    "exists to simulate against."
                )

            applicant = session["applicant"]

        simulation = self.simulation_engine.simulate(
            applicant=applicant,
            changes=simulation_changes,
        )

        # NOTE: SimulationPrompt exposes build_prompt(...), not
        # build(...), and its second argument is named
        # simulation_result, not simulation.

        prompt = self.simulation_prompt.build_prompt(
            user_question=question,
            simulation_result=simulation,
        )

        answer = self.response_generator.generate(prompt)

        result = {
            "simulation": simulation,
            "prompt": prompt,
            "answer": answer,
        }

        self.session_manager.add_message(
            role="user",
            message=question,
            session_id=session_id,
        )

        self.session_manager.add_message(
            role="assistant",
            message=answer,
            session_id=session_id,
        )

        self.session_manager.save(
            interaction={"type": "simulation", **result},
            session_id=session_id,
        )

        return result

    # ---------------------------------------------------------

    def _run_knowledge_pipeline(
        self,
        question: str,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Execute the Knowledge / bank-policy pipeline: retrieve
        relevant policy chunks directly from the retrieval
        engine (using the raw question as the query, since
        there is no SHAP-derived evidence for a pure policy
        question), then answer using GeneralPrompt.
        """

        evidence = {"retrieval_query": question}

        evidence = self.retrieval_engine.retrieve(evidence)

        retrieved_documents = [
            item["document"].page_content
            for item in evidence["retrieved_documents"]
        ]

        prompt = self.general_prompt.build(
            query=question,
            retrieved_documents=retrieved_documents,
        )

        answer = self.response_generator.generate(prompt)

        result = {
            "prompt": prompt,
            "answer": answer,
            "retrieved_documents": evidence["retrieved_documents"],
        }

        self.session_manager.add_message(
            role="user",
            message=question,
            session_id=session_id,
        )

        self.session_manager.add_message(
            role="assistant",
            message=answer,
            session_id=session_id,
        )

        self.session_manager.save(
            interaction={"type": "knowledge", **result},
            session_id=session_id,
        )

        return result

    # ---------------------------------------------------------

    def _run_general_pipeline(
        self,
        question: str,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Execute the General Question pipeline for small talk /
        anything that isn't a decision, simulation, or policy
        question. Uses GeneralPrompt with an empty document set
        so it will correctly respond that it has no grounding,
        rather than crashing on a missing argument.
        """

        prompt = self.general_prompt.build(
            query=question,
            retrieved_documents=[],
        )

        answer = self.response_generator.generate(prompt)

        result = {
            "prompt": prompt,
            "answer": answer,
        }

        self.session_manager.save(
            interaction={"type": "general", **result},
            session_id=session_id,
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
        session_id="test-session",
    )

    print("=" * 80)
    print("ORCHESTRATOR TEST")
    print("=" * 80)

    print("\nPrediction")
    print("-" * 80)
    print(result["prediction"]["prediction"])

    print("\nRepayment Probability")
    print("-" * 80)
    print(result["prediction"]["repayment_probability"])

    print("\nDefault Probability")
    print("-" * 80)
    print(result["prediction"]["default_probability"])

    print("\nTop SHAP Features")
    print("-" * 80)

    for feature in result["evidence"]["top_features"]:
        print(f"{feature['feature']} (Importance: {feature['importance']:.4f})")

    print("\nRetrieved Documents")
    print("-" * 80)
    print(len(result["evidence"]["retrieved_documents"]))

    print("\nPrompt Preview")
    print("-" * 80)
    print(result["prompt"][:1000])

    print("\nFinal AI Response")
    print("-" * 80)
    print(result["answer"])