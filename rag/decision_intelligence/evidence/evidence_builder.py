"""
evidence_builder.py

Purpose
-------
Builds the retrieval evidence required by the
Decision Intelligence module.

The Evidence Builder coordinates the complete
Evidence Layer by:

1. Selecting the most important SHAP features.
2. Generating retrieval queries.
3. Returning a structured evidence object.

This module does NOT perform retrieval.

Author
------
Intelligent Credit Decision Support Platform
"""

from rag.decision_intelligence.evidence.feature_selector import (
    FeatureSelector,
)

from rag.decision_intelligence.evidence.query_generator import (
    QueryGenerator,
)


class EvidenceBuilder:
    """
    Coordinates the complete Evidence Layer.
    """

    def __init__(self):
        """
        Initialize Evidence Builder.
        """

        self.feature_selector = FeatureSelector()

        self.query_generator = QueryGenerator()

    # ---------------------------------------------------------

    def build(
        self,
        context: dict,
    ) -> dict:
        """
        Build retrieval evidence.

        Parameters
        ----------
        context : dict

            Prediction context.

        Returns
        -------
        dict

            Evidence object.
        """

        

        top_features = self.feature_selector.select(

        context["shap_explanation"]

    )

        retrieval_query = self.query_generator.generate(

            top_features,

        )

        evidence = {

            "prediction":
            context["prediction"],

            "probability":
            context["probability"],

            "top_features":
            top_features,

            "retrieval_query":
            retrieval_query,

        }

        return evidence


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":

    context = {

        "applicant": {

            "loan_amount": 25000,

            "annual_income": 50000,

            "dti": 41,

            "grade": "B3",

            "interest_rate": 12.7,

        },

        "prediction": "Charged Off",

        "probability": 0.84,

        "shap_values": {

            "dti": 0.44,

            "annual_income": -0.28,

            "grade": 0.17,

            "interest_rate": 0.12,

            "loan_amount": 0.05,

        }

    }

    builder = EvidenceBuilder()

    evidence = builder.build(context)

    print("=" * 80)
    print("EVIDENCE")
    print("=" * 80)

    for key, value in evidence.items():

        print(f"\n{key}")

        print("-" * 80)

        print(value)