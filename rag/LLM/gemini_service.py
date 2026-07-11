"""
gemini_service.py

Purpose
-------
Handles all communication with the Gemini API.

Responsibilities
----------------
1. Load Gemini model.
2. Send prompt to Gemini.
3. Return generated response.

This class knows NOTHING about:
- RAG
- Retriever
- ChromaDB
- BM25
- Cross Encoder
- Prompt Builder

It only receives a prompt and returns an answer.
"""

import os

import google.generativeai as genai

from dotenv import load_dotenv


load_dotenv()


class GeminiService:
    """
    Wrapper around Google's Gemini model.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
    ):
        """
        Initialize Gemini.

        Parameters
        ----------
        model_name : str
            Gemini model name.
        """

        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found.")

        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(model_name="gemini-flash-latest")

    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate response from Gemini.

        Parameters
        ----------
        prompt : str

        Returns
        -------
        str
        """

        response = self.model.generate_content(prompt)

        return response.text.strip()


if __name__ == "__main__":

    llm = GeminiService()

    prompt = """
You are an AI assistant.

Question:
What is Debt-to-Income Ratio?
"""

    answer = llm.generate(prompt)

    print("=" * 80)
    print("GEMINI RESPONSE")
    print("=" * 80)
    print(answer)
