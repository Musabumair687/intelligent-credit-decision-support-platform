"""
query_generator.py

Purpose
-------
Generates retrieval queries from the most important
SHAP features.

Instead of sending the entire prediction or SHAP
explanation to the retriever, this module converts
the important features into banking policy queries.

These queries are later passed to the Hybrid Retriever.

Fix applied in this version
----------------------------
FEATURE_QUERY_MAP previously used business-friendly key
names ("annual_income", "loan_amount", "interest_rate",
"employment_length", "revolving_utilization") that never
occur in the real pipeline. The actual feature names come
from PredictionService.feature_order, which are the raw
dataset column names ("annual_inc", "loan_amnt", "int_rate",
"emp_length", "revol_util", etc.). Because of the mismatch,
`if feature in self.FEATURE_QUERY_MAP` was silently False
for exactly the features most likely to matter, and the
retrieval query quietly degraded to almost nothing extra.

The map below is now keyed by the real dataset column names
used throughout prediction_service.py and orchestrator.py.

Author
------
Intelligent Credit Decision Support Platform
"""

from typing import Dict, List


class QueryGenerator:
    """
    Generate policy retrieval queries from
    the selected top-feature list.
    """

    # ---------------------------------------------------------
    # Keyed by the REAL dataset column names, matching
    # PredictionService.feature_order / feature_names.
    # ---------------------------------------------------------

    FEATURE_QUERY_MAP = {

        "dti":
        "Debt-to-Income Ratio policy borrower indebtedness maximum DTI",

        "annual_inc":
        "Annual income eligibility income verification minimum income",

        "grade":
        "Credit grade borrower risk classification loan grading",

        "sub_grade":
        "Credit sub-grade lending policy borrower risk",

        "loan_amnt":
        "Maximum loan amount lending limits loan eligibility",

        "int_rate":
        "Interest rate lending policy pricing policy",

        "term":
        "Loan term repayment period lending policy",

        "emp_length":
        "Employment history employment stability borrower eligibility",

        "verification_status":
        "Income verification status borrower documentation policy",

        "home_ownership":
        "Home ownership collateral borrower profile",

        "purpose":
        "Loan purpose lending policy approved loan usage",

        "revol_util":
        "Credit utilization revolving balance borrower indebtedness",

        "revol_bal":
        "Revolving balance borrower indebtedness credit utilization",

        "open_acc":
        "Open credit accounts borrower credit profile",

        "total_acc":
        "Total credit accounts borrower credit history depth",

        "pub_rec":
        "Public record derogatory marks borrower credit history",

        "pub_rec_bankruptcies":
        "Bankruptcy policy borrower risk classification",

        "mort_acc":
        "Mortgage accounts borrower credit profile collateral",

        "initial_list_status":
        "Loan listing status lending policy",

        "application_type":
        "Individual joint application policy borrower eligibility",

        # Kept for backward compatibility in case any caller still
        # passes the older, human-friendly feature names.
        "annual_income": "Annual income eligibility income verification minimum income",
        "loan_amount": "Maximum loan amount lending limits loan eligibility",
        "interest_rate": "Interest rate lending policy pricing policy",
        "employment_length": "Employment history employment stability borrower eligibility",
        "revolving_utilization": "Credit utilization revolving balance borrower indebtedness",
        "delinquencies": "Delinquency policy repayment history borrower risk",
        "credit_history": "Credit history borrower creditworthiness",

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

            Output from FeatureSelector. Each item is expected
            to contain at least a "feature" key holding the raw
            dataset column name.

        Returns
        -------
        str

            Retrieval query, one topic per line, de-duplicated
            while preserving order.
        """

        queries = [

            "Loan approval policy",

            "Loan rejection policy",

        ]

        unmatched = []

        for item in features:

            feature = item.get("feature")

            if feature in self.FEATURE_QUERY_MAP:

                queries.append(self.FEATURE_QUERY_MAP[feature])

            else:

                # Don't silently drop it — fall back to using the
                # raw feature name itself as a query term so
                # retrieval still has something to search for,
                # even for a feature we haven't mapped yet.
                unmatched.append(feature)

        if unmatched:

            queries.append(
                "Lending policy regarding: " + ", ".join(
                    str(f) for f in unmatched if f
                )
            )

        retrieval_query = "\n".join(dict.fromkeys(queries))

        return retrieval_query


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":

    features = [

        {"feature": "dti", "value": 41, "importance": 0.44},
        {"feature": "annual_inc", "value": 50000, "importance": 0.28},
        {"feature": "sub_grade", "value": "B3", "importance": 0.17},
        {"feature": "loan_amnt", "value": 25000, "importance": 0.08},
        {"feature": "int_rate", "value": 12.7, "importance": 0.05},
        {"feature": "some_new_feature", "value": 1, "importance": 0.01},

    ]

    generator = QueryGenerator()

    query = generator.generate(features)

    print("=" * 80)
    print("RETRIEVAL QUERY")
    print("=" * 80)

    print(query)