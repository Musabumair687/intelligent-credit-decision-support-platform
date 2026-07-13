"""
context_manager.py

Purpose
-------
Builds clean context for the Decision Intelligence module.

The Context Manager reads the active loan session from the
Session Manager and prepares only the information required
for the current task.

Different tasks require different context.

Examples
--------
Decision Explanation
    • Applicant Information
    • Prediction
    • Probability
    • SHAP Values

Knowledge Question
    • Retrieved Documents
    • Conversation History

Simulation
    • Applicant Information
    • Prediction
    • SHAP Values

The Context Manager does NOT create prompts.
It only prepares structured context.

Author
------
Intelligent Credit Decision Support Platform
"""

from rag.decision_intelligence.managers.session_manager import SessionManager


class ContextManager:
    """
    Builds structured context from the active session.
    """

    def __init__(self):
        """
        Initialize the Context Manager.
        """

        self.session_manager = SessionManager()

    def build_prediction_context(self):
        """
        Build context for prediction explanation.

        Returns
        -------
        dict
        """

        session = self.session_manager.get_session()

        if session is None:

            raise ValueError("No active session found.")

        return {

            "applicant": session["applicant"],

            "prediction": session["prediction"],

            "probability": session["probability"],

            "shap_values": session["shap_values"],

            "conversation_history": session["conversation_history"],

        }

    def build_rag_context(self):
        """
        Build context for knowledge retrieval.

        Returns
        -------
        dict
        """

        session = self.session_manager.get_session()

        if session is None:

            raise ValueError("No active session found.")

        return {

            "retrieved_documents": session["retrieved_documents"],

            "conversation_history": session["conversation_history"],

        }

    def build_simulation_context(self):
        """
        Build context for what-if simulation.

        Returns
        -------
        dict
        """

        session = self.session_manager.get_session()

        if session is None:

            raise ValueError("No active session found.")

        return {

            "applicant": session["applicant"],

            "prediction": session["prediction"],

            "probability": session["probability"],

            "shap_values": session["shap_values"],

        }


if __name__ == "__main__":

    session_manager = SessionManager()

    applicant = {

        "loan_amount": 25000,

        "annual_income": 50000,

        "dti": 28,

        "grade": "B3",

    }

    shap = {

        "annual_income": -0.25,

        "dti": 0.42,

        "grade": 0.19,

    }

    session_manager.create_session(

        applicant=applicant,

        prediction="Charged Off",

        probability=0.81,

        shap_values=shap,

    )

    session_manager.update_session(

        "retrieved_documents",

        [

            "DTI should remain below 35%.",

            "Income verification is mandatory.",

        ]

    )

    session_manager.add_message(

        role="user",

        message="Why was this loan rejected?",

    )

    context = ContextManager()

    context.session_manager = session_manager

    print("=" * 80)
    print("Prediction Context")
    print("=" * 80)
    print(context.build_prediction_context())

    print()

    print("=" * 80)
    print("RAG Context")
    print("=" * 80)
    print(context.build_rag_context())

    print()

    print("=" * 80)
    print("Simulation Context")
    print("=" * 80)
    print(context.build_simulation_context())