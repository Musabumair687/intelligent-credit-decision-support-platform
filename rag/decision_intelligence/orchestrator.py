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

Decision Pipeline (first turn: full explain)

Prediction -> Feature Selection -> Query Generation ->
Retrieval -> Evidence Builder -> Decision Prompt ->
Response Generator

Decision Pipeline (follow-up turn: lightweight)

Reuse stored Prediction + SHAP + Retrieved Documents from the
session -> Decision Prompt (new question) -> Response Generator

Simulation Pipeline

Change Extraction (structured input, or parsed from free text) ->
Simulation Engine -> Simulation Prompt -> Response Generator

Knowledge Pipeline

Retrieval -> General Prompt -> Response Generator

General Pipeline

General Prompt -> Response Generator

Fixes / features in this version
---------------------------------
1. intent_router.classify(...) is called correctly and its return value
   (a dict containing an Intent enum) is unpacked and compared against
   Intent members instead of raw strings.

2. simulation_prompt.build_prompt(...) is called with the correct method
   name and keyword arguments.

3. The general and knowledge pipelines perform retrieval before calling
   general_prompt.build(), since GeneralPrompt.build() requires
   retrieved_documents.

4. Session handling goes through SessionManager.create_session /
   update_session / save consistently, using a single shared
   SessionManager + ContextManager instance.

5. Conversation history is passed into intent classification so
   multi-turn "what if" follow-ups have context.

6. Every pipeline result now includes an explicit "intent" field
   ("DECISION" / "SIMULATION" / "KNOWLEDGE" / "GENERAL"), so a caller of
   /api/v1/query (e.g. the post-prediction "Ask AI" chat) has an
   authoritative answer to "which pipeline actually ran" instead of
   having to guess from the response's shape.

7. NEW — Decision follow-up questions no longer re-run the ML model.
   Previously, _run_decision_pipeline always called explain(), which
   requires a full applicant dict and re-runs prediction + SHAP +
   retrieval from scratch. That made "why was this rejected?" as a chat
   follow-up either impossible (no applicant available) or wastefully
   expensive (re-predicting an unchanged applicant). Now: if no
   applicant is passed in, the pipeline reuses the prediction, SHAP
   explanation, and retrieved documents already stored in the session
   from the original /api/v1/decision call, and only rebuilds the
   prompt for the new question. This is both correct (nothing about
   the applicant changed) and cheap (no model call, no retrieval call).

8. NEW — Simulation follow-ups asked in free text (e.g. "what if annual
   income increases to 150000?") are now parsed into the structured
   {field: new_value} dict simulation_engine.simulate() expects, via
   _extract_changes(): a fast regex/synonym heuristic first, falling
   back to a small LLM extraction call only if the heuristic finds
   nothing. This keeps the common, clearly-phrased case instant and
   free, and only pays the extra LLM round-trip for ambiguous phrasing.

Author
------
Intelligent Credit Decision Support Platform
"""

import json
import re
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

    # -------------------------------------------------------
    # Fields the Simulation pipeline is allowed to change, and
    # the plain-English synonyms the regex heuristic looks for.
    # Longer synonyms are checked before shorter ones so, e.g.,
    # "loan amount" matches before the bare word "loan" does.
    # -------------------------------------------------------
    SIM_FIELD_SYNONYMS = {
        "annual_inc": ["annual income", "yearly income", "gross income", "income", "salary"],
        "dti": ["debt-to-income", "debt to income", "dti"],
        "loan_amnt": ["loan amount", "amount"],
        "revol_util": ["revolving utilization", "credit utilization", "utilization"],
        "revol_bal": ["revolving balance", "credit card balance", "balance"],
        "emp_length": ["employment length", "years employed", "employment"],
        "int_rate": ["interest rate", "rate"],
        "open_acc": ["open accounts", "open credit lines"],
        "total_acc": ["total accounts", "total credit lines"],
        "mort_acc": ["mortgage accounts", "mortgages"],
    }

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

        This is the single endpoint a chat-style "Ask AI" experience
        should call: it detects intent first, then dispatches to
        exactly one of the four pipelines below. Every returned dict
        includes an "intent" field naming which pipeline actually ran.

        Parameters
        ----------
        user_question : str

        applicant : dict | None
            Only needed for a first-ever decision in a new session.
            Chat follow-ups (decision or simulation) should omit this
            and rely on the session's stored applicant instead.

        simulation_changes : dict | None
            Structured {field: new_value} changes. Optional — if the
            detected intent is SIMULATION and this is empty, the
            question text itself is parsed for changes (see
            _extract_changes).

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
        Complete Decision Intelligence pipeline: predict, build
        evidence, retrieve policy support, and explain. This is the
        FULL, expensive path — model call, SHAP, retrieval, all of it.

        Called directly by /api/v1/decision (a fresh applicant is
        always submitted there), and by _run_decision_pipeline only
        when an applicant IS supplied (i.e. not a chat follow-up).

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
        # Step 2 — Persist session so ContextManager and any
        # downstream follow-up or what-if question can find it.
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
        # Step 3 — Build Context
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

    # ---------------------------------------------------------

    def _explain_followup(
        self,
        question: str,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Lightweight decision follow-up: answers a NEW question about
        an ALREADY-PREDICTED applicant, without re-running the model,
        SHAP, or retrieval — all three are reused from the session,
        since nothing about the applicant has changed.

        Raises
        ------
        ValueError
            If no prediction session exists yet for this session_id
            (i.e. the caller asked a decision question before ever
            running a prediction).
        """

        session = self.session_manager.get_session(session_id=session_id)

        if session is None or session.get("prediction") is None:
            raise ValueError(
                "No applicant supplied and no active prediction session "
                "exists. Run a prediction first, then ask a follow-up "
                "question about it."
            )

        self.session_manager.add_message(
            role="user",
            message=question,
            session_id=session_id,
        )

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

        # Recomputing top_features here is cheap (just sorting the
        # already-computed SHAP values) — no model or retrieval call.
        evidence = self.evidence_builder.build(evidence_input)

        # Reuse the documents retrieved during the ORIGINAL prediction
        # rather than retrieving again: retrieval was driven by SHAP
        # top_features, not by the free-text question, and those
        # features haven't changed, so a fresh retrieval call would
        # return the same documents at the cost of an extra round-trip.
        evidence["retrieved_documents"] = session.get("retrieved_documents", [])

        prompt = self.decision_prompt.build(
            user_question=question,
            evidence=evidence,
        )

        answer = self.response_generator.generate(prompt)

        self.session_manager.add_message(
            role="assistant",
            message=answer,
            session_id=session_id,
        )

        return {
            "prediction": {
                "prediction": prediction_context["prediction"],
                "repayment_probability": prediction_context["repayment_probability"],
                "default_probability": prediction_context["default_probability"],
                "top_features": evidence["top_features"],
            },
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
        applicant: Optional[dict],
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Execute the Decision pipeline. Reached either directly via
        /api/v1/decision (applicant always supplied there), or via
        /api/v1/query once the Intent Router has classified the
        question as DECISION.

        If applicant is supplied, runs the full (expensive) explain().
        If applicant is None — the normal case for a chat follow-up —
        runs the lightweight _explain_followup() instead.
        """

        if applicant is not None:
            result = self.explain(
                applicant=applicant,
                user_question=question,
                session_id=session_id,
            )
        else:
            result = self._explain_followup(
                question=question,
                session_id=session_id,
            )

        result = {"intent": "DECISION", **result}

        self.session_manager.save(
            interaction=result,
            session_id=session_id,
        )

        return result

    # ---------------------------------------------------------

    def _extract_changes_heuristic(self, question: str, applicant: dict) -> dict:
        """
        Fast, free, zero-latency pass at extracting {field: new_value}
        from a what-if question, using known field synonyms and a
        nearby number. Handles the common, clearly-phrased case, e.g.:

            "what if annual income increases to 150k?"       -> {"annual_inc": 150000}
            "what if the loan amount was 8000 instead?"       -> {"loan_amnt": 8000}
            "what if dti decreases to 8?"                     -> {"dti": 8}

        Does NOT handle vague phrasing ("what if they made more
        money") — that falls through to _extract_changes_with_llm.

        Returns
        -------
        dict
            Possibly empty if nothing was confidently matched.
        """

        text = question.lower()
        changes = {}

        for field, synonyms in self.SIM_FIELD_SYNONYMS.items():

            if field not in applicant:
                continue

            for synonym in sorted(synonyms, key=len, reverse=True):

                idx = text.find(synonym)

                if idx == -1:
                    continue

                # Look at a short window of text right after the
                # synonym for the first number that appears.
                window = text[idx + len(synonym): idx + len(synonym) + 40]

                match = re.search(r"\$?\s?([\d][\d,]*(?:\.\d+)?)\s?(k|thousand)?", window)

                if not match:
                    continue

                raw_number = match.group(1).replace(",", "")

                try:
                    value = float(raw_number)
                except ValueError:
                    continue

                if match.group(2):
                    value *= 1000

                changes[field] = value
                break  # matched this field; move to the next one

        return changes

    # ---------------------------------------------------------

    def _extract_changes_with_llm(self, question: str, applicant: dict) -> dict:
        """
        Fallback extraction for what-if questions the regex heuristic
        couldn't confidently parse. Asks the LLM to return the changed
        fields as strict JSON, using only field names that exist on
        the applicant. Never raises — any failure (bad JSON, empty
        response, LLM error) simply returns {}, which the caller
        treats as "could not determine what to change."
        """

        known_fields = {
            k: applicant[k] for k in self.SIM_FIELD_SYNONYMS.keys() if k in applicant
        }

        prompt = f"""
You are a Structured Change Extractor for a credit-simulation system.

Given a user's "what if" question and the applicant's current field
values, extract ONLY the fields the user wants changed, together with
their NEW numeric value.

Valid fields and current values:
{json.dumps(known_fields, indent=2)}

Rules:
- Return ONLY valid JSON. No explanation. No markdown code fences.
- Keys must be exactly one of the valid field names shown above.
- Values must be plain numbers — no "$", no commas, and convert a "k"
  suffix to thousands (e.g. "150k" -> 150000).
- Only include fields the question actually asks to change.
- If the question does not specify any concrete new value, return {{}}.

Question:
{question}

JSON:
"""

        try:
            raw = self.response_generator.generate(prompt)
        except Exception:
            return {}

        cleaned = (raw or "").strip()

        if cleaned.startswith("```"):
            first_newline = cleaned.find("\n")
            if first_newline != -1:
                cleaned = cleaned[first_newline + 1:]
            if cleaned.rstrip().endswith("```"):
                cleaned = cleaned.rstrip()[:-3]
        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            return {}

        if not isinstance(parsed, dict):
            return {}

        result = {}
        for key, value in parsed.items():
            if key not in self.SIM_FIELD_SYNONYMS:
                continue
            try:
                result[key] = float(value)
            except (TypeError, ValueError):
                continue

        return result

    # ---------------------------------------------------------

    def _extract_changes(self, question: str, applicant: dict) -> dict:
        """
        Two-stage change extraction: try the free heuristic first,
        only pay for an LLM call if it finds nothing.
        """

        changes = self._extract_changes_heuristic(question, applicant)

        if changes:
            return changes

        return self._extract_changes_with_llm(question, applicant)

    # ---------------------------------------------------------

    def _run_simulation_pipeline(
        self,
        question: str,
        applicant: Optional[dict],
        simulation_changes: Optional[dict],
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Execute the Simulation pipeline. Reached either directly via
        /api/v1/simulate (structured changes always supplied there),
        or via /api/v1/query once the Intent Router has classified a
        chat question as SIMULATION — the "what if annual income
        increases to 150000?" path.

        If applicant is None, falls back to the session's stored
        applicant. If simulation_changes is empty, parses the question
        text into structured changes via _extract_changes().
        """

        if applicant is None:

            session = self.session_manager.get_session(session_id=session_id)

            if session is None or session.get("applicant") is None:
                raise ValueError(
                    "No applicant supplied and no active prediction "
                    "session exists to simulate against. Run a "
                    "prediction first, then ask the what-if question."
                )

            applicant = session["applicant"]

        changes = simulation_changes or {}

        if not changes:
            changes = self._extract_changes(question, applicant)

        if not changes:
            raise ValueError(
                "Could not identify which value(s) to change from that "
                "question. Try being specific, e.g. 'what if annual "
                "income increases to 150000?'"
            )

        simulation = self.simulation_engine.simulate(
            applicant=applicant,
            changes=changes,
        )

        prompt = self.simulation_prompt.build_prompt(
            user_question=question,
            simulation_result=simulation,
        )

        answer = self.response_generator.generate(prompt)

        result = {
            "intent": "SIMULATION",
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
            interaction=result,
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
        relevant policy chunks using the raw question as the query,
        then answer using GeneralPrompt.

        Reached either directly via /api/v1/knowledge (the standalone
        Policy Knowledge page — plain RAG, no prediction context), or
        via /api/v1/query once the Intent Router has classified a
        post-prediction chat question as KNOWLEDGE.
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
            "intent": "KNOWLEDGE",
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
            interaction=result,
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
        question. Uses GeneralPrompt with an empty document set.
        """

        prompt = self.general_prompt.build(
            query=question,
            retrieved_documents=[],
        )

        answer = self.response_generator.generate(prompt)

        result = {
            "intent": "GENERAL",
            "prompt": prompt,
            "answer": answer,
        }

        self.session_manager.save(
            interaction=result,
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

    print("=" * 80)
    print("STEP 1 — Run a prediction (establishes the session)")
    print("=" * 80)

    result = orchestrator.explain(
        applicant=applicant,
        user_question="Why was this applicant rejected?",
        session_id="demo-session",
    )
    print("Prediction:", result["prediction"]["prediction"])

    print()
    print("=" * 80)
    print("STEP 2 — Ask follow-ups through process_request(), letting the")
    print("Intent Router decide what kind of question each one is, with NO")
    print("applicant resupplied — exactly how the post-prediction chat works")
    print("=" * 80)

    followups = [
        "Why was this applicant rejected?",
        "What if annual income increases to 150000?",
        "What is the maximum allowed DTI?",
    ]

    for q in followups:
        r = orchestrator.process_request(
            user_question=q,
            session_id="demo-session",
        )
        print(f"\nQuestion: {q}")
        print(f"Detected intent: {r['intent']}")
        print(f"Answer preview: {r['answer'][:150]}...")