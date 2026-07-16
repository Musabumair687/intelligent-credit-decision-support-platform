"""
feature_engineering.py

Purpose
-------
Performs feature engineering required for the
LightGBM Credit Risk Model.

This script:

1. Converts text features into numerical values.
2. Encodes categorical variables.
3. Saves LabelEncoders for inference.
4. Removes unused columns.
5. Saves engineered dataset.

Author
------
Intelligent Credit Decision Support Platform
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# ==========================================================
# Project Paths
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cleaned_data.csv"
)

FEATURE_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "feature_engineered_data.csv"
)

ENCODER_PATH = (
    PROJECT_ROOT
    / "models"
    / "label_encoders.pkl"
)

# ==========================================================
# Load Dataset
# ==========================================================

df = pd.read_csv(DATA_PATH)

# ==========================================================
# Convert Loan Term
# ==========================================================

df["term"] = (
    df["term"]
    .str.replace("months", "", regex=False)
    .str.strip()
    .astype(int)
)

# ==========================================================
# Employment Length Mapping
# ==========================================================

emp_length_mapping = {

    "< 1 year": 0,

    "1 year": 1,

    "2 years": 2,

    "3 years": 3,

    "4 years": 4,

    "5 years": 5,

    "6 years": 6,

    "7 years": 7,

    "8 years": 8,

    "9 years": 9,

    "10+ years": 10,

}

df["emp_length"] = df["emp_length"].map(emp_length_mapping)

# ==========================================================
# Target Encoding
# ==========================================================

loan_status_mapping = {

    "Charged Off": 1,

    "Fully Paid": 0,

}

df["loan_status"] = df["loan_status"].map(
    loan_status_mapping
)

# ==========================================================
# Label Encoding
# ==========================================================

categorical_columns = [

    "sub_grade",

    "home_ownership",

    "verification_status",

    "purpose",

    "initial_list_status",

    "application_type",

]

# Dictionary that stores every encoder
encoders = {}

for column in categorical_columns:

    encoder = LabelEncoder()

    df[column] = encoder.fit_transform(
        df[column]
    )

    encoders[column] = encoder

# ==========================================================
# Remove Unused Columns
# ==========================================================

df = df.drop(
    columns=["earliest_cr_line"]
)

# ==========================================================
# Save Feature Engineered Dataset
# ==========================================================

df.to_csv(
    FEATURE_PATH,
    index=False,
)

# ==========================================================
# Save Encoders
# ==========================================================

joblib.dump(
    encoders,
    ENCODER_PATH,
)

print("=" * 80)
print("Feature Engineering Completed")
print("=" * 80)

print(f"\nDataset Saved : {FEATURE_PATH}")

print(f"Encoders Saved: {ENCODER_PATH}")

print("\nStored Encoders:")

for name in encoders:

    print(f"  • {name}")