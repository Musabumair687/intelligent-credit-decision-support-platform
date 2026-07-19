"""
gemini_service.py

Purpose
-------
Handles all communication with the Groq API for text generation.

The class name remains GeminiService so existing project imports
do not need to change; Gemini itself is used only for embeddings
elsewhere in the project.

Fix applied in this version
----------------------------
generate() previously caught its own exceptions and returned a
plain string like "Groq API Error: <details>" instead of raising.
This meant response_generator.py's own try/except could never
detect a real API failure — the error string was indistinguishable
from a genuine answer, got treated as valid output, and would be
saved into session/conversation history as if it were a real
explanation. generate() now re-raises, so ResponseGenerator (the
single intended place for user-facing error handling) is the only
place that decides what the user sees on failure.

Author
------
Intelligent Credit Decision Support Platform
"""

from openai import OpenAI

from rag.config import GROQ_API_KEY, LLM_MODEL


class GeminiService:
    """
    Wrapper around the Groq API (OpenAI-compatible endpoint).
    """

    def __init__(self):

        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in config.py")

        self.client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )

    # ---------------------------------------------------------

    def generate(self, prompt: str) -> str:
        """
        Generate a response from Groq.

        Raises
        ------
        RuntimeError
            If the Groq API call fails for any reason. Callers
            (specifically ResponseGenerator) are responsible for
            catching this and deciding what to show the user.
        """

        try:

            response = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            content = response.choices[0].message.content

            if not content:
                raise RuntimeError("Groq returned an empty completion.")

            return content.strip()

        except Exception as error:
            raise RuntimeError(f"Groq API call failed: {error}") from error

    # ---------------------------------------------------------

    def generate_stream(self, prompt: str):
        """
        Stream Groq responses.

        Yields chunks of generated text. On failure, raises
        RuntimeError rather than silently yielding an error string
        disguised as content — same reasoning as generate() above.
        """

        try:

            stream = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as error:
            raise RuntimeError(f"Groq streaming call failed: {error}") from error


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":

    print("=" * 80)
    print("Groq Model :", LLM_MODEL)
    print("=" * 80)

    llm = GeminiService()

    prompt = """
You are an AI Banking Assistant.

Question:
What is Debt-to-Income Ratio?
"""

    try:
        answer = llm.generate(prompt)
        print("\n" + "=" * 80)
        print("GROQ RESPONSE")
        print("=" * 80)
        print(answer)
    except RuntimeError as error:
        print("\nGROQ CALL FAILED:", error)