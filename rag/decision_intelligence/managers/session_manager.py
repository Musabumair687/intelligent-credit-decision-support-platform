
"""
session_manager.py

Purpose
-------
Manages the active loan application session for the
Decision Intelligence module.

The Session Manager acts as a temporary memory that
stores all information related to the currently
processed loan application.

The stored session includes:

- Applicant information
- ML prediction
- Prediction probability
- SHAP explanation
- Retrieved RAG documents
- Suggested questions
- Conversation history
- Additional metadata

Other modules such as the Context Manager,
Suggestion Generator, Simulation Engine and
Orchestrator access the current loan session
through this manager.

Author
------
Intelligent Credit Decision Support Platform
"""


class SessionManager:
    """
    Stores and manages the current loan application session.
    """

    def __init__(self):
        """
        Initialize an empty session.
        """

        self.current_session = None

    def create_session(
        self,
        applicant: dict,
        prediction: str,
        probability: float,
        shap_values: dict,
    ):
        """
        Create a new loan session.

        Parameters
        ----------
        applicant : dict
            Applicant information.

        prediction : str
            Model prediction.

        probability : float
            Prediction confidence.

        shap_values : dict
            SHAP feature contributions.
        """

        self.current_session = {

            "applicant": applicant,

            "prediction": prediction,

            "probability": probability,

            "shap_values": shap_values,

            "retrieved_documents": [],

            "suggested_questions": [],

            "conversation_history": [],

            "metadata": {},

        }

    def get_session(self):
        """
        Return the current session.

        Returns
        -------
        dict
        """

        return self.current_session

    def update_session(
        self,
        key: str,
        value,
    ):
        """
        Update a single field inside the session.

        Parameters
        ----------
        key : str

        value
        """

        if self.current_session is None:

            raise ValueError("No active session exists.")

        self.current_session[key] = value

    def add_message(
        self,
        role: str,
        message: str,
    ):
        """
        Store a conversation message.

        Parameters
        ----------
        role : str
            user or assistant.

        message : str
            Conversation text.
        """

        if self.current_session is None:

            raise ValueError("No active session exists.")

        self.current_session["conversation_history"].append(

            {

                "role": role,

                "message": message,

            }

        )

    def clear_session(self):
        """
        Remove the active session.
        """

        self.current_session = None


if __name__ == "__main__":

    manager = SessionManager()

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

    manager.create_session(

        applicant=applicant,

        prediction="Charged Off",

        probability=0.81,

        shap_values=shap,

    )

    manager.add_message(

        role="user",

        message="Why was this applicant rejected?",

    )

    manager.add_message(

        role="assistant",

        message="The applicant has a high debt-to-income ratio.",

    )

    print(manager.get_session())