

import pandas as pd 
from pathlib import Path
import numpy as np 
import matplotlib.pyplot as plt 
import joblib

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "loan_dataset.csv"
df = pd.read_csv(DATA_PATH)

df = df.drop(["installment","grade","emp_title","issue_d","title","address"], axis=1)
print(df.columns)

# Compute imputation values FIRST (before filling, so we capture true training stats)
emp_length_mode      = df["emp_length"].mode()[0]
revol_util_median    = df["revol_util"].median()
pub_rec_bankruptcies_mode = df["pub_rec_bankruptcies"].mode()[0]
mort_acc_median      = df["mort_acc"].median()

# Apply imputation
df["emp_length"] = df["emp_length"].fillna(emp_length_mode)
df["revol_util"] = df["revol_util"].fillna(revol_util_median)
df["pub_rec_bankruptcies"] = df["pub_rec_bankruptcies"].fillna(pub_rec_bankruptcies_mode)
df["mort_acc"] = df["mort_acc"].fillna(mort_acc_median)

print(df.isnull().sum())

# Save cleaned data
CLEAN_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_data.csv"
df.to_csv(CLEAN_PATH, index=False)

# Save imputation statistics for inference
IMPUTE_PATH = PROJECT_ROOT / "models" / "imputation_stats.pkl"
joblib.dump({
    "emp_length": emp_length_mode,
    "revol_util": revol_util_median,
    "pub_rec_bankruptcies": pub_rec_bankruptcies_mode,
    "mort_acc": mort_acc_median,
}, IMPUTE_PATH)

print("Cleaned dataset saved successfully!")
print(f"Imputation stats saved to: {IMPUTE_PATH}")