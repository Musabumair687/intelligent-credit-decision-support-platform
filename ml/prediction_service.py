
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
3. Loads imputation statistics.
4. Loads emp_length mapping.
5. Loads feature order.
6. Creates a SHAP explainer.
7. Performs prediction and explanation.

Key Design Principle
--------------------
Replicates the EXACT training preprocessing pipeline
internally. The frontend/orchestration can send RAW
data (same format as the original CSV) and this
service handles everything.
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

    DEFAULT_CLASS_INDEX = 1
    REPAYMENT_CLASS_INDEX = 0

    # Columns dropped during training (preprocessing + feature engineering)
    DROPPED_COLUMNS = [
        "installment",
        "grade",
        "emp_title",
        "issue_d",
        "title",
        "address",
        "earliest_cr_line",
    ]

    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent

        # -------------------------------------
        # Paths
        # -------------------------------------
        self.model_path = self.project_root / "models" / "lightgbm_model.pkl"
        self.encoder_path = self.project_root / "models" / "label_encoders.pkl"
        self.impute_path = self.project_root / "models" / "imputation_stats.pkl"
        self.emp_map_path = self.project_root / "models" / "emp_length_map.pkl"
        self.train_path = self.project_root / "data" / "processed" / "X_train.pkl"

        # -------------------------------------
        # Load Artifacts
        # -------------------------------------
        self.model = joblib.load(self.model_path)
        self.encoders = joblib.load(self.encoder_path)
        self.impute_stats = joblib.load(self.impute_path)
        self.emp_length_map = joblib.load(self.emp_map_path)

        # Feature order (fallback to X_train.pkl if feature_order.pkl absent)
        feature_order_path = self.project_root / "models" / "feature_order.pkl"
        if feature_order_path.exists():
            self.feature_order = joblib.load(feature_order_path)
        else:
            X_train = joblib.load(self.train_path)
            self.feature_order = list(X_train.columns)

        # -------------------------------------
        # SHAP Explainer
        # -------------------------------------
        self.explainer = shap.TreeExplainer(self.model)

    # ---------------------------------------------------------
    # Preprocess Raw Input (REPLICATES TRAINING PIPELINE)
    # ---------------------------------------------------------

    def preprocess_raw_input(self, applicant: dict):
        """
        Replicate the full training preprocessing:

        1. Drop columns not used by the model.
        2. Impute missing values using training statistics.
        3. Convert term: "36 months" -> 36.
        4. Map emp_length: "7 years" -> 7.
        """
        applicant = applicant.copy()

        # 1. Drop unused columns (silently ignore if missing)
        for col in self.DROPPED_COLUMNS:
            applicant.pop(col, None)

        # 2. Impute missing values using training statistics
        for col, val in self.impute_stats.items():
            if col not in applicant or applicant[col] is None or pd.isna(applicant[col]):
                applicant[col] = val

        # 3. Convert term: handle both "36 months" and 36
        term = applicant.get("term")
        if isinstance(term, str):
            applicant["term"] = int(term.lower().replace("months", "").strip())

        # 4. Map emp_length: handle both "7 years" and 7
        emp_length = applicant.get("emp_length")
        if isinstance(emp_length, str):
            mapped = self.emp_length_map.get(emp_length)
            if mapped is None:
                known = list(self.emp_length_map.keys())
                raise ValueError(
                    f"Unrecognized emp_length '{emp_length}'. "
                    f"Known values: {known}"
                )
            applicant["emp_length"] = mapped

        return applicant

    # ---------------------------------------------------------
    # Validate Applicant
    # ---------------------------------------------------------

    def validate_input(self, applicant: dict):
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
        applicant = applicant.copy()
        for column, encoder in self.encoders.items():
            raw_value = applicant.get(column)
            try:
                applicant[column] = int(encoder.transform([raw_value])[0])
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
        dataframe = pd.DataFrame([applicant])
        dataframe = dataframe[self.feature_order]
        return dataframe

    # ---------------------------------------------------------
    # Prepare Input
    # ---------------------------------------------------------

    def prepare_input(self, applicant: dict):
        """
        Complete preprocessing pipeline:
        Raw -> Preprocess -> Validate -> Encode -> DataFrame
        """
        preprocessed = self.preprocess_raw_input(applicant)
        self.validate_input(preprocessed)
        encoded = self.encode_features(preprocessed)
        dataframe = self.build_dataframe(encoded)
        return dataframe

    # ---------------------------------------------------------
    # Predict Probabilities
    # ---------------------------------------------------------

    def predict_probability(self, dataframe):
        probabilities = self.model.predict_proba(dataframe)[0]
        repayment_probability = float(probabilities[self.REPAYMENT_CLASS_INDEX])
        default_probability = float(probabilities[self.DEFAULT_CLASS_INDEX])
        return repayment_probability, default_probability

    # ---------------------------------------------------------
    # Business Decision
    # ---------------------------------------------------------

    def make_decision(self, repayment_probability: float, threshold: float = 0.60):
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
        raw_shap_values = self.explainer.shap_values(dataframe)
        expected_value = self.explainer.expected_value

        if isinstance(raw_shap_values, list):
            class_values = raw_shap_values[self.DEFAULT_CLASS_INDEX][0]
            base_value = (
                expected_value[self.DEFAULT_CLASS_INDEX]
                if isinstance(expected_value, (list, np.ndarray))
                else expected_value
            )
        else:
            values_array = np.array(raw_shap_values)
            if values_array.ndim == 3:
                class_values = values_array[0, :, self.DEFAULT_CLASS_INDEX]
                base_value = (
                    expected_value[self.DEFAULT_CLASS_INDEX]
                    if isinstance(expected_value, (list, np.ndarray))
                    else expected_value
                )
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
        dataframe = self.prepare_input(applicant)
        repayment_probability, default_probability = self.predict_probability(dataframe)
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

    # ============================================================
    # TEST 1: Low-Risk Applicant (should be APPROVED)
    # ============================================================
    applicant_low_risk = {
        "loan_amnt": 8000,
        "term": "36 months",
        "int_rate": 7.5,
        "sub_grade": "A2",
        "emp_length": "10+ years",
        "home_ownership": "MORTGAGE",
        "verification_status": "Verified",
        "annual_inc": 120000,
        "purpose": "debt_consolidation",
        "dti": 8.5,
        "open_acc": 12,
        "pub_rec": 0,
        "revol_bal": 2500,
        "revol_util": 15.0,
        "total_acc": 35,
        "initial_list_status": "w",
        "application_type": "INDIVIDUAL",
        "mort_acc": 3,
        "pub_rec_bankruptcies": 0,
    }

    # ============================================================
    # TEST 2: High-Risk Applicant (should be REJECTED)
    # ============================================================
    applicant_high_risk = {
        "loan_amnt": 35000,
        "term": "60 months",
        "int_rate": 28.99,
        "sub_grade": "G5",
        "emp_length": "< 1 year",
        "home_ownership": "RENT",
        "verification_status": "Not Verified",
        "annual_inc": 28000,
        "purpose": "small_business",
        "dti": 38.0,
        "open_acc": 4,
        "pub_rec": 3,
        "revol_bal": 18000,
        "revol_util": 92.0,
        "total_acc": 8,
        "initial_list_status": "f",
        "application_type": "INDIVIDUAL",
        "mort_acc": 0,
        "pub_rec_bankruptcies": 2,
    }

    # ============================================================
    # TEST 3: Missing Values (tests imputation logic)
    # ============================================================
    # emp_length, revol_util, mort_acc, pub_rec_bankruptcies are missing
    # The service should fill them from imputation_stats.pkl
    applicant_missing_values = {
        "loan_amnt": 15000,
        "term": "36 months",
        "int_rate": 14.5,
        "sub_grade": "C3",
        "emp_length": None,              # MISSING — should be imputed
        "home_ownership": "OWN",
        "verification_status": "Source Verified",
        "annual_inc": 65000,
        "purpose": "credit_card",
        "dti": 22.0,
        "open_acc": 9,
        "pub_rec": 1,
        "revol_bal": 8500,
        "revol_util": None,              # MISSING — should be imputed
        "total_acc": 22,
        "initial_list_status": "w",
        "application_type": "INDIVIDUAL",
        "mort_acc": None,                # MISSING — should be imputed
        "pub_rec_bankruptcies": None,    # MISSING — should be imputed
    }

    # ============================================================
    # TEST 4: Pre-Cleaned Numeric Inputs (no string conversion needed)
    # ============================================================
    # term is already 36 (int), emp_length is already 5 (int)
    # This verifies the service handles BOTH raw strings and pre-cleaned numbers
    applicant_pre_cleaned = {
        "loan_amnt": 20000,
        "term": 36,                      # Already numeric
        "int_rate": 11.2,
        "sub_grade": "B5",
        "emp_length": 5,                 # Already numeric
        "home_ownership": "MORTGAGE",
        "verification_status": "Verified",
        "annual_inc": 85000,
        "purpose": "home_improvement",
        "dti": 16.0,
        "open_acc": 11,
        "pub_rec": 0,
        "revol_bal": 12000,
        "revol_util": 35.0,
        "total_acc": 25,
        "initial_list_status": "w",
        "application_type": "INDIVIDUAL",
        "mort_acc": 1,
        "pub_rec_bankruptcies": 0,
    }

    # ============================================================
    # Run All Tests
    # ============================================================
    test_cases = [
        ("TEST 1 — Low Risk", applicant_low_risk),
        ("TEST 2 — High Risk", applicant_high_risk),
        ("TEST 3 — Missing Values", applicant_missing_values),
        ("TEST 4 — Pre-Cleaned Numeric", applicant_pre_cleaned),
    ]

    for label, applicant in test_cases:
        print("\n" + "=" * 80)
        print(label)
        print("=" * 80)

        try:
            result = service.predict(applicant)

            print(f"Prediction           : {result['prediction']}")
            print(f"Repayment Probability: {result['repayment_probability']:.4f}")
            print(f"Default Probability  : {result['default_probability']:.4f}")
            print(f"Threshold            : {result['threshold']}")
            print(f"Approved             : {result['approved']}")

            print("\nTop 5 SHAP Features:")
            for i, feature in enumerate(result["top_features"], 1):
                print(
                    f"  {i}. {feature['feature']:25s} "
                    f"value={feature['value']:>10}  "
                    f"shap={feature['shap']:>+10.4f}"
                )

        except Exception as e:
            print(f"ERROR: {e}")
    print()
    print("=" * 80)
    print("Top SHAP Features")
    print("=" * 80)
    print("Model classes:", service.model.classes_)

    for feature in result["top_features"]:
        print(feature)