from pathlib import Path 
import pandas as pd


# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Dataset path
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "loan_dataset.csv"

# Load dataset
df = pd.read_csv(DATA_PATH)

print("Dataset Loaded Successfully!")
print(f"Rows: {df.shape[0]}")
print(f"Columns: {df.shape[1]}")

print(df.head())
print(df.dtypes)
print(df.columns)
print(df.isnull().sum())
print(df["mort_acc"].head())
