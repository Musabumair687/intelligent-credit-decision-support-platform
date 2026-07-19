"""
prediction_service.py

Purpose
-------
Provides a single service responsible for making
credit risk predictions using the trained
LightGBM model.

This service:

1. Loads the trained model.
2. Loads Label Encoders.
3. Loads feature order.
4. Creates a SHAP explainer.
5. Performs prediction and explanation.

Fixes applied in this version
------------------------------
1. explain_prediction now handles all three SHAP output
   shapes seen across SHAP versions for a binary classifier:
   - list of two arrays (older API)
   - 3D ndarray (n_samples, n_features, n_classes) (newer API)
   - plain 2D ndarray (n_samples, n_features) (some model/
     explainer combinations return only the positive class)
   The previous version only handled the first case and would
   index incorrectly (or crash) on the others.

2. base_values is now indexed consistently with whichever
   shape branch was taken above, instead of always assuming
   expected_value is a 2-element list.

3. encode_features now raises a clear, specific error when a
   categorical value was never seen during training, instead
   of letting sklearn's internal ValueError surface with no
   context about which feature/value caused it.

4. A CLASS_INDEX section documents explicitly which predicted
   class index corresponds to "default" vs "repayment", since
   this is currently just assumed based on training-time label
   encoding and was previously undocumented anywhere in code.
   ADAPT THIS to match how your label encoder actually encoded
   the target column — verify with label_encoders.pkl / your
   training notebook before trusting it in production.

Author
------
Intelligent Credit Decision Support Platform
"""

import joblib
import numpy as np
import pandas as pd
import shap

from pathlib import Path


class PredictionService:
    """
    Central prediction service for the
    Intelligent Credit Decision Support Platform.
    """

    # -------------------------------------------------------
    # IMPORTANT: verify this against your actual training
    # pipeline's label encoding for the target column before
    # relying on it. model.predict_proba(...)[0] returns
    # probabilities in class-index order; this constant says
    # which index is which outcome.
    # -------------------------------------------------------
    DEFAULT_CLASS_INDEX = 1
    REPAYMENT_CLASS_INDEX = 0

    def __init__(self):
        """
        Load every resource only once.

        These objects remain in memory for
        future predictions.
        """

        # -------------------------------------
        # Project Paths
        # -------------------------------------

        self.project_root = Path(__file__).resolve().parent.parent

        self.model_path = (
            self.project_root / "models" / "lightgbm_model.pkl"
        )

        self.encoder_path = (
            self.project_root / "models" / "label_encoders.pkl"
        )

        self.train_path = (
            self.project_root / "data" / "processed" / "X_train.pkl"
        )

        # -------------------------------------
        # Load Model
        # -------------------------------------

        self.model = joblib.load(self.model_path)

        # -------------------------------------
        # Load Encoders
        # -------------------------------------

        self.encoders = joblib.load(self.encoder_path)

        # -------------------------------------
        # Load Training Features / Feature Order
        # -------------------------------------
        #
        # NOTE: this still loads the full X_train.pkl just to
        # read .columns. For a lighter production footprint,
        # consider persisting feature_order as its own small
        # artifact (e.g. feature_order.json) at training time
        # and loading that instead. Left as-is here to avoid
        # requiring a re-export you may not have yet, but flag
        # this as a follow-up.

        self.X_train = joblib.load(self.train_path)

        self.feature_order = list(self.X_train.columns)

        # -------------------------------------
        # SHAP Explainer
        # -------------------------------------

        self.explainer = shap.TreeExplainer(self.model)

    # ---------------------------------------------------------
    # Validate Applicant
    # ---------------------------------------------------------

    def validate_input(self, applicant: dict):
        """
        Ensure every required feature exists.
        """

        missing_features = [
            feature for feature in self.feature_order
            if feature not in applicant
        ]

        if missing_features:
            raise ValueError(f"Missing Features : {missing_features}")

    # ---------------------------------------------------------
    # Encode Categories
    # ---------------------------------------------------------

    def encode_features(self, applicant: dict):
        """
        Encode categorical features using stored LabelEncoders.

        Raises a clear, specific error if a category was never
        seen during training, rather than letting sklearn's
        internal ValueError surface with no context.
        """

        applicant = applicant.copy()

        for column, encoder in self.encoders.items():

            raw_value = applicant.get(column)

            try:

                applicant[column] = int(
                    encoder.transform([raw_value])[0]
                )

            except ValueError as error:

                known_values = list(getattr(encoder, "classes_", []))

                raise ValueError(
                    f"Unrecognized value '{raw_value}' for feature "
                    f"'{column}'. Known values: {known_values}. "
                    f"Original error: {error}"
                ) from error

        return applicant

    # ---------------------------------------------------------
    # Build DataFrame
    # ---------------------------------------------------------

    def build_dataframe(self, applicant: dict):
        """
        Convert applicant dictionary into a one-row DataFrame,
        ordered to match the model's expected feature order.
        """

        dataframe = pd.DataFrame([applicant])

        dataframe = dataframe[self.feature_order]

        return dataframe

    # ---------------------------------------------------------
    # Prepare Input
    # ---------------------------------------------------------

    def prepare_input(self, applicant: dict):
        """
        Complete preprocessing pipeline.

        Validation -> Encoding -> DataFrame
        """

        self.validate_input(applicant)

        encoded = self.encode_features(applicant)

        dataframe = self.build_dataframe(encoded)

        return dataframe

    # ---------------------------------------------------------
    # Predict Probabilities
    # ---------------------------------------------------------

    def predict_probability(self, dataframe):
        """
        Predict repayment and default probabilities.

        Returns
        -------
        tuple
            (repayment_probability, default_probability)
        """

        probabilities = self.model.predict_proba(dataframe)[0]

        repayment_probability = float(
            probabilities[self.REPAYMENT_CLASS_INDEX]
        )

        default_probability = float(
            probabilities[self.DEFAULT_CLASS_INDEX]
        )

        return repayment_probability, default_probability

    # ---------------------------------------------------------
    # Business Decision
    # ---------------------------------------------------------

    def make_decision(
        self,
        repayment_probability: float,
        threshold: float = 0.60,
    ):
        """
        Apply business approval threshold.
        """

        approved = repayment_probability >= threshold

        prediction = "Approved" if approved else "Rejected"

        return {
            "prediction": prediction,
            "approved": approved,
            "threshold": threshold,
        }

    # ---------------------------------------------------------
    # Generate SHAP Explanation
    # ---------------------------------------------------------

    def explain_prediction(self, dataframe):
        """
        Generate a SHAP explanation for a single-row prediction,
        normalized to always represent the DEFAULT_CLASS_INDEX
        class, regardless of which SHAP output shape this
        version of the shap library / explainer returns.

        Returns
        -------
        shap.Explanation
        """

        raw_shap_values = self.explainer.shap_values(dataframe)

        expected_value = self.explainer.expected_value

        # --- Case 1: list of arrays, one per class (older API) ---
        if isinstance(raw_shap_values, list):

            class_values = raw_shap_values[self.DEFAULT_CLASS_INDEX][0]

            base_value = (
                expected_value[self.DEFAULT_CLASS_INDEX]
                if isinstance(expected_value, (list, np.ndarray))
                else expected_value
            )

        else:

            values_array = np.array(raw_shap_values)

            # --- Case 2: 3D array (n_samples, n_features, n_classes) ---
            if values_array.ndim == 3:

                class_values = values_array[0, :, self.DEFAULT_CLASS_INDEX]

                base_value = (
                    expected_value[self.DEFAULT_CLASS_INDEX]
                    if isinstance(expected_value, (list, np.ndarray))
                    else expected_value
                )

            # --- Case 3: plain 2D array (n_samples, n_features) ---
            else:

                class_values = values_array[0]

                base_value = (
                    expected_value[0]
                    if isinstance(expected_value, (list, np.ndarray))
                    else expected_value
                )

        explanation = shap.Explanation(
            values=class_values,
            base_values=base_value,
            data=dataframe.iloc[0],
            feature_names=dataframe.columns,
        )

        return explanation

    # ---------------------------------------------------------
    # Extract Top Features
    # ---------------------------------------------------------

    def extract_top_features(self, explanation, top_k: int = 5):
        """
        Extract the top_k most influential SHAP features by
        absolute contribution.

        Returns
        -------
        list[dict]
        """

        importance = np.abs(explanation.values)

        ranked_index = np.argsort(importance)[::-1]

        features = []

        for index in ranked_index[:top_k]:

            features.append({
                "feature": explanation.feature_names[index],
                "value": explanation.data.iloc[index],
                "shap": float(explanation.values[index]),
                "importance": float(abs(explanation.values[index])),
            })

        return features

    # ---------------------------------------------------------
    # Complete Prediction Pipeline
    # ---------------------------------------------------------

    def predict(self, applicant: dict):
        """
        Complete prediction pipeline.
        """

        dataframe = self.prepare_input(applicant)

        repayment_probability, default_probability = (
            self.predict_probability(dataframe)
        )

        decision = self.make_decision(repayment_probability)

        explanation = self.explain_prediction(dataframe)

        top_features = self.extract_top_features(explanation)

        return {
            **decision,
            "repayment_probability": repayment_probability,
            "default_probability": default_probability,
            "prepared_dataframe": dataframe,
            "shap_explanation": explanation,
            "top_features": top_features,
        }


if __name__ == "__main__":

    service = PredictionService()

    applicant = {
        "loan_amnt": 12000,
        "term": 36,
        "int_rate": 13.33,
        "sub_grade": "B3",
        "emp_length": 7,
        "home_ownership": "MORTGAGE",
        "verification_status": "Verified",
        "annual_inc": 71000,
        "purpose": "debt_consolidation",
        "dti": 12,
        "open_acc": 10,
        "pub_rec": 0,
        "revol_bal": 6000,
        "revol_util": 41,
        "total_acc": 28,
        "initial_list_status": "w",
        "application_type": "INDIVIDUAL",
        "mort_acc": 2,
        "pub_rec_bankruptcies": 0,
    }

    result = service.predict(applicant)

    print("=" * 80)
    print("Prediction")
    print("=" * 80)
    print(result["prediction"])

    print()
    print("Repayment Probability :", result["repayment_probability"])
    print("Default Probability :", result["default_probability"])

    print()
    print("=" * 80)
    print("Top SHAP Features")
    print("=" * 80)

    for feature in result["top_features"]:
        print(feature)