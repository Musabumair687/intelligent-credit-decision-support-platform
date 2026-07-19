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
5. Verified Policy Comparisons (computed here, not by the LLM)
6. Retrieved Policy Evidence

into a single structured prompt.

This module NEVER performs retrieval.

It ONLY prepares the final prompt.

Fix applied in this version
----------------------------
A live test showed the LLM incorrectly stating that a DTI of
12.0% was "higher than" the Chapter 14 Grade A range of 5-15%,
which is false — 12 falls inside that range. Rather than asking
the LLM to compare numbers against ranges it only sees as prose
in retrieved policy excerpts (error-prone), this file now computes
those comparisons itself in Python, using the Chapter 14 Section
14.3 grade bands stored below as a class-level constant, and
injects the result into the prompt as a labeled "VERIFIED" section
the model is instructed to treat as ground truth rather than
recompute. No new files were added — the bands and the comparison
logic both live inside this existing class.

Author
------
Intelligent Credit Decision Support Platform
"""


class DecisionPrompt:
    """
    Builds the prompt for the AI Credit Decision Assistant.
    """

    # -------------------------------------------------------
    # Chapter 14, Section 14.3 — Primary Credit Grade bands.
    # (low, high) per metric per grade letter. Kept here, not in
    # a separate file, since this is the only place it's used.
    # Update this if Chapter 14's numeric bands are ever revised.
    # -------------------------------------------------------
    GRADE_BANDS = {
        "A": {"dti": (5.0, 15.0), "rate": (6.50, 9.00), "util": (0.0, 20.0)},
        "B": {"dti": (15.0, 22.0), "rate": (9.00, 12.50), "util": (15.0, 40.0)},
        "C": {"dti": (22.0, 30.0), "rate": (12.50, 16.50), "util": (35.0, 60.0)},
        "D": {"dti": (30.0, 38.0), "rate": (16.50, 21.00), "util": (55.0, 75.0)},
        "E": {"dti": (38.0, 45.0), "rate": (21.00, 26.00), "util": (70.0, 90.0)},
        "F": {"dti": (45.0, 52.0), "rate": (26.00, 31.00), "util": (85.0, 100.0)},
        "G": {"dti": (52.0, 60.0), "rate": (31.00, 36.00), "util": (95.0, 100.0)},
    }

    GRADE_ORDER = ["A", "B", "C", "D", "E", "F", "G"]

    METRIC_LABELS = {
        "dti": ("Debt-to-Income Ratio", "%"),
        "rate": ("Interest Rate", "%"),
        "util": ("Revolving Utilization", "%"),
    }

    # Maps applicant dict keys -> the metric name used in GRADE_BANDS
    FEATURE_TO_METRIC = {
        "dti": "dti",
        "int_rate": "rate",
        "revol_util": "util",
    }

    def __init__(self):
        pass

    # ---------------------------------------------------------

    def build(self, user_question: str, evidence: dict) -> str:
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
            self._policy_comparison_section(evidence),
            self._policy_section(evidence),
            self._question_section(user_question),
            self._instruction_section(),
        ]

        return "\n\n".join(sections)

    # ---------------------------------------------------------

    def _system_prompt(self) -> str:
        return """
===========================
SYSTEM
===========================

You are a Senior Credit Risk Analyst working for a commercial bank.

Your responsibility is to explain Machine Learning
credit decisions using BOTH:

- Predictive analytics

and

- Retrieved banking policy evidence.

Always remain objective.

Never fabricate facts.

Never invent banking policies.

Never contradict the supplied evidence.

If evidence is insufficient,
clearly mention the limitation.

Write in a professional banking style.
"""

    # ---------------------------------------------------------

    def _prediction_section(self, evidence: dict) -> str:

        prediction = evidence.get("prediction", "Unknown")

        repayment_probability = evidence.get("repayment_probability", 0)
        default_probability = evidence.get("default_probability", 0)

        return f"""
===========================
PREDICTION
===========================

Prediction

{prediction}

Repayment Probability

{repayment_probability:.2%}

Default Probability

{default_probability:.2%}

"""

    # ---------------------------------------------------------

    def _feature_section(self, evidence: dict) -> str:

        features = evidence.get("top_features", [])

        text = """
===========================
TOP CONTRIBUTING FEATURES
===========================

"""

        if not features:
            text += "No feature explanation available."
            return text

        for index, feature in enumerate(features, start=1):

            text += f"""
Feature {index}

Name
{feature['feature']}

Applicant Value
{feature['value']}

SHAP Contribution

{feature['shap']:.4f}

"""

        return text

    # ---------------------------------------------------------

    def _policy_comparison_section(self, evidence: dict) -> str:
        """
        Pre-computed, exactly-verified numeric comparisons between
        the applicant's actual metrics and the Chapter 14 grade
        bands. This is arithmetic done in Python, not something the
        model is asked to derive — see module docstring for why.
        """

        applicant = evidence.get("applicant", {}) or {}

        comparisons = self._build_policy_comparisons(applicant)

        text = """
===========================
VERIFIED POLICY COMPARISONS (COMPUTED, NOT ESTIMATED)
===========================

These comparisons are pre-calculated and verified. Treat them as
ground truth. Do not restate a numeric relationship differently
than stated here.

"""

        if not comparisons:
            text += "No verified numeric comparisons available for this applicant.\n"
            return text

        for line in comparisons:
            text += f"- {line}\n"

        return text

    # ---------------------------------------------------------

    def _build_policy_comparisons(self, applicant: dict):
        """
        Compare the applicant's raw DTI / interest rate / revolving
        utilization against the Chapter 14 band for their own
        assigned Primary Grade (derived from sub_grade, e.g. "B3"
        -> "B"), plus note which grade's band their raw value
        actually falls into if different from their own grade.
        """

        statements = []

        sub_grade = applicant.get("sub_grade")

        own_letter = None

        if sub_grade:
            candidate = str(sub_grade).strip()[0].upper()
            if candidate in self.GRADE_BANDS:
                own_letter = candidate

        for feature_key, metric in self.FEATURE_TO_METRIC.items():

            raw_value = applicant.get(feature_key)

            if raw_value is None:
                continue

            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue

            label, unit = self.METRIC_LABELS[metric]

            # Which grade's band does this raw value actually sit in?
            actual_letter = None
            for letter in self.GRADE_ORDER:
                low, high = self.GRADE_BANDS[letter][metric]
                if low <= value <= high:
                    actual_letter = letter
                    break

            if own_letter:

                low, high = self.GRADE_BANDS[own_letter][metric]

                if low <= value <= high:
                    relation = (
                        f"WITHIN their own Grade {own_letter}'s typical range "
                        f"({low}{unit}-{high}{unit})"
                    )
                elif value < low:
                    relation = (
                        f"BELOW (more favorable than) their own Grade {own_letter}'s "
                        f"typical range ({low}{unit}-{high}{unit})"
                    )
                else:
                    relation = (
                        f"ABOVE (less favorable than) their own Grade {own_letter}'s "
                        f"typical range ({low}{unit}-{high}{unit})"
                    )

                statement = (
                    f"{label}: applicant value is {value}{unit}. "
                    f"This is {relation}."
                )

                if actual_letter and actual_letter != own_letter:
                    statement += (
                        f" On its own, a value of {value}{unit} for {label} falls "
                        f"within the range typically associated with Grade {actual_letter}."
                    )

                statements.append(statement)

            elif actual_letter:

                statements.append(
                    f"{label}: applicant value is {value}{unit}, which falls within "
                    f"the range typically associated with Grade {actual_letter}."
                )

        return statements

    # ---------------------------------------------------------

    def _policy_section(self, evidence: dict) -> str:

        documents = evidence.get("retrieved_documents", [])

        text = """
===========================
RETRIEVED POLICY EVIDENCE
===========================

"""

        if not documents:
            text += "No supporting documents found."
            return text

        for index, item in enumerate(documents, start=1):

            document = item["document"]
            metadata = document.metadata

            source = metadata.get("source", "Unknown")
            page = metadata.get("page_label", metadata.get("page", "-"))
            cross_score = item["cross_score"]

            text += f"""
--------------------------------------------------
Evidence {index}

Source
{source}

Page
{page}

Cross Encoder Score
{cross_score:.4f}

Policy Excerpt

{document.page_content}

"""

        return text

    # ---------------------------------------------------------

    def _question_section(self, user_question: str) -> str:

        return f"""
===========================
USER QUESTION
===========================

{user_question}
"""

    # ---------------------------------------------------------

    def _instruction_section(self) -> str:

        return """
===========================
INSTRUCTIONS
===========================

Write your response using the following structure.

1. Executive Summary

2. Prediction Interpretation

3. Key Risk Drivers
   (based on SHAP)

4. Supporting Banking Policies
   (using retrieved evidence)

5. Overall Risk Assessment

6. Conclusion

Rules

- Use ONLY the supplied evidence.

- Treat the VERIFIED POLICY COMPARISONS section as ground truth.
  Do not recompute or contradict any relationship stated there.

- Never fabricate policy rules.

- Never invent applicant information.

- Never mention internal ML implementation.

- Clearly distinguish:
  - Model evidence
  - Banking policy evidence

- If retrieved evidence is insufficient,
  clearly mention the limitation.

Write professionally for banking staff."""


# ==========================================================
# Testing
# ==========================================================

if __name__ == "__main__":

    prompt_builder = DecisionPrompt()

    evidence = {

        "applicant": {
            "sub_grade": "B3",
            "dti": 12,
            "int_rate": 13.33,
            "revol_util": 41,
        },

        "prediction": "Charged Off",

        "repayment_probability": 0.16,

        "default_probability": 0.84,

        "top_features": [
            {"feature": "dti", "value": 12, "shap": 0.44, "importance": 0.44},
            {"feature": "sub_grade", "value": "B3", "shap": -0.28, "importance": 0.28},
        ],

        "retrieved_documents": [],

    }

    prompt = prompt_builder.build(
        user_question="Why was this applicant rejected?",
        evidence=evidence,
    )

    print(prompt)