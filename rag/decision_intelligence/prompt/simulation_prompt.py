"""
simulation_prompt.py

Purpose
-------
Builds the final prompt used for explaining
"What-If" simulations.

Unlike DecisionPrompt,
this prompt explains how modifying
applicant features changes the ML prediction.

This module NEVER:

- Calls the LLM
- Performs retrieval
- Makes predictions

It ONLY builds the prompt.

Author
------
Intelligent Credit Decision Support Platform
"""


class SimulationPrompt:
    """
    Builds prompts for simulation explanations.
    """

    def build_prompt(
        self,
        user_question: str,
        simulation_result: dict,
    ) -> str:
        """
        Build the simulation prompt.

        Parameters
        ----------
        user_question : str

        simulation_result : dict

        Returns
        -------
        str
        """

        original = simulation_result.get("original", {})
        simulation = simulation_result.get("simulation", {})
        changes = simulation_result.get("changes", {})
        comparison = simulation_result.get("comparison", {})

        # --------------------------------------------------
        # Build Changed Features Section
        # --------------------------------------------------

        change_text = ""

        if changes:

            for feature, values in changes.items():

                change_text += (
                    f"- {feature}: "
                    f"{values.get('old')} "
                    f"→ "
                    f"{values.get('new')}\n"
                )

        else:

            change_text = "No applicant features were modified.\n"

        # --------------------------------------------------
        # Build Original SHAP Section
        # --------------------------------------------------

        original_shap = ""

        for feature in original.get("top_features", []):

            original_shap += f"- {feature}\n"

        if not original_shap:

            original_shap = "No SHAP features available.\n"

        # --------------------------------------------------
        # Build Simulation SHAP Section
        # --------------------------------------------------

        simulation_shap = ""

        for feature in simulation.get("top_features", []):

            simulation_shap += f"- {feature}\n"

        if not simulation_shap:

            simulation_shap = "No SHAP features available.\n"

        # --------------------------------------------------
        # Build Prompt
        # --------------------------------------------------

        prompt = f"""
You are a Senior Credit Risk Analyst.

Your task is to explain the results of a hypothetical
"What-If" simulation produced by a Machine Learning
credit risk model.

====================================================
USER QUESTION
====================================================

{user_question}

====================================================
ORIGINAL PREDICTION
====================================================

Prediction:
{original.get("prediction")}

Repayment Probability:
{original.get("repayment_probability")}

Default Probability:
{original.get("default_probability")}

====================================================
SIMULATION PREDICTION
====================================================

Prediction:
{simulation.get("prediction")}

Repayment Probability:
{simulation.get("repayment_probability")}

Default Probability:
{simulation.get("default_probability")}

====================================================
FEATURE CHANGES
====================================================

{change_text}

====================================================
ORIGINAL TOP SHAP FEATURES
====================================================

{original_shap}

====================================================
SIMULATION TOP SHAP FEATURES
====================================================

{simulation_shap}

====================================================
COMPARISON
====================================================

Prediction Changed:
{comparison.get("prediction_changed")}

Repayment Probability Difference:
{comparison.get("repayment_probability_difference")}

Default Probability Difference:
{comparison.get("default_probability_difference")}

====================================================
INSTRUCTIONS
====================================================

Explain the simulation professionally.

Your explanation should include:

1. Describe what applicant information changed.

2. Explain whether the prediction changed.

3. Explain why the prediction did or did not change.

4. Discuss which features had the greatest influence
   according to SHAP.

5. Mention any remaining risk factors.

6. If the prediction did not change,
   explain why the modifications were insufficient.

7. If the prediction changed,
   explain which modifications produced the largest
   improvement or deterioration.

Rules:

- Use ONLY the supplied information.
- Never invent applicant data.
- Never invent banking policy.
- Do not mention internal model implementation.
- Keep the explanation suitable for banking
  professionals.
"""

        return prompt


# ==========================================================
# Testing
# ==========================================================

if __name__ == "__main__":

    builder = SimulationPrompt()

    simulation_result = {

        "original": {

            "prediction": "Rejected",

            "repayment_probability": 0.27,

            "default_probability": 0.73,

            "top_features": [

                "dti",

                "annual_inc",

                "sub_grade",

            ],

        },

        "simulation": {

            "prediction": "Approved",

            "repayment_probability": 0.81,

            "default_probability": 0.19,

            "top_features": [

                "annual_inc",

                "dti",

                "sub_grade",

            ],

        },

        "changes": {

            "annual_inc": {

                "old": 71000,

                "new": 95000,

            },

            "dti": {

                "old": 12,

                "new": 8,

            },

        },

        "comparison": {

            "prediction_changed": True,

            "repayment_probability_difference": 0.54,

            "default_probability_difference": -0.54,

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