"""
prediction_service.py

Purpose
-------
Provides a single service responsible for making
credit risk predictions using the trained
LightGBM model.

This service will:

1. Load the trained model.
2. Load Label Encoders.
3. Load feature order.
4. Create a SHAP explainer.
5. Later perform prediction and explanation.

Author
------
Intelligent Credit Decision Support Platform
"""

import joblib
import shap

from pathlib import Path


class PredictionService:
    """
    Central prediction service for the
    Intelligent Credit Decision Support Platform.
    """

    def __init__(self):
        """
        Load every resource only once.

        These objects remain in memory for
        future predictions.
        """

        # -------------------------------------
        # Project Paths
        # -------------------------------------

        self.project_root = (
            Path(__file__).resolve().parent.parent
        )

        self.model_path = (
            self.project_root
            / "models"
            / "lightgbm_model.pkl"
        )

        self.encoder_path = (
            self.project_root
            / "models"
            / "label_encoders.pkl"
        )

        self.train_path = (
            self.project_root
            / "data"
            / "processed"
            / "X_train.pkl"
        )

        # -------------------------------------
        # Load Model
        # -------------------------------------

        self.model = joblib.load(
            self.model_path
        )

        # -------------------------------------
        # Load Encoders
        # -------------------------------------

        self.encoders = joblib.load(
            self.encoder_path
        )

        # -------------------------------------
        # Load Training Features
        # -------------------------------------

        self.X_train = joblib.load(
            self.train_path
        )

        # -------------------------------------
        # Store Feature Order
        # -------------------------------------

        self.feature_order = list(
            self.X_train.columns
        )

        # -------------------------------------
        # SHAP Explainer
        # -------------------------------------

        self.explainer = shap.TreeExplainer(
            self.model
        )
        # ---------------------------------------------------------
    # Validate Applicant
    # ---------------------------------------------------------

    def validate_input(
        self,
        applicant: dict,
    ):
        """
        Ensure every required feature exists.
        """

        missing_features = []

        for feature in self.feature_order:

            if feature not in applicant:

                missing_features.append(feature)

        if missing_features:

            raise ValueError(

                f"Missing Features : {missing_features}"

            )

    # ---------------------------------------------------------
    # Encode Categories
    # ---------------------------------------------------------

    def encode_features(
        self,
        applicant: dict,
    ):
        """
        Encode categorical features using
        stored LabelEncoders.
        """

        applicant = applicant.copy()

        for column, encoder in self.encoders.items():

            applicant[column] = int(

                encoder.transform(

                    [applicant[column]]

                )[0]

            )

        return applicant

    # ---------------------------------------------------------
    # Build DataFrame
    # ---------------------------------------------------------

    def build_dataframe(
        self,
        applicant: dict,
    ):
        """
        Convert applicant dictionary into
        a one-row DataFrame.
        """

        import pandas as pd

        dataframe = pd.DataFrame(

            [applicant]

        )

        dataframe = dataframe[

            self.feature_order

        ]

        return dataframe

    # ---------------------------------------------------------
    # Prepare Input
    # ---------------------------------------------------------

    def prepare_input(
        self,
        applicant: dict,
    ):
        """
        Complete preprocessing pipeline.

        Validation

        →

        Encoding

        →

        DataFrame
        """

        self.validate_input(

            applicant

        )

        encoded = self.encode_features(

            applicant

        )

        dataframe = self.build_dataframe(

            encoded

        )

        return dataframe
    
        # ---------------------------------------------------------
    # Predict Probabilities
    # ---------------------------------------------------------

    def predict_probability(
        self,
        dataframe,
    ):
        """
        Predict repayment and default probabilities.

        Returns
        -------
        tuple
            (
                repayment_probability,
                default_probability
            )
        """

        probabilities = self.model.predict_proba(
            dataframe
        )[0]

        default_probability = float(
            probabilities[1]
        )

        repayment_probability = float(
            probabilities[0]
        )

        return (

            repayment_probability,

            default_probability,

        )

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

        approved = (

            repayment_probability >= threshold

        )

        prediction = (

            "Approved"

            if approved

            else "Rejected"

        )

        return {

            "prediction": prediction,

            "approved": approved,

            "threshold": threshold,

        }

    # ---------------------------------------------------------
    # Predict
    # ---------------------------------------------------------

        # ---------------------------------------------------------
    # Complete Prediction Pipeline
    # ---------------------------------------------------------

    def predict(
        self,
        applicant: dict,
    ):
        """
        Complete prediction pipeline.
        """

        dataframe = self.prepare_input(
            applicant
        )

        (

            repayment_probability,

            default_probability,

        ) = self.predict_probability(
            dataframe
        )

        decision = self.make_decision(
            repayment_probability
        )

        explanation = self.explain_prediction(
            dataframe
        )

        top_features = self.extract_top_features(
            explanation
        )

        return {

            **decision,

            "repayment_probability":
                repayment_probability,

            "default_probability":
                default_probability,

            "prepared_dataframe":
                dataframe,

            "shap_explanation":
                explanation,

            "top_features":
                top_features,

        }
    
        # ---------------------------------------------------------
    # Generate SHAP Explanation
    # ---------------------------------------------------------

    def explain_prediction(
        self,
        dataframe,
    ):
        """
        Generate SHAP explanation for a prediction.

        Returns
        -------
        shap.Explanation
        """

        shap_values = self.explainer.shap_values(dataframe)

        # LightGBM Binary Classification
        if isinstance(shap_values, list):
            shap_values = shap_values[1]

        explanation = shap.Explanation(

            values=shap_values[0],

            base_values=self.explainer.expected_value,

            data=dataframe.iloc[0],

            feature_names=dataframe.columns,

        )

        return explanation

    # ---------------------------------------------------------
    # Extract Top Features
    # ---------------------------------------------------------

    def extract_top_features(
        self,
        explanation,
        top_k: int = 5,
    ):
        """
        Extract top SHAP features.

        Returns
        -------
        list[dict]
        """

        import numpy as np

        importance = np.abs(explanation.values)

        ranked_index = np.argsort(
            importance
        )[::-1]

        features = []

        for index in ranked_index[:top_k]:

            features.append(

                {

                    "feature":
                        explanation.feature_names[index],

                    "value":
                        explanation.data.iloc[index],

                    "shap":
                        float(explanation.values[index]),

                    "importance":
                        float(
                            abs(
                                explanation.values[index]
                            )
                        ),

                }

            )

        return features
    

if __name__ == "__main__":

    service = PredictionService()

    applicant = {

        "loan_amnt":12000,

        "term":36,

        "int_rate":13.33,

        "sub_grade":"B3",

        "emp_length":7,

        "home_ownership":"MORTGAGE",

        "verification_status":"Verified",

        "annual_inc":71000,

        "purpose":"debt_consolidation",

        "dti":12,

        "open_acc":10,

        "pub_rec":0,

        "revol_bal":6000,

        "revol_util":41,

        "total_acc":28,

        "initial_list_status":"w",

        "application_type":"INDIVIDUAL",

        "mort_acc":2,

        "pub_rec_bankruptcies":0

    }

    result = service.predict(
        applicant
    )

    print("=" * 80)
    print("Prediction")
    print("=" * 80)

    print(
        result["prediction"]
    )

    print()

    print(
        "Repayment Probability :",
        result["repayment_probability"]
    )

    print(
        "Default Probability :",
        result["default_probability"]
    )

    print()

    print("=" * 80)
    print("Top SHAP Features")
    print("=" * 80)

    for feature in result["top_features"]:

        print(feature)

        