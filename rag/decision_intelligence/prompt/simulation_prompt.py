"""
simulation_prompt.py

Purpose
-------
Builds the prompt used to explain
What-If simulations.

This module never:

- Runs the ML model
- Performs retrieval
- Calls the LLM

It only converts structured simulation
results into a professional prompt.

Fix applied in this version
----------------------------
_build_shap_section() previously dumped raw Python dicts straight
into the prompt via an f-string. Because the values inside those
dicts are numpy scalar types (np.float64), this produced ugly,
implementation-revealing text like:

    {'feature': 'sub_grade', 'value': np.float64(7.0), 'shap': 0.433...}

directly inside the prompt sent to the LLM. This both increased
the chance of the LLM misreading a value and violated this
module's own rule to never reveal internal implementation details
(numpy, in this case). _build_shap_section() now normalizes every
item into a clean "feature (importance: X.XXXX)" line regardless
of whether it's given a plain feature-name string or a full dict,
and explicitly coerces all numeric values to native Python floats
so no numpy repr can leak through.

Author
------
Intelligent Credit Decision Support Platform
"""


class SimulationPrompt:
    """
    Builds prompts for What-If simulation
    explanations.
    """

    def __init__(self):
        """
        Initialize prompt builder.
        """
        pass

    # =====================================================
    # Helper Functions
    # =====================================================

    def _build_applicant_summary(
        self,
        applicant_summary: dict,
    ) -> str:
        """
        Convert applicant summary into text.
        """

        return f"""
Loan Amount            : {applicant_summary.get("loan_amount")}
Interest Rate          : {applicant_summary.get("interest_rate")}
Term                   : {applicant_summary.get("term")}
Sub Grade              : {applicant_summary.get("sub_grade")}
Purpose                : {applicant_summary.get("purpose")}
Annual Income          : {applicant_summary.get("annual_income")}
Debt-to-Income Ratio   : {applicant_summary.get("dti")}
"""

    # -----------------------------------------------------

    def _build_changes(
        self,
        changes: dict,
    ) -> str:
        """
        Build feature modification section.
        """

        if not changes:

            return "No applicant features were modified."

        text = ""

        for feature, values in changes.items():

            text += f"""
Feature

{feature}

Old Value

{values.get("old")}

New Value

{values.get("new")}

Direction

{values.get("direction")}

Percentage Change

{values.get("percentage_change")}

----------------------------------------
"""

        return text

    # -----------------------------------------------------

    def _build_shap_section(
        self,
        shap_comparison: dict,
    ) -> str:
        """
        Build SHAP comparison section.

        Accepts original_top_features / simulation_top_features in
        either shape:

        - a list of plain feature-name strings, or
        - a list of dicts like
          {"feature": "dti", "shap": 0.126, "importance": 0.126}
          (which is what FeatureSelector / EvidenceBuilder /
          PredictionService currently produce).

        Every numeric value is coerced to a native Python float
        before formatting, so numpy scalar types (np.float64)
        never reach the prompt as a raw, implementation-revealing
        repr string.
        """

        original = shap_comparison.get(
            "original_top_features",
            [],
        )

        simulation = shap_comparison.get(
            "simulation_top_features",
            [],
        )

        def _format_feature_line(item) -> str:

            # Plain string feature name — nothing to format.
            if isinstance(item, str):
                return f"- {item}"

            # Dict shape — pull out name/importance, coercing any
            # numpy scalar to a native float first.
            if isinstance(item, dict):

                name = item.get("feature", "unknown")

                importance = item.get("importance", item.get("shap"))

                if importance is not None:
                    try:
                        importance = float(importance)
                        return f"- {name} (importance: {importance:.4f})"
                    except (TypeError, ValueError):
                        pass

                return f"- {name}"

            # Fallback for any other shape.
            return f"- {item}"

        text = "Original Important Features\n\n"

        for feature in original:
            text += _format_feature_line(feature) + "\n"

        text += "\n"

        text += "Simulation Important Features\n\n"

        for feature in simulation:
            text += _format_feature_line(feature) + "\n"

        return text

    # -----------------------------------------------------

    def build_prompt(
        self,
        user_question: str,
        simulation_result: dict,
    ) -> str:
        """
        Build complete simulation prompt.
        """

        original = simulation_result.get(
            "original",
            {},
        )

        simulation = simulation_result.get(
            "simulation",
            {},
        )

        comparison = simulation_result.get(
            "comparison",
            {},
        )

        applicant_summary = simulation_result.get(
            "applicant_summary",
            {},
        )

        changes = simulation_result.get(
            "changes",
            {},
        )

        shap_comparison = simulation_result.get(
            "shap_comparison",
            {},
        )

        applicant_text = self._build_applicant_summary(
            applicant_summary,
        )

        changes_text = self._build_changes(
            changes,
        )

        shap_text = self._build_shap_section(
            shap_comparison,
        )

        prompt = f"""
You are a Senior Credit Risk Analyst at a financial institution.

Your responsibility is to explain the outcome of a hypothetical
"What-If" simulation generated by a Machine Learning credit risk model.

The purpose is to help banking professionals understand
how changing applicant information influenced the prediction.

Do NOT invent information.

Use ONLY the information provided below.

============================================================
USER QUESTION
============================================================

{user_question}

============================================================
APPLICANT SUMMARY
============================================================

{applicant_text}

============================================================
ORIGINAL MODEL RESULT
============================================================

Decision

{original.get("prediction")}

Repayment Probability

{original.get("repayment_probability")}

Default Probability

{original.get("default_probability")}

============================================================
SIMULATION MODEL RESULT
============================================================

Decision

{simulation.get("prediction")}

Repayment Probability

{simulation.get("repayment_probability")}

Default Probability

{simulation.get("default_probability")}

============================================================
DECISION COMPARISON
============================================================

Decision Transition

{comparison.get("decision_transition")}

Prediction Changed

{comparison.get("prediction_changed")}

Risk Change

{comparison.get("risk_change")}

Repayment Probability Difference

{comparison.get("repayment_probability_difference")}

Default Probability Difference

{comparison.get("default_probability_difference")}

============================================================
FEATURE MODIFICATIONS
============================================================

{changes_text}

============================================================
MODEL EXPLANATION (SHAP)
============================================================

{shap_text}

============================================================
TASK
============================================================

Write a professional explanation for this simulation.

Your explanation should cover:

1. Summarize what the user changed.

2. Explain how those changes affected the prediction.

3. Explain whether the repayment probability
   improved or deteriorated.

4. Explain why the important SHAP features
   influenced the model.

5. Identify the primary factors responsible
   for the final prediction.

6. If the prediction did not change,
   explain why the changes were insufficient.

7. If the prediction changed,
   explain which changes had the largest impact.

8. Mention any remaining financial risks.

============================================================
RULES
============================================================

- Use only the supplied information.

- Never invent applicant information.

- Never invent banking policies.

- Never invent SHAP values.

- Never mention LightGBM,
  Machine Learning implementation,
  or internal system architecture.

- Explain in clear,
  professional banking language.

- Focus on causal reasoning instead of
  simply repeating probabilities.

- Keep the explanation concise,
  informative,
  and suitable for financial professionals.
"""

        return prompt


# ==========================================================
# Testing
# ==========================================================

if __name__ == "__main__":

    import numpy as np

    builder = SimulationPrompt()

    simulation_result = {

        "original": {
            "prediction": "Rejected",
            "repayment_probability": 0.27,
            "default_probability": 0.73,
        },

        "simulation": {
            "prediction": "Approved",
            "repayment_probability": 0.81,
            "default_probability": 0.19,
        },

        "comparison": {
            "prediction_changed": True,
            "decision_transition": "Rejected -> Approved",
            "risk_change": "Lower Risk",
            "repayment_probability_difference": 0.54,
            "default_probability_difference": -0.54,
        },

        "applicant_summary": {
            "loan_amount": 12000,
            "interest_rate": 13.33,
            "term": 36,
            "sub_grade": "B3",
            "purpose": "debt_consolidation",
            "annual_income": 71000,
            "dti": 12,
        },

        "changes": {
            "annual_inc": {
                "old": 71000,
                "new": 95000,
                "direction": "Increase",
                "percentage_change": 33.80,
            },
            "dti": {
                "old": 12,
                "new": 8,
                "direction": "Decrease",
                "percentage_change": -33.33,
            },
        },

        # Deliberately shaped like real upstream output, including
        # numpy scalar types, to prove the fix normalizes them.
        "shap_comparison": {
            "original_top_features": [
                {"feature": "sub_grade", "value": np.float64(7.0), "shap": 0.4331, "importance": 0.4331},
                {"feature": "dti", "value": np.float64(12.0), "shap": 0.1262, "importance": 0.1262},
            ],
            "simulation_top_features": [
                {"feature": "sub_grade", "value": np.float64(7.0), "shap": 0.4225, "importance": 0.4225},
                {"feature": "annual_inc", "value": np.float64(95000.0), "shap": 0.2167, "importance": 0.2167},
            ],
        },

    }

    prompt = builder.build_prompt(
        user_question="What happens if annual income increases to 95,000 and DTI decreases to 8?",
        simulation_result=simulation_result,
    )

    print("=" * 80)
    print("SIMULATION PROMPT")
    print("=" * 80)
    print(prompt)