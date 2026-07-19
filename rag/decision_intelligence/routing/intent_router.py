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
User Query -> Routing Prompt -> LLM -> JSON Parsing ->
Intent Validation -> Intent Object

Fixes applied in this version
------------------------------
1. LLM responses are stripped of Markdown code fences
   (```json ... ``` or ``` ... ```) before json.loads()
   is attempted. LLMs add these constantly despite being
   told not to in the routing prompt, and the previous
   version had no defense against it, silently falling
   back to UNKNOWN on every fenced response.

2. Confidence is coerced to float defensively, since a
   malformed LLM response could return it as a string.

3. classify() now logs (via a returned "raw_response" field
   in debug mode) what the LLM actually said when parsing
   fails, so failures are debuggable instead of silently
   becoming UNKNOWN with no trace.

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

    def __init__(self, debug: bool = False):
        """
        Parameters
        ----------
        debug : bool
            When True, classify() includes the raw LLM
            response and the cleaned text in its return
            value, to help diagnose misclassification.
        """

        self.llm = GeminiService()

        self.debug = debug

    # ---------------------------------------------------------

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """
        Remove Markdown code fences an LLM may wrap its
        JSON response in, e.g.:

```json
            {"intent": "DECISION", "confidence": 0.9}
```

        Returns the cleaned text, stripped of leading/trailing
        whitespace.
        """

        if text is None:
            return ""

        cleaned = text.strip()

        if cleaned.startswith("```"):

            # Drop the opening fence, optionally with a language tag
            # like ```json, then drop a trailing ``` if present.
            first_newline = cleaned.find("\n")

            if first_newline != -1:
                cleaned = cleaned[first_newline + 1:]

            if cleaned.rstrip().endswith("```"):
                cleaned = cleaned.rstrip()[:-3]

        return cleaned.strip()

    # ---------------------------------------------------------

    def classify(
        self,
        current_query: str,
        conversation_history=None,
    ) -> dict:
        """
        Classify user intent.

        Parameters
        ----------
        current_query : str

        conversation_history : list | None

        Returns
        -------
        dict

        {
            "intent": Intent,
            "confidence": float,
        }

        (plus "raw_response" / "cleaned_response" when
        self.debug is True)
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

        cleaned_response = self._strip_code_fences(response)

        # ------------------------------------
        # Parse JSON
        # ------------------------------------

        try:

            result = json.loads(cleaned_response)

        except Exception:

            fallback = {
                "intent": Intent.UNKNOWN,
                "confidence": 0.0,
            }

            if self.debug:
                fallback["raw_response"] = response
                fallback["cleaned_response"] = cleaned_response

            return fallback

        # ------------------------------------
        # Extract values
        # ------------------------------------

        intent_value = result.get("intent", "UNKNOWN")

        confidence = result.get("confidence", 0.0)

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        # ------------------------------------
        # Validate Intent
        # ------------------------------------

        try:

            intent = Intent[intent_value]

        except Exception:

            intent = Intent.UNKNOWN

        output = {
            "intent": intent,
            "confidence": confidence,
        }

        if self.debug:
            output["raw_response"] = response
            output["cleaned_response"] = cleaned_response

        return output


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":

    router = IntentRouter(debug=True)

    history = [
        {"role": "user", "message": "Why was this loan rejected?"},
        {"role": "assistant", "message": "The DTI ratio exceeded policy."},
    ]

    result = router.classify(
        current_query="What if annual income becomes 80000?",
        conversation_history=history,
    )

    print("=" * 80)
    print("INTENT ROUTER")
    print("=" * 80)

    print(result)