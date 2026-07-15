"""
query_generator.py

Purpose
-------
Generates retrieval queries from the most important
SHAP features.

Instead of sending the entire prediction or SHAP
explanation to the retriever, this module converts
the important ML features into banking policy
queries.

These queries are later passed to the Hybrid Retriever.

Author
------
Intelligent Credit Decision Support Platform
"""

from typing import Dict, List


class QueryGenerator:
    """
    Generate policy retrieval queries from
    the selected SHAP features.
    """

    # ---------------------------------------------------------

    FEATURE_QUERY_MAP = {

        "dti":
        "Debt-to-Income Ratio policy borrower indebtedness maximum DTI",

        "annual_income":
        "Annual income eligibility income verification minimum income",

        "grade":
        "Credit grade borrower risk classification loan grading",

        "sub_grade":
        "Credit sub-grade lending policy borrower risk",

        "loan_amount":
        "Maximum loan amount lending limits loan eligibility",

        "interest_rate":
        "Interest rate lending policy pricing policy",

        "employment_length":
        "Employment history employment stability borrower eligibility",

        "home_ownership":
        "Home ownership collateral borrower profile",

        "purpose":
        "Loan purpose lending policy approved loan usage",

        "term":
        "Loan term repayment period lending policy",

        "revolving_utilization":
        "Credit utilization revolving balance borrower indebtedness",

        "open_accounts":
        "Open credit accounts borrower credit profile",

        "delinquencies":
        "Delinquency policy repayment history borrower risk",

        "credit_history":
        "Credit history borrower creditworthiness",

    }

    # ---------------------------------------------------------

    def __init__(self):
        """
        Initialize Query Generator.
        """

        pass

    # ---------------------------------------------------------

    def generate(
        self,
        features: List[Dict],
    ) -> str:
        """
        Generate one enriched retrieval query.

        Parameters
        ----------
        features : List[Dict]

            Output from FeatureSelector.

        Returns
        -------
        str

            Retrieval query.
        """

        queries = [

            "Loan approval policy",

            "Loan rejection policy",

        ]

        for item in features:

            feature = item["feature"]

            if feature in self.FEATURE_QUERY_MAP:

                queries.append(

                    self.FEATURE_QUERY_MAP[feature]

                )

        retrieval_query = "\n".join(

            dict.fromkeys(queries)

        )

        return retrieval_query


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":

    features = [

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

        {
            "feature": "loan_amount",
            "value": 25000,
            "importance": 0.08,
        },

        {
            "feature": "interest_rate",
            "value": 12.7,
            "importance": 0.05,
        },

    ]

    generator = QueryGenerator()

    query = generator.generate(features)

    print("=" * 80)
    print("RETRIEVAL QUERY")
    print("=" * 80)

    print(query)