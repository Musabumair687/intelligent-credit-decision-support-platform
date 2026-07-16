"""
decision_prompt.py

Purpose
-------
Builds the final prompt used for explaining
Machine Learning credit decisions.

The Decision Prompt combines:

1. User Question
2. ML Prediction
3. Prediction Probability
4. SHAP Feature Importance
5. Retrieved Policy Evidence

into a single structured prompt.

This module NEVER performs retrieval.

It ONLY prepares the final prompt.

Author
------
Intelligent Credit Decision Support Platform
"""


class DecisionPrompt:
    """
    Builds the prompt for the AI Credit Decision Assistant.
    """

    def __init__(self):
        pass

    # ---------------------------------------------------------

    def build(
        self,
        user_question: str,
        evidence: dict,
    ) -> str:
        """
        Build the final decision prompt.

        Parameters
        ----------
        user_question : str

        evidence : dict
            Output returned by Retrieval Engine.

        Returns
        -------
        str
            Complete prompt.
        """

        sections = [

            self._system_prompt(),

            self._prediction_section(evidence),

            self._feature_section(evidence),

            self._policy_section(evidence),

            self._question_section(user_question),

            self._instruction_section(),

        ]

        return "\n\n".join(sections)

    # ---------------------------------------------------------

    def _system_prompt(self) -> str:
        """
        AI role definition.
        """

        return """
===========================
SYSTEM
===========================

You are an AI Credit Decision Assistant.

Your job is to explain lending decisions
using BOTH:

• Machine Learning outputs

and

• Retrieved Bank Policies

Never fabricate information.

Never invent banking policies.

If sufficient evidence is unavailable,
clearly state that.

Always answer professionally.
"""

    # ---------------------------------------------------------

    def _prediction_section(
        self,
        evidence: dict,
    ) -> str:
        """
        Prediction information.
        """

        prediction = evidence.get(
            "prediction",
            "Unknown",
        )

        probability = evidence.get(
            "probability",
            0,
        )

        return f"""
===========================
PREDICTION
===========================

Prediction

{prediction}

Probability

{probability:.2%}
"""

    # ---------------------------------------------------------

    def _feature_section(
        self,
        evidence: dict,
    ) -> str:
        """
        SHAP explanation.
        """

        features = evidence.get(
            "top_features",
            [],
        )

        text = """
===========================
TOP CONTRIBUTING FEATURES
===========================

"""

        if not features:

            text += "No feature explanation available."

            return text

        for index, feature in enumerate(
            features,
            start=1,
        ):

            text += f"""
Feature {index}

Name
{feature['feature']}

Applicant Value
{feature['value']}

Importance
{feature['importance']:.4f}

"""

        return text

    # ---------------------------------------------------------

    def _policy_section(
        self,
        evidence: dict,
    ) -> str:
        """
        Retrieved policy evidence.
        """

        documents = evidence.get(
            "retrieved_documents",
            [],
        )

        text = """
===========================
RETRIEVED POLICY EVIDENCE
===========================

"""

        if not documents:

            text += "No supporting documents found."

            return text

        for index, item in enumerate(
            documents,
            start=1,
        ):

            document = item["document"]

            metadata = document.metadata

            source = metadata.get(
                "source",
                "Unknown",
            )

            page = metadata.get(
                "page_label",
                metadata.get(
                    "page",
                    "-",
                ),
            )

            cross_score = item["cross_score"]

            text += f"""
--------------------------------------------------

Document {index}

Source
{source}

Page
{page}

Cross Encoder Score
{cross_score:.4f}

Content

{document.page_content}

"""

        return text

    # ---------------------------------------------------------

    def _question_section(
        self,
        user_question: str,
    ) -> str:
        """
        User question.
        """

        return f"""
===========================
USER QUESTION
===========================

{user_question}
"""

    # ---------------------------------------------------------

    def _instruction_section(self) -> str:
        """
        Final instructions.
        """

        return """
===========================
INSTRUCTIONS
===========================

1. Answer ONLY using the supplied evidence.

2. Explain the prediction clearly.

3. Connect the prediction with
the retrieved banking policies.

4. Reference policy evidence
naturally in your explanation.

5. Do NOT fabricate policy rules.

6. If evidence is insufficient,
clearly mention the limitation.

7. Write in a professional
banking tone.

8. Produce a structured answer
using clear paragraphs.
"""


# ==========================================================
# Testing
# ==========================================================

if __name__ == "__main__":

    prompt_builder = DecisionPrompt()

    evidence = {

        "prediction": "Charged Off",

        "probability": 0.84,

        "top_features": [

            {
                "feature": "dti",
                "value": 41,
                "importance": 0.44,
            },

            {
                "feature": "annual_income",
                "value": 50000,
                "importance": 0.28,
            },

            {
                "feature": "grade",
                "value": "B3",
                "importance": 0.17,
            },

        ],

        "retrieved_documents": [],

    }

    prompt = prompt_builder.build(

        user_question="Why was this applicant rejected?",

        evidence=evidence,

    )

    print(prompt)