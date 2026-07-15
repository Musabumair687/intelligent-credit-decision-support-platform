"""
feature_selector.py

Purpose
-------
Selects the most important features from the SHAP
explanation after a loan prediction.

The selected features are passed to the Query Generator
to create policy-aware retrieval queries.

This module DOES NOT perform retrieval.

Author
------
Intelligent Credit Decision Support Platform
"""

from typing import Dict, List


class FeatureSelector:
    """
    Select the most influential SHAP features.

    Features are ranked using the absolute SHAP value
    because both positive and negative SHAP values
    represent important contributions.
    """

    def __init__(
        self,
        top_k: int = 5,
    ):
        """
        Parameters
        ----------
        top_k : int

            Number of top features to return.
        """

        self.top_k = top_k

    # ---------------------------------------------------------

    def select(
        self,
        applicant: Dict,
        shap_values: Dict[str, float],
    ) -> List[Dict]:
        """
        Select the top SHAP features.

        Parameters
        ----------
        applicant : Dict

            Applicant information.

        Example

        {
            "annual_income": 50000,
            "dti": 41,
            "grade": "B3",
            "loan_amount": 25000
        }

        shap_values : Dict[str, float]

            SHAP explanation.

        Example

        {
            "annual_income": -0.28,
            "dti": 0.44,
            "grade": 0.17
        }

        Returns
        -------
        List[Dict]

        Example

        [
            {
                "feature": "dti",
                "value": 41,
                "importance": 0.44
            },
            ...
        ]
        """

        if not shap_values:

            return []

        ranked_features = sorted(

            shap_values.items(),

            key=lambda item: abs(item[1]),

            reverse=True,

        )

        selected_features = []

        for feature, importance in ranked_features[: self.top_k]:

            selected_features.append(

                {
                    "feature": feature,

                    "value": applicant.get(feature),

                    "importance": importance,
                }

            )

        return selected_features


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":

    applicant = {

        "loan_amount": 25000,

        "annual_income": 50000,

        "dti": 41,

        "grade": "B3",

        "interest_rate": 12.7,

        "employment_length": 5,

    }

    shap_values = {

        "dti": 0.44,

        "annual_income": -0.28,

        "grade": 0.17,

        "interest_rate": 0.12,

        "loan_amount": 0.05,

        "employment_length": 0.03,

    }

    selector = FeatureSelector()

    features = selector.select(

        applicant=applicant,

        shap_values=shap_values,

    )

    print("=" * 80)
    print("TOP SHAP FEATURES")
    print("=" * 80)

    for index, item in enumerate(features, start=1):

        print(f"\nFeature {index}")

        print("-" * 80)

        print(f"Feature     : {item['feature']}")

        print(f"Value       : {item['value']}")

        print(f"Importance  : {item['importance']:.4f}")