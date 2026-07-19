"""
session_manager.py

Purpose
-------
Manages loan application sessions for the
Decision Intelligence module.

The Session Manager acts as memory that stores
all information related to one or more loan
applications currently being processed.

Each session is keyed by a session_id so that
multiple concurrent users (or multiple browser
tabs / requests) do not overwrite each other's
state. If no session_id is supplied, a default
single-user session is used, which keeps local
testing and the Streamlit demo simple.

The stored session includes:

- Applicant information
- ML prediction
- Repayment probability
- Default probability
- SHAP explanation
- Retrieved RAG documents
- Suggested questions
- Conversation history
- Additional metadata

Other modules such as the Context Manager,
Suggestion Generator, Simulation Engine and
Orchestrator access session state through this
manager.

Fix applied in this version
----------------------------
add_message() previously raised ValueError if no session existed
yet for the given session_id. But save() already auto-creates a
minimal session shell when one doesn't exist. This inconsistency
meant that any pipeline calling add_message() BEFORE save() — which
is exactly what _run_simulation_pipeline, _run_knowledge_pipeline,
and _run_general_pipeline in orchestrator.py all do — would throw
a hard error for any session_id that hadn't already been created
via a prior /decision call (e.g. Swagger's leftover placeholder
"string", or any brand-new simulation/knowledge/general question
that is a user's very first message). add_message() now auto-
creates the same minimal session shell as save() if needed, so the
simulation, knowledge, and general pipelines all work correctly
even as someone's very first request in a session.

Author
------
Intelligent Credit Decision Support Platform
"""

from typing import Optional


DEFAULT_SESSION_ID = "default"


def _blank_session(session_id: str) -> dict:
    """
    Shape of a freshly-created session with no prediction data
    yet attached — used both by create_session() (with real data
    filled in afterward) and by the auto-create paths in
    add_message() / save() / update_session().
    """

    return {
        "session_id": session_id,
        "applicant": None,
        "prediction": None,
        "repayment_probability": None,
        "default_probability": None,
        "shap_explanation": None,
        "retrieved_documents": [],
        "suggested_questions": [],
        "conversation_history": [],
        "metadata": {},
    }


class SessionManager:
    """
    Stores and manages one or more loan application sessions.
    """

    def __init__(self):
        """
        Initialize an empty session store.
        """

        self.sessions: dict = {}

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------

    def _resolve_id(self, session_id: Optional[str]) -> str:
        """
        Resolve a session_id, falling back to the
        default single-user session when none is given.
        """

        return session_id if session_id else DEFAULT_SESSION_ID

    def _ensure_session(self, session_id: str) -> dict:
        """
        Return the session for session_id, creating a blank shell
        for it first if it doesn't exist yet. Centralizes the
        auto-create behavior so every method below (add_message,
        save, update_session) behaves consistently instead of some
        raising and others silently creating, as before.
        """

        if session_id not in self.sessions:
            self.sessions[session_id] = _blank_session(session_id)

        return self.sessions[session_id]

    # ---------------------------------------------------------
    # Create / Get / Update
    # ---------------------------------------------------------

    def create_session(
        self,
        applicant: dict,
        prediction: str,
        repayment_probability: float,
        default_probability: float,
        shap_explanation=None,
        session_id: Optional[str] = None,
    ):
        """
        Create or overwrite a loan session with full prediction data.

        Parameters
        ----------
        applicant : dict
            Applicant information.

        prediction : str
            Model prediction ("Approved" / "Rejected").

        repayment_probability : float

        default_probability : float

        shap_explanation : shap.Explanation | None
            Full SHAP explanation object for this prediction.

        session_id : str | None
            Identifier for this session. Defaults to a
            single shared session if not provided.
        """

        sid = self._resolve_id(session_id)

        self.sessions[sid] = {
            "session_id": sid,
            "applicant": applicant,
            "prediction": prediction,
            "repayment_probability": repayment_probability,
            "default_probability": default_probability,
            "shap_explanation": shap_explanation,
            "retrieved_documents": [],
            "suggested_questions": [],
            "conversation_history": [],
            "metadata": {},
        }

        return self.sessions[sid]

    # ---------------------------------------------------------

    def get_session(
        self,
        session_id: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Return a session, or None if it does not exist.

        Deliberately does NOT auto-create — callers that need to
        check "does a real prediction session already exist"
        (e.g. the simulation applicant-fallback logic in
        orchestrator.py) rely on this returning None when nothing
        has been created yet.
        """

        sid = self._resolve_id(session_id)

        return self.sessions.get(sid)

    # ---------------------------------------------------------

    def update_session(
        self,
        key: str,
        value,
        session_id: Optional[str] = None,
    ):
        """
        Update a single field inside a session. Auto-creates a
        blank session shell first if one doesn't exist yet, for
        the same reason described in the module docstring.
        """

        sid = self._resolve_id(session_id)

        session = self._ensure_session(sid)

        session[key] = value

    # ---------------------------------------------------------

    def save(
        self,
        interaction: dict,
        session_id: Optional[str] = None,
    ):
        """
        Append a completed interaction (decision, simulation,
        or general Q&A result) to the session's conversation
        history and metadata log. Auto-creates a blank session
        shell if one doesn't exist yet.
        """

        sid = self._resolve_id(session_id)

        session = self._ensure_session(sid)

        session["metadata"].setdefault("interactions", []).append(interaction)

    # ---------------------------------------------------------

    def add_message(
        self,
        role: str,
        message: str,
        session_id: Optional[str] = None,
    ):
        """
        Store a conversation message ("user" or "assistant").

        Fix: now auto-creates a blank session shell if one doesn't
        exist yet, matching save()'s behavior, instead of raising
        ValueError. This is what was breaking /api/v1/simulate and
        /api/v1/knowledge whenever they were the first call made
        for a given session_id.
        """

        sid = self._resolve_id(session_id)

        session = self._ensure_session(sid)

        session["conversation_history"].append(
            {
                "role": role,
                "message": message,
            }
        )

    # ---------------------------------------------------------

    def clear_session(
        self,
        session_id: Optional[str] = None,
    ):
        """
        Remove a session.
        """

        sid = self._resolve_id(session_id)

        self.sessions.pop(sid, None)


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":

    manager = SessionManager()

    # Prove add_message() no longer requires a pre-existing session
    # (this used to raise ValueError before the fix).
    manager.add_message(
        role="user",
        message="What if annual income increases to 95000?",
        session_id="brand-new-session",
    )

    print("add_message on a brand-new session_id succeeded:")
    print(manager.get_session(session_id="brand-new-session"))

    print()

    # Full flow, same as before.
    applicant = {
        "loan_amnt": 25000,
        "annual_inc": 50000,
        "dti": 28,
        "sub_grade": "B3",
    }

    manager.create_session(
        applicant=applicant,
        prediction="Rejected",
        repayment_probability=0.19,
        default_probability=0.81,
        shap_explanation=None,
        session_id="demo-user-1",
    )

    manager.add_message(
        role="user",
        message="Why was this applicant rejected?",
        session_id="demo-user-1",
    )

    manager.add_message(
        role="assistant",
        message="The applicant has a high debt-to-income ratio.",
        session_id="demo-user-1",
    )

    manager.save(
        interaction={"type": "decision", "answer": "..."},
        session_id="demo-user-1",
    )

    print("Full session after create_session + messages + save:")
    print(manager.get_session(session_id="demo-user-1"))