
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

7. Decision follow-up questions no longer re-run the ML model.
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

8. Simulation follow-ups asked in free text (e.g. "what if annual
   income increases to 150000?") are now parsed into the structured
   {field: new_value} dict simulation_engine.simulate() expects, via
   _extract_changes(): a fast regex/synonym heuristic first, falling
   back to a small LLM extraction call only if the heuristic finds
   nothing. This keeps the common, clearly-phrased case instant and
   free, and only pays the extra LLM round-trip for ambiguous phrasing.

9. FIXED — _extract_changes_heuristic now supports:
   - ALL applicant fields (sub_grade, home_ownership, verification_status,
     purpose, initial_list_status, application_type, pub_rec,
     pub_rec_bankruptcies, term, etc.)
   - Percentage changes with OR without % symbol
     ("increase by 30%", "increase by 30 percent")
   - Categorical value changes ("subgrade become A1",
     "home ownership is RENT")
   - Typo-tolerant synonyms ("bankcrupcy" -> pub_rec_bankruptcies)

10. FIXED — _extract_changes_with_llm now accepts ANY field present on
    the applicant dict, not just a hardcoded subset. It also instructs
    the LLM to convert percentages into absolute numeric values.

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
    # Longer synonyms are checked before shorter ones.
    # -------------------------------------------------------
    SIM_FIELD_SYNONYMS = {
        "annual_inc": ["annual income", "yearly income", "gross income", "income", "salary"],
        "dti": ["debt-to-income", "debt to income", "dti"],
        "loan_amnt": ["loan amount", "amount", "principal", "loan size"],
        "revol_util": ["revolving utilization", "credit utilization", "utilization", "revol util"],
        "revol_bal": ["revolving balance", "credit card balance", "balance", "revol bal"],
        "emp_length": ["employment length", "years employed", "employment", "emp length"],
        "int_rate": ["interest rate", "rate", "apr"],
        "open_acc": ["open accounts", "open credit lines", "open acc"],
        "total_acc": ["total accounts", "total credit lines", "total acc"],
        "mort_acc": ["mortgage accounts", "mortgages", "mort acc"],
        "sub_grade": ["sub grade", "subgrade", "grade"],
        "home_ownership": ["home ownership", "homeownership", "housing", "home"],
        "verification_status": ["verification status", "verification", "verified status", "verified"],
        "purpose": ["purpose", "loan purpose", "reason"],
        "initial_list_status": ["initial list status", "list status", "initial status"],
        "application_type": ["application type", "app type", "application"],
        "pub_rec": ["public records", "pub rec", "public rec"],
        "pub_rec_bankruptcies": ["public record bankruptcies", "bankruptcies", "bankruptcy", "pub rec bankruptcies", "bankcrupcy", "bankrupcy"],
        "term": ["term", "loan term", "duration", "tenor"],
    }

    # Known valid categorical values for heuristic matching
    CATEGORICAL_VALUES = {
        "sub_grade": [
            "A1", "A2", "A3", "A4", "A5",
            "B1", "B2", "B3", "B4", "B5",
            "C1", "C2", "C3", "C4", "C5",
            "D1", "D2", "D3", "D4", "D5",
            "E1", "E2", "E3", "E4", "E5",
            "F1", "F2", "F3", "F4", "F5",
            "G1", "G2", "G3", "G4", "G5",
        ],
        "home_ownership": ["MORTGAGE", "RENT", "OWN", "ANY", "NONE", "OTHER"],
        "verification_status": ["Verified", "Source Verified", "Not Verified"],
        "purpose": [
            "debt_consolidation", "credit_card", "home_improvement",
            "major_purchase", "small_business", "car", "medical",
            "moving", "vacation", "house", "wedding",
            "renewable_energy", "educational", "other"
        ],
        "initial_list_status": ["w", "f"],
        "application_type": ["INDIVIDUAL", "JOINT", "DIRECT_PAY"],
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
        Fast, free, zero-latency extraction of {field: new_value} from
        a what-if question. Handles numeric (absolute & percentage) and
        categorical changes.

        Supported patterns:
            "annual income increases to 95,000"      -> absolute
            "annual income increases by 30%"         -> percentage
            "annual income increases by 30 percent"  -> percentage
            "subgrade become A1"                     -> categorical
            "loan amount increase by 1 percent"      -> percentage
            "bankruptcy become 1"                    -> absolute numeric
        """
        text = question.lower()
        changes = {}

        # Clause breakers — truncate window so "bankcrupcy become 1 AND loan amount..."
        # doesn't let the bankcrupcy regex greedily match the 10% from the loan clause
        CLAUSE_BREAKERS = [
            " and ", " but ", " or ", " then ", " also ", " while ",
            " whereas ", " plus ", " along with ", " together with ",
        ]

        for field, synonyms in self.SIM_FIELD_SYNONYMS.items():
            if field not in applicant:
                continue

            current_value = applicant[field]
            is_numeric = isinstance(current_value, (int, float))
            is_categorical = field in self.CATEGORICAL_VALUES

            for synonym in sorted(synonyms, key=len, reverse=True):
                idx = text.find(synonym)
                if idx == -1:
                    continue

                # Window of text right after the synonym
                window = text[idx + len(synonym): idx + len(synonym) + 80]

                # Truncate at first clause boundary so we don't leak into next field
                for breaker in CLAUSE_BREAKERS:
                    bidx = window.find(breaker)
                    if bidx != -1:
                        window = window[:bidx]
                        break

                matched = False

                # ==================================================
                # Pattern 1: Percentage change (numeric fields only)
                # "increase by 30%", "decrease 15 percent", "drop 5 pct"
                # ==================================================
                if is_numeric and not matched:
                    pct_match = re.search(
                        r"(increase|decrease|reduce|lower|raise|improve|drop|fall|rise|up|down)"
                        r"(?:s|d|ing|es|ed)?\s*(?:by|of|to)?\s*"
                        r"([\d][\d,]*(?:\.\d+)?)\s*(%|percent|percentage|pct|pc)",
                        window,
                    )
                    if pct_match:
                        verb = pct_match.group(1)
                        raw_pct = float(pct_match.group(2).replace(",", ""))
                        decrease = verb in {"decrease", "reduce", "lower", "drop", "fall", "down"}
                        new_val = current_value * (1 - raw_pct / 100) if decrease else current_value * (1 + raw_pct / 100)
                        changes[field] = round(new_val, 2)
                        matched = True

                # ==================================================
                # Pattern 2: Absolute numeric value
                # "to 95000", "of 150k", "is 8", "set at $50,000", "become 1"
                # ==================================================
                if is_numeric and not matched:
                    abs_match = re.search(
                        r"(?:to|of|is|was|become|becomes|set to|equals?|at|into)\s*"
                        r"\$?\s?([\d][\d,]*(?:\.\d+)?)\s?(k|thousand)?",
                        window,
                    )
                    if abs_match:
                        raw_number = abs_match.group(1).replace(",", "")
                        value = float(raw_number)
                        if abs_match.group(2):
                            value *= 1000
                        # Safety: skip if value is suspiciously tiny (< 2% of current)
                        if abs(current_value) > 0 and abs(value) < abs(current_value) * 0.02:
                            pass
                        else:
                            changes[field] = value
                            matched = True

                # ==================================================
                # Pattern 3: Categorical value from known list
                # "subgrade become A1", "home ownership is MORTGAGE"
                # ==================================================
                if is_categorical and not matched:
                    for valid_value in self.CATEGORICAL_VALUES[field]:
                        if re.search(rf"\b{re.escape(valid_value.lower())}\b", window):
                            changes[field] = valid_value
                            matched = True
                            break

                # ==================================================
                # Pattern 4: Categorical fallback (any capitalized word)
                # ==================================================
                if not is_numeric and not matched:
                    str_match = re.search(r'["\']?([A-Z][A-Za-z0-9_+-]*)["\']?', window)
                    if str_match:
                        changes[field] = str_match.group(1)
                        matched = True

                if matched:
                    break

        return changes
    # ---------------------------------------------------------

    def _extract_changes_with_llm(self, question: str, applicant: dict) -> dict:
        """
        Fallback extraction for what-if questions the regex heuristic
        couldn't confidently parse. Asks the LLM to return the changed
        fields as strict JSON, using any field name that exists on
        the applicant.
        """

        # Build field descriptions showing current values and types
        field_descriptions = []
        for key, val in applicant.items():
            if isinstance(val, (int, float)):
                field_descriptions.append(f'{key}: {val} (numeric)')
            else:
                field_descriptions.append(f'{key}: "{val}" (categorical)')

        prompt = f"""
You are a Structured Change Extractor for a credit-simulation system.

Given a user's "what if" question and the applicant's current field
values, extract ONLY the fields the user wants changed, together with
their NEW value.

Current applicant fields:
{chr(10).join(field_descriptions)}

Rules:
- Return ONLY valid JSON. No explanation. No markdown code fences.
- Keys must be exactly one of the field names shown above.
- For numeric fields: values must be plain numbers — no "$", no commas.
  Convert a "k" suffix to thousands (e.g. "150k" -> 150000).
  Convert percentages to absolute values (e.g. if current income is 71000
  and user says "increase by 30%", return 92300, not 30).
- For categorical fields: values must be exact strings (e.g. sub_grade: "A1",
  home_ownership: "MORTGAGE", initial_list_status: "w").
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
            if key not in applicant:
                continue
            current = applicant[key]
            if isinstance(current, (int, float)):
                try:
                    result[key] = float(value)
                except (TypeError, ValueError):
                    continue
            else:
                # Categorical: accept string value as-is
                if isinstance(value, str):
                    result[key] = value
                else:
                    result[key] = str(value)
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

# if __name__ == "__main__":

#     orchestrator = Orchestrator()

#     applicant = {
#         "loan_amnt": 12000,
#         "term": "36 months",
#         "int_rate": 13.33,
#         "sub_grade": "B3",
#         "emp_length": "7 years",
#         "home_ownership": "MORTGAGE",
#         "verification_status": "Verified",
#         "annual_inc": 71000,
#         "purpose": "debt_consolidation",
#         "dti": 12,
#         "open_acc": 10,
#         "pub_rec": 0,
#         "revol_bal": 6000,
#         "revol_util": 41,
#         "total_acc": 28,
#         "initial_list_status": "w",
#         "application_type": "INDIVIDUAL",
#         "mort_acc": 2,
#         "pub_rec_bankruptcies": 0,
#     }

#     # ------------------------------------------------------------------
#     # BONUS: Heuristic Parser Self-Test (no ML, no LLM)
#     # ------------------------------------------------------------------
#     print("=" * 80)
#     print("BONUS — Heuristic Parser Self-Test")
#     print("=" * 80)

#     test_queries = [
#         ("annual income +30%", "What if annual income increases by 30 percent?"),
#         ("subgrade A1", "What if subgrade become A1?"),
#         ("multi-field typo", "What if bankcrupcy become 1 and loan amount increase by 10 percent?"),
#         ("dti absolute", "What if dti drops to 8.5?"),
#         ("categorical", "What if home ownership is RENT?"),
#     ]

#     for label, q in test_queries:
#         parsed = orchestrator._extract_changes_heuristic(q, applicant)
#         print(f"\n  [{label}]")
#         print(f"  Query : {q}")
#         print(f"  Parsed: {parsed if parsed else '(nothing — would fall back to LLM)'}")

#     # ------------------------------------------------------------------
#     # Print helpers
#     # ------------------------------------------------------------------
#     def print_decision_result(r, q):
#         intent = r.get("intent", "DECISION")
#         pred = r.get("prediction", {})
#         if isinstance(pred, dict) and "prediction" in pred:
#             pass
#         elif isinstance(pred, dict) and "repayment_probability" in pred:
#             pass
#         else:
#             pred = {}

#         print(f"\n  Question        : {q}")
#         print(f"  Intent          : {intent}")
#         print(f"  Prediction      : {pred.get('prediction', 'N/A')}")
#         print(f"  Repay Prob      : {pred.get('repayment_probability', 'N/A')}")
#         print(f"  Default Prob    : {pred.get('default_probability', 'N/A')}")
#         top = pred.get("top_features", [])[:3]
#         if top:
#             print("  Top 3 Features  :")
#             for f in top:
#                 print(f"    • {f.get('feature', '?'):20s} (importance: {f.get('importance', 0):.4f})")

#     def print_simulation_result(r, q):
#         sim = r.get("simulation", {})
#         orig = sim.get("original", {})
#         new = sim.get("simulation", {})
#         comp = sim.get("comparison", {})

#         print(f"\n  Question        : {q}")
#         print(f"  Intent          : {r.get('intent', 'SIMULATION')}")
#         print(f"  Original        : {orig.get('prediction', 'N/A')} (repay: {orig.get('repayment_probability', 'N/A')})")
#         print(f"  Simulated       : {new.get('prediction', 'N/A')} (repay: {new.get('repayment_probability', 'N/A')})")
#         print(f"  Transition      : {comp.get('decision_transition', 'N/A')}")
#         print(f"  Risk Change     : {comp.get('risk_change', 'N/A')}")

#         changes = sim.get("changes", {})
#         if changes:
#             print("  Feature Changes :")
#             for feat, vals in changes.items():
#                 print(f"    • {feat:20s} {vals.get('old')} → {vals.get('new')} ({vals.get('direction')}, {vals.get('percentage_change')}%)")
#         else:
#             print("  Feature Changes : (none detected)")

#     def print_knowledge_result(r, q):
#         print(f"\n  Question        : {q}")
#         print(f"  Intent          : {r.get('intent', 'KNOWLEDGE')}")
#         ans = r.get("answer", "")
#         print(f"  Answer Preview  : {ans[:250]}...")

#     # ==================================================================
#     # TEST 1 — DECISION: Full prediction
#     # ==================================================================
#     print("\n" + "=" * 80)
#     print("TEST 1 — DECISION: Full prediction + explanation")
#     print("=" * 80)
#     try:
#         r1 = orchestrator.process_request(
#             user_question="Why was this applicant rejected?",
#             applicant=applicant,
#             session_id="test-session",
#         )
#         print_decision_result(r1, "Why was this applicant rejected?")
#     except Exception as e:
#         print(f"  ERROR: {type(e).__name__}: {e}")

#     # ==================================================================
#     # TEST 2 — DECISION: Follow-up (reuses session)
#     # ==================================================================
#     print("\n" + "=" * 80)
#     print("TEST 2 — DECISION: Follow-up (reuses session, no applicant)")
#     print("=" * 80)
#     try:
#         r2 = orchestrator.process_request(
#             user_question="Why is this applicant's debt-to-income ratio important?",
#             applicant=None,
#             session_id="test-session",
#         )
#         print_decision_result(r2, "Why is this applicant's debt-to-income ratio important?")
#     except Exception as e:
#         print(f"  ERROR: {type(e).__name__}: {e}")

#     # ==================================================================
#     # TEST 3 — SIMULATION: Percentage without % symbol
#     # ==================================================================
#     print("\n" + "=" * 80)
#     print("TEST 3 — SIMULATION: Percentage without % symbol")
#     print("=" * 80)
#     try:
#         r3 = orchestrator.process_request(
#             user_question="What if annual income increases by 30 percent?",
#             applicant=applicant,
#             session_id="test-session-3",
#         )
#         print_simulation_result(r3, "What if annual income increases by 30 percent?")
#     except Exception as e:
#         print(f"  ERROR: {type(e).__name__}: {e}")

#     # ==================================================================
#     # TEST 4 — SIMULATION: Categorical change
#     # ==================================================================
#     print("\n" + "=" * 80)
#     print("TEST 4 — SIMULATION: Categorical change (sub_grade)")
#     print("=" * 80)
#     try:
#         r4 = orchestrator.process_request(
#             user_question="What if subgrade become A1?",
#             applicant=applicant,
#             session_id="test-session-4",
#         )
#         print_simulation_result(r4, "What if subgrade become A1?")
#     except Exception as e:
#         print(f"  ERROR: {type(e).__name__}: {e}")

#     # ==================================================================
#     # TEST 5 — SIMULATION: Typo + multi-field + percentage
#     # ==================================================================
#     print("\n" + "=" * 80)
#     print("TEST 5 — SIMULATION: Typo + multi-field + percentage")
#     print("=" * 80)
#     try:
#         r5 = orchestrator.process_request(
#             user_question="What if bankcrupcy become 1 and loan amount increase by 10 percent?",
#             applicant=applicant,
#             session_id="test-session-5",
#         )
#         print_simulation_result(r5, "What if bankcrupcy become 1 and loan amount increase by 10 percent?")
#     except Exception as e:
#         print(f"  ERROR: {type(e).__name__}: {e}")

#     # ==================================================================
#     # TEST 6 — KNOWLEDGE: Bank policy
#     # ==================================================================
#     print("\n" + "=" * 80)
#     print("TEST 6 — KNOWLEDGE: Bank policy question")
#     print("=" * 80)
#     try:
#         r6 = orchestrator.process_request(
#             user_question="What is the maximum allowed debt-to-income ratio?",
#             applicant=None,
#             session_id="test-session-6",
#         )
#         print_knowledge_result(r6, "What is the maximum allowed debt-to-income ratio?")
#     except Exception as e:
#         print(f"  ERROR: {type(e).__name__}: {e}")

#     # ==================================================================
#     print("\n" + "=" * 80)
#     print("ALL TESTS COMPLETE")
#     print("=" * 80)


if __name__ == "__main__":
    # your test code here...
    pass