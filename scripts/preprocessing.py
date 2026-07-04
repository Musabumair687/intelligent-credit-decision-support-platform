import pandas as pd 
from pathlib import Path
import numbers as np 
import matplotlib.pyplot as plt 
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "loan_dataset.csv"
df = pd.read_csv(DATA_PATH)

df = df.drop(["installment","grade","emp_title","issue_d","title","address"], axis=1)
print(df.columns)


df["emp_length"] = df["emp_length"].fillna(
    df["emp_length"].mode()[0]
)

df["revol_util"] = df["revol_util"].fillna(
    df["revol_util"].median()
)

df["pub_rec_bankruptcies"] = df[
    "pub_rec_bankruptcies"
].fillna(
    df["pub_rec_bankruptcies"].mode()[0]
)

df["mort_acc"] = df["mort_acc"].fillna(
    df["mort_acc"].median()
)

print(df.isnull().sum())


CLEAN_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_data.csv"

df.to_csv(CLEAN_PATH, index=False)

print("Cleaned dataset saved successfully!")