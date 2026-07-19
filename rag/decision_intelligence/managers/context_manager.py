"""
context_manager.py

Purpose
-------
Builds clean, structured context for the Decision
Intelligence module from an active session.

Different tasks require different context:

Decision Explanation
    • Applicant Information
    • Prediction
    • Repayment / Default Probability
    • SHAP Explanation

Knowledge Question
    • Retrieved Documents
    • Conversation History

Simulation
    • Applicant Information
    • Prediction
    • SHAP Explanation

The Context Manager does NOT create prompts and does
NOT own session storage — it reads from whichever
SessionManager instance is handed to it, so the same
session store used by the Orchestrator is the one this
class reads from (previously, ContextManager created
its own separate SessionManager instance, so it could
never see any session created by the Orchestrator).

Author
------
Intelligent Credit Decision Support Platform
"""

from typing import Optional

from rag.decision_intelligence.managers.session_manager import (
    SessionManager,
)


class ContextManager:
    """
    Builds structured context from an active session.
    """

    def __init__(self, session_manager: Optional[SessionManager] = None):
        """
        Parameters
        ----------
        session_manager : SessionManager | None
            Shared SessionManager instance. If not supplied,
            a new (empty) one is created — mainly useful for
            standalone testing of this module.
        """

        self.session_manager = session_manager or SessionManager()

    # ---------------------------------------------------------

    def _get_session_or_raise(self, session_id: Optional[str]) -> dict:

        session = self.session_manager.get_session(session_id=session_id)

        if session is None:
            raise ValueError("No active session found.")

        return session

    # ---------------------------------------------------------

    def build_prediction_context(
        self,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Build context for prediction explanation.

        Returns
        -------
        dict
        """

        session = self._get_session_or_raise(session_id)

        return {
            "applicant": session["applicant"],
            "prediction": session["prediction"],
            "repayment_probability": session["repayment_probability"],
            "default_probability": session["default_probability"],
            "shap_explanation": session["shap_explanation"],
            "conversation_history": session["conversation_history"],
        }

    # ---------------------------------------------------------

    def build_rag_context(
        self,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Build context for knowledge retrieval.

        Returns
        -------
        dict
        """

        session = self._get_session_or_raise(session_id)

        return {
            "retrieved_documents": session["retrieved_documents"],
            "conversation_history": session["conversation_history"],
        }

    # ---------------------------------------------------------

    def build_simulation_context(
        self,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Build context for what-if simulation.

        Returns
        -------
        dict
        """

        session = self._get_session_or_raise(session_id)

        return {
            "applicant": session["applicant"],
            "prediction": session["prediction"],
            "repayment_probability": session["repayment_probability"],
            "default_probability": session["default_probability"],
            "shap_explanation": session["shap_explanation"],
        }


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":

    session_manager = SessionManager()

    applicant = {
        "loan_amount": 25000,
        "annual_income": 50000,
        "dti": 28,
        "grade": "B3",
    }

    session_manager.create_session(
        applicant=applicant,
        prediction="Charged Off",
        repayment_probability=0.19,
        default_probability=0.81,
        shap_explanation=None,
        session_id="demo",
    )

    session_manager.update_session(
        key="retrieved_documents",
        value=[
            "DTI should remain below 35%.",
            "Income verification is mandatory.",
        ],
        session_id="demo",
    )

    session_manager.add_message(
        role="user",
        message="Why was this loan rejected?",
        session_id="demo",
    )

    context = ContextManager(session_manager=session_manager)

    print("=" * 80)
    print("Prediction Context")
    print("=" * 80)
    print(context.build_prediction_context(session_id="demo"))

    print()

    print("=" * 80)
    print("RAG Context")
    print("=" * 80)
    print(context.build_rag_context(session_id="demo"))

    print()

    print("=" * 80)
    print("Simulation Context")
    print("=" * 80)
    print(context.build_simulation_context(session_id="demo"))