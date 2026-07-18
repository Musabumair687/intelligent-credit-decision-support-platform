"""
feature_selector.py

Purpose
-------
Selects the most important features from the SHAP
Explanation returned by the Prediction Service.

The selected features are passed to the Query Generator
to create policy-aware retrieval queries.

This module DOES NOT perform retrieval.

Author
------
Intelligent Credit Decision Support Platform
"""

from typing import List, Dict

import numpy as np

import shap


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
        shap_explanation: shap.Explanation,
    ) -> List[Dict]:
        """
        Select the most important SHAP features.

        Parameters
        ----------
        shap_explanation : shap.Explanation

            SHAP Explanation object returned by
            PredictionService.

        Returns
        -------
        List[Dict]

        Example

        [
            {
                "feature": "annual_inc",
                "value": 71000,
                "shap": -0.38,
                "importance": 0.38
            }
        ]
        """

        if shap_explanation is None:

            return []

        shap_values = np.array(shap_explanation.values)

        ranked_indices = np.argsort(
            np.abs(shap_values)
        )[::-1]

        selected_features = []

        for index in ranked_indices[: self.top_k]:

            selected_features.append(

                {

                    "feature":
                        shap_explanation.feature_names[index],

                    "value":
                        shap_explanation.data.iloc[index],

                    "shap":
                        float(shap_values[index]),

                    "importance":
                        float(abs(shap_values[index])),

                }

            )

        return selected_features


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":

    import pandas as pd

    explanation = shap.Explanation(

        values=np.array(
            [
                -0.43,
                0.15,
                -0.28,
                0.07,
                0.02,
            ]
        ),

        data=pd.Series(
            [
                71000,
                12,
                "B3",
                12000,
                13.33,
            ]
        ),

        feature_names=[
            "annual_inc",
            "dti",
            "sub_grade",
            "loan_amnt",
            "int_rate",
        ],

    )

    selector = FeatureSelector()

    features = selector.select(

        shap_explanation=explanation,

    )

    print("=" * 80)
    print("TOP SHAP FEATURES")
    print("=" * 80)

    for index, item in enumerate(features, start=1):

        print(f"\nFeature {index}")

        print("-" * 80)

        print(f"Feature     : {item['feature']}")

        print(f"Value       : {item['value']}")

        print(f"SHAP        : {item['shap']:.4f}")

        print(f"Importance  : {item['importance']:.4f}")