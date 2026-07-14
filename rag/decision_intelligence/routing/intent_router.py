"""
intent_router.py

Purpose
-------
Routes every incoming user query to the
appropriate Decision Intelligence pipeline.

The router uses the LLM to classify the
user intent.

The router NEVER answers the user.

It ONLY returns the detected intent.

Pipeline
--------
User Query
      ↓
Routing Prompt
      ↓
Groq LLM
      ↓
JSON Parsing
      ↓
Intent Validation
      ↓
Intent Object

Author
------
Intelligent Credit Decision Support Platform
"""

import json

from rag.LLM.gemini_service import GeminiService

from rag.decision_intelligence.routing.routing_prompt import (
    build_routing_prompt,
)

from rag.decision_intelligence.routing.intent_schema import (
    Intent,
)


class IntentRouter:
    """
    LLM-based Intent Router.
    """

    def __init__(self):
        """
        Initialize the router.
        """

        self.llm = GeminiService()

    # ---------------------------------------------------------

    def classify(
        self,
        current_query: str,
        conversation_history=None,
    ):
        """
        Classify user intent.

        Parameters
        ----------
        current_query : str

        conversation_history : list

        Returns
        -------
        dict

        {
            "intent": Intent,
            "confidence": float
        }
        """

        if conversation_history is None:

            conversation_history = []

        # ------------------------------------
        # Build Routing Prompt
        # ------------------------------------

        prompt = build_routing_prompt(

            conversation_history=conversation_history,

            current_query=current_query,

        )

        # ------------------------------------
        # Call LLM
        # ------------------------------------

        response = self.llm.generate(prompt)

        # ------------------------------------
        # Parse JSON
        # ------------------------------------

        try:

            result = json.loads(response)

        except Exception:

            return {

                "intent": Intent.UNKNOWN,

                "confidence": 0.0,

            }

        # ------------------------------------
        # Extract values
        # ------------------------------------

        intent = result.get(

            "intent",

            "UNKNOWN",

        )

        confidence = result.get(

            "confidence",

            0.0,

        )

        # ------------------------------------
        # Validate Intent
        # ------------------------------------

        try:

            intent = Intent[intent]

        except Exception:

            intent = Intent.UNKNOWN

        return {

            "intent": intent,

            "confidence": confidence,

        }


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":

    router = IntentRouter()

    history = [

        {

            "role": "user",

            "message": "Why was this loan rejected?"

        },

        {

            "role": "assistant",

            "message": "The DTI ratio exceeded policy."

        }

    ]

    result = router.classify(

        current_query="What if annual income becomes 80000?",

        conversation_history=history,

    )

    print("=" * 80)
    print("INTENT ROUTER")
    print("=" * 80)

    print(result)