
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