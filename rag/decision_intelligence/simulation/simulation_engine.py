# """
# simulation_engine.py

# Purpose
# -------
# Performs "What-If" simulations for loan applicants.

# Instead of explaining a prediction,
# this module creates a modified version of an
# applicant, runs the prediction again,
# and compares both results.

# The Simulation Engine DOES NOT use an LLM.

# It ONLY communicates with the Prediction Service.

# Pipeline
# --------

# Original Applicant
#         │
#         ▼
# Copy Applicant
#         │
#         ▼
# Apply User Changes
#         │
#         ▼
# Prediction Service
#         │
#         ▼
# Compare Predictions
#         │
#         ▼
# Return Structured Comparison

# Author
# ------
# Intelligent Credit Decision Support Platform
# """

# import copy

# from ml.prediction_service import PredictionService


# class SimulationEngine:
#     """
#     Performs hypothetical loan simulations.

#     This class never loads the ML model directly.

#     Instead it delegates all prediction work
#     to PredictionService.
#     """

#     def __init__(self):
#         """
#         Initialize Prediction Service.
#         """

#         self.prediction_service = PredictionService()

#     # ---------------------------------------------------------
#     # Private Helpers
#     # ---------------------------------------------------------

#     def _copy_applicant(
#         self,
#         applicant: dict,
#     ) -> dict:
#         """
#         Create a deep copy of an applicant.

#         Parameters
#         ----------
#         applicant : dict

#         Returns
#         -------
#         dict
#         """

#         return copy.deepcopy(applicant)

#     # ---------------------------------------------------------

#     def _apply_changes(
#         self,
#         applicant: dict,
#         changes: dict,
#     ) -> dict:
#         """
#         Apply user supplied changes.

#         Example
#         -------

#         changes =

#         {

#             "annual_inc":80000,

#             "dti":18

#         }

#         Parameters
#         ----------
#         applicant : dict

#         changes : dict

#         Returns
#         -------
#         dict
#         """

#         simulated_applicant = self._copy_applicant(applicant)

#         for feature, value in changes.items():

#             if feature in simulated_applicant:

#                 simulated_applicant[feature] = value

#         return simulated_applicant

#     # ---------------------------------------------------------

#     def _build_change_summary(
#         self,
#         original: dict,
#         simulated: dict,
#     ) -> dict:
#         """
#         Compare original and simulated applicants.

#         Returns only modified fields.

#         Example
#         -------

#         {

#             "annual_inc":{

#                 "old":50000,

#                 "new":80000

#             }

#         }
#         """

#         summary = {}

#         for feature in original:

#             original_value = original.get(feature)

#             simulated_value = simulated.get(feature)

#             if original_value != simulated_value:

#                 summary[feature] = {

#                     "old": original_value,

#                     "new": simulated_value,

#                 }

#         return summary

#     # ---------------------------------------------------------

#     def simulate(
#         self,
#         applicant: dict,
#         changes: dict,
#     ) -> dict:
#         """
#         Perform a What-If simulation.

#         Parameters
#         ----------
#         applicant : dict

#             Original applicant.

#         changes : dict

#             Hypothetical changes.

#         Returns
#         -------
#         dict

#         Structure

#         {

#             "original":...,

#             "simulation":...,

#             "changes":...

#         }

#         """

#         # ---------------------------------------------
#         # Step 1
#         # Build simulated applicant
#         # ---------------------------------------------

#         simulated_applicant = self._apply_changes(

#             applicant=applicant,

#             changes=changes,

#         )

#         # ---------------------------------------------
#         # Step 2
#         # Predict original applicant
#         # ---------------------------------------------

#         original_result = self.prediction_service.predict(

#             applicant

#         )

#         # ---------------------------------------------
#         # Step 3
#         # Predict simulated applicant
#         # ---------------------------------------------

#         simulated_result = self.prediction_service.predict(

#             simulated_applicant

#         )
#         # ---------------------------------------------
#         # Step 4
#         # Build change summary
#         # ---------------------------------------------

#         change_summary = self._build_change_summary(

#             original=applicant,

#             simulated=simulated_applicant,

#         )

#         # ---------------------------------------------
#         # Step 5
#         # Build comparison object
#         # ---------------------------------------------

#         comparison = {

#             "original": original_result,

#             "simulation": simulated_result,

#             "changes": change_summary,

#         }

#         return comparison


# # ==========================================================
# # Testing
# # ==========================================================

# if __name__ == "__main__":

#     engine = SimulationEngine()

#     applicant = {

#     "loan_amnt":12000,

#     "term":36,

#     "int_rate":13.33,

#     "sub_grade":"B3",

#     "emp_length":7,

#     "home_ownership":"MORTGAGE",

#     "verification_status":"Verified",

#     "annual_inc":71000,

#     "purpose":"debt_consolidation",

#     "dti":12,

#     "open_acc":10,

#     "pub_rec":0,

#     "revol_bal":6000,

#     "revol_util":41,

#     "total_acc":28,

#     "initial_list_status":"w",

#     "application_type":"INDIVIDUAL",

#     "mort_acc":2,

#     "pub_rec_bankruptcies":0

# }

#     changes = {

#         "annual_inc": 95000,

#         "dti": 8,

#     }

#     result = engine.simulate(

#         applicant=applicant,

#         changes=changes,

#     )

#     print("=" * 80)
#     print("SIMULATION RESULT")
#     print("=" * 80)

#     print("\nOriginal Prediction")
#     print("-" * 80)

#     print(result["original"]["prediction"])

#     print(

#     f"Repayment Probability : "

#     f"{result['original']['repayment_probability']:.4f}"

# )

#     print(
    
#         f"Default Probability : "
    
#         f"{result['original']['default_probability']:.4f}"
    
#     )

#     print("\nSimulation Prediction")
#     print("-" * 80)
    
#     print(result["simulation"]["prediction"])
    
#     print(
#         f"Repayment Probability : "
#         f"{result['simulation']['repayment_probability']:.4f}"
#     )
    
#     print(
#         f"Default Probability : "
#         f"{result['simulation']['default_probability']:.4f}"
#     )

#     print("\nChanged Features")
#     print("-" * 80)

#     for feature, values in result["changes"].items():

#         print(

#             f"{feature} : "

#             f"{values['old']}"

#             f" -> "

#             f"{values['new']}"

#         )
"""
simulation_engine.py

Purpose
-------
Performs What-If simulations for loan applicants.

Instead of explaining an existing prediction,
this engine creates a modified version of an
applicant, predicts again using the ML model,
and prepares a rich comparison object for
the LLM.

Author
------
Intelligent Credit Decision Support Platform
"""

import copy

from ml.prediction_service import PredictionService


class SimulationEngine:
    """
    Performs hypothetical applicant simulations.
    """

    def __init__(self):

        self.prediction_service = PredictionService()

    # ==========================================================
    # Applicant Helpers
    # ==========================================================

    def _copy_applicant(
        self,
        applicant: dict,
    ) -> dict:
        """
        Create a deep copy of the applicant.
        """

        return copy.deepcopy(applicant)

    # ----------------------------------------------------------

    def _apply_changes(
        self,
        applicant: dict,
        changes: dict,
    ) -> dict:
        """
        Apply hypothetical feature changes.
        """

        simulated = self._copy_applicant(applicant)

        for feature, value in changes.items():

            if feature in simulated:

                simulated[feature] = value

        return simulated

    # ==========================================================
    # Change Summary
    # ==========================================================

    def _build_change_summary(
        self,
        original: dict,
        simulated: dict,
    ) -> dict:
        """
        Build detailed feature changes.
        """

        summary = {}

        for feature in original:

            old = original.get(feature)
            new = simulated.get(feature)

            if old != new:

                direction = (
                    "Increase"
                    if new > old
                    else "Decrease"
                    if new < old
                    else "No Change"
                )

                percentage = None

                if isinstance(old, (int, float)):

                    if old != 0:

                        percentage = round(

                            ((new - old) / old) * 100,

                            2,

                        )

                summary[feature] = {

                    "old": old,

                    "new": new,

                    "direction": direction,

                    "percentage_change": percentage,

                }

        return summary

    # ==========================================================
    # Applicant Summary
    # ==========================================================

    def _build_applicant_summary(
        self,
        applicant: dict,
    ) -> dict:
        """
        Build a compact applicant summary
        for prompt generation.
        """

        return {

            "loan_amount":
                applicant.get("loan_amnt"),

            "interest_rate":
                applicant.get("int_rate"),

            "term":
                applicant.get("term"),

            "sub_grade":
                applicant.get("sub_grade"),

            "purpose":
                applicant.get("purpose"),

            "annual_income":
                applicant.get("annual_inc"),

            "dti":
                applicant.get("dti"),

        }

    # ==========================================================
    # Comparison Builder
    # ==========================================================

    def _build_comparison(
        self,
        original: dict,
        simulation: dict,
    ) -> dict:
        """
        Build comparison statistics.
        """

        original_prediction = original["prediction"]

        simulation_prediction = simulation["prediction"]

        prediction_changed = (

            original_prediction != simulation_prediction

        )

        repayment_difference = round(

            simulation["repayment_probability"]
            -
            original["repayment_probability"],

            4,

        )

        default_difference = round(

            simulation["default_probability"]
            -
            original["default_probability"],

            4,

        )

        if repayment_difference > 0:

            risk_change = "Lower Risk"

        elif repayment_difference < 0:

            risk_change = "Higher Risk"

        else:

            risk_change = "No Change"

        return {

            "prediction_changed":

                prediction_changed,

            "decision_transition":

                f"{original_prediction} → {simulation_prediction}",

            "repayment_probability_difference":

                repayment_difference,

            "default_probability_difference":

                default_difference,

            "risk_change":

                risk_change,

        }

    # ==========================================================
    # SHAP Comparison
    # ==========================================================

    def _build_shap_comparison(
        self,
        original: dict,
        simulation: dict,
    ):
        """
        Placeholder.

        In Version 2 this method will compare
        actual SHAP contribution values.

        Currently it compares the top features.
        """

        return {

            "original_top_features":

                original.get("top_features", []),

            "simulation_top_features":

                simulation.get("top_features", []),

        }

    # ==========================================================
    # simulate()
    # ==========================================================
    def simulate(
        self,
        applicant: dict,
        changes: dict,
    ) -> dict:
        """
        Perform a complete What-If simulation.

        Parameters
        ----------
        applicant : dict
            Original applicant.

        changes : dict
            User requested hypothetical changes.

        Returns
        -------
        dict
            Rich simulation result.
        """

        # =====================================================
        # Step 1
        # Create simulated applicant
        # =====================================================

        simulated_applicant = self._apply_changes(

            applicant=applicant,

            changes=changes,

        )

        # =====================================================
        # Step 2
        # Predict original applicant
        # =====================================================

        original_prediction = self.prediction_service.predict(

            applicant

        )

        # =====================================================
        # Step 3
        # Predict simulated applicant
        # =====================================================

        simulation_prediction = self.prediction_service.predict(

            simulated_applicant

        )

        # =====================================================
        # Step 4
        # Build feature change summary
        # =====================================================

        change_summary = self._build_change_summary(

            original=applicant,

            simulated=simulated_applicant,

        )

        # =====================================================
        # Step 5
        # Build applicant summary
        # =====================================================

        applicant_summary = self._build_applicant_summary(

            applicant

        )

        # =====================================================
        # Step 6
        # Build prediction comparison
        # =====================================================

        comparison = self._build_comparison(

            original=original_prediction,

            simulation=simulation_prediction,

        )

        # =====================================================
        # Step 7
        # Build SHAP comparison
        # =====================================================

        shap_comparison = self._build_shap_comparison(

            original=original_prediction,

            simulation=simulation_prediction,

        )

        # =====================================================
        # Step 8
        # Build final response
        # =====================================================

        return {

            "original":

                original_prediction,

            "simulation":

                simulation_prediction,

            "changes":

                change_summary,

            "comparison":

                comparison,

            "applicant_summary":

                applicant_summary,

            "shap_comparison":

                shap_comparison,

        }