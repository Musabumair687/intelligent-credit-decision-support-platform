"""
response_generator.py

Purpose
-------
Generates the final natural language response
using the configured Large Language Model.

This class NEVER:

- Builds prompts
- Retrieves documents
- Runs ML predictions
- Calculates SHAP

It simply forwards a completed prompt
to the LLM service and returns the response.

Pipeline
--------

Completed Prompt
        │
        ▼
Response Generator
        │
        ▼
LLM Service
        │
        ▼
Configured LLM
        │
        ▼
Generated Response
"""

from rag.LLM.gemini_service import GeminiService


class ResponseGenerator:
    """
    Sends completed prompts to the configured LLM.
    """

    def __init__(self):
        """
        Initialize the LLM service.
        """

        self.llm = GeminiService()

    # ---------------------------------------------------------

    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a response from the configured LLM.

        Parameters
        ----------
        prompt : str
            Fully constructed prompt.

        Returns
        -------
        str
            Generated explanation.
        """

        try:

            response = self.llm.generate(prompt)

            if not response:

                return (
                    "The language model returned an empty response."
                )

            return response

        except Exception as error:

            return (
                f"LLM Generation Error: {error}"
            )


# ==========================================================
# Testing
# ==========================================================

if __name__ == "__main__":

    generator = ResponseGenerator()

    prompt = """
You are a Senior Credit Risk Analyst.

Explain why this applicant was rejected.

Prediction:
Rejected

Default Probability:
72.92%

Repayment Probability:
27.08%

Main Risk Factors:
- High Interest Rate
- Loan Amount
- Debt-to-Income Ratio
- Sub Grade

Relevant Banking Policy:
Applications with high borrowing costs and affordability concerns
present elevated repayment risk.

Write a professional explanation.
"""

    response = generator.generate(prompt)

    print("=" * 80)
    print("LLM RESPONSE")
    print("=" * 80)

    print(response)