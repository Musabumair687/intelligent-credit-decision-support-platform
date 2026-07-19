"""
evidence_builder.py

Purpose
-------
Builds the retrieval evidence required by the
Decision Intelligence module.

Fix applied in this version
----------------------------
The applicant's raw (unencoded) dict is now passed through to
FeatureSelector.select(), so it can substitute human-readable
values (e.g. "B3", "MORTGAGE") in place of the label-encoded
integers that live inside the SHAP Explanation object. Without
this, categorical top_features showed meaningless encoder IDs
(sub_grade: 7, home_ownership: 1) to both the LLM and the end
user, which previously caused the LLM to misinterpret an encoder
ID as a real grade value in its explanation.

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
        self.feature_selector = FeatureSelector()
        self.query_generator = QueryGenerator()

    # ---------------------------------------------------------

    def build(self, context: dict) -> dict:
        """
        Build retrieval evidence.

        Parameters
        ----------
        context : dict
            Prediction context. Must include "applicant" (the raw,
            unencoded applicant dict) and "shap_explanation".

        Returns
        -------
        dict
            Evidence object.
        """

        applicant = context["applicant"]

        shap_explanation = context["shap_explanation"]

        # ---------------------------------------------
        # Select top SHAP features, decoded back to
        # human-readable values using the raw applicant dict.
        # ---------------------------------------------

        top_features = self.feature_selector.select(
            shap_explanation=shap_explanation,
            applicant=applicant,
        )

        # ---------------------------------------------
        # Generate retrieval query
        # ---------------------------------------------

        retrieval_query = self.query_generator.generate(top_features)

        # ---------------------------------------------
        # Build evidence package
        # ---------------------------------------------

        evidence = {
            "applicant": applicant,
            "prediction": context["prediction"],
            "repayment_probability": context["repayment_probability"],
            "default_probability": context["default_probability"],
            "shap_explanation": shap_explanation,
            "top_features": top_features,
            "retrieval_query": retrieval_query,
            "retrieved_documents": [],
        }

        return evidence


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":
    print("=" * 80)
    print("EvidenceBuilder uses SHAP Explanation objects.")
    print("Please test this module through orchestrator.py")
    print("=" * 80)