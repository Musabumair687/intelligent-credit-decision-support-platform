"""
gemini_service.py

Purpose
-------
Handles all communication with the Groq API.

Gemini is used only for embeddings.

This service is responsible only for text generation.

Author
------
Intelligent Credit Decision Support Platform
"""

from openai import OpenAI

from rag.config import (
    GROQ_API_KEY,
    LLM_MODEL,
)


class GeminiService:
    """
    Wrapper around the Groq API.

    The class name remains GeminiService so the
    existing project imports do not need to change.
    """

    def __init__(self):
        """
        Initialize the Groq client.
        """

        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY not found in config.py"
            )

        self.client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )

    # ---------------------------------------------------------

    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a response from Groq.
        """

        try:

            response = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.2,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:

            return f"Groq API Error: {e}"

    # ---------------------------------------------------------

    def generate_stream(
        self,
        prompt: str,
    ):
        """
        Stream Groq responses.
        """

        try:

            stream = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.2,
                stream=True,
            )

            for chunk in stream:

                if (
                    chunk.choices
                    and chunk.choices[0].delta.content
                ):
                    yield chunk.choices[0].delta.content

        except Exception as e:

            yield f"Groq API Error: {e}"


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

    answer = llm.generate(prompt)

    print("\n" + "=" * 80)
    print("GROQ RESPONSE")
    print("=" * 80)
    print(answer)