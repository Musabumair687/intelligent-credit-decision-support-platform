"""
feature_selector.py

Purpose
-------
Selects the most important features from the SHAP
Explanation returned by the Prediction Service.

The selected features are passed to the Query Generator
to create policy-aware retrieval queries, and to the
Decision Prompt to be shown to both the LLM and the
credit officer reading the final explanation.

This module DOES NOT perform retrieval.

Fix applied in this version
----------------------------
select() now accepts the raw (unencoded) applicant dict. When a
top feature's name matches a key in that dict, the ORIGINAL
value is used instead of shap_explanation.data.iloc[index] —
which is the label-encoded integer, not the real category. This
matters specifically for every categorical feature that went
through LabelEncoder before hitting the model: sub_grade,
home_ownership, verification_status, purpose, initial_list_status,
application_type, term. Numeric features (dti, annual_inc,
int_rate, revol_util, etc.) were never encoded, so this has no
effect on them — they already displayed correctly.

Author
------
Intelligent Credit Decision Support Platform
"""

from typing import Dict, List, Optional

import numpy as np

import shap


class FeatureSelector:
    """
    Select the most influential SHAP features, with their
    original (human-readable) applicant values where available.
    """

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    # ---------------------------------------------------------

    def select(
        self,
        shap_explanation: shap.Explanation,
        applicant: Optional[dict] = None,
    ) -> List[Dict]:
        """
        Select the most important SHAP features.

        Parameters
        ----------
        shap_explanation : shap.Explanation
            SHAP Explanation object returned by PredictionService.
            Its .data holds encoded values for categorical features.

        applicant : dict | None
            The original, unencoded applicant dict submitted by the
            user. When supplied, any top feature whose name is a key
            in this dict is displayed using this raw value instead
            of the encoded one baked into shap_explanation.data.

        Returns
        -------
        List[Dict]

        Example
        -------
        [
            {
                "feature": "sub_grade",
                "value": "B3",          # human-readable, not 7
                "shap": 0.4331,
                "importance": 0.4331
            }
        ]
        """

        if shap_explanation is None:
            return []

        applicant = applicant or {}

        shap_values = np.array(shap_explanation.values)

        ranked_indices = np.argsort(np.abs(shap_values))[::-1]

        selected_features = []

        for index in ranked_indices[: self.top_k]:

            feature_name = shap_explanation.feature_names[index]

            # Prefer the original applicant-submitted value when
            # available — this is what fixes the encoded-integer
            # display bug for categorical features.
            if feature_name in applicant:
                display_value = applicant[feature_name]
            else:
                display_value = shap_explanation.data.iloc[index]

            selected_features.append({
                "feature": feature_name,
                "value": display_value,
                "shap": float(shap_values[index]),
                "importance": float(abs(shap_values[index])),
            })

        return selected_features


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":

    import pandas as pd

    explanation = shap.Explanation(
        values=np.array([-0.43, 0.15, 0.4331, 0.07, 0.02]),
        data=pd.Series([71000, 12, 7, 12000, 13.33]),  # sub_grade ENCODED as 7
        feature_names=["annual_inc", "dti", "sub_grade", "loan_amnt", "int_rate"],
    )

    applicant = {
        "annual_inc": 71000,
        "dti": 12,
        "sub_grade": "B3",   # the REAL value the user submitted
        "loan_amnt": 12000,
        "int_rate": 13.33,
    }

    selector = FeatureSelector()

    print("Without applicant dict (old behavior):")
    for f in selector.select(explanation):
        print(f"  {f['feature']} = {f['value']}")

    print("\nWith applicant dict (fixed behavior):")
    for f in selector.select(explanation, applicant=applicant):
        print(f"  {f['feature']} = {f['value']}")