
import matplotlib.pyplot as plt 
from pathlib import Path 
import pandas as pd


# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Dataset path
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "loan_dataset.csv"

# Load dataset
df = pd.read_csv(DATA_PATH)
print(df.dtypes)
print(df.columns)
print(df.info())
print(df.describe())
print(df.isnull().sum())
print(df["loan_status"].value_counts())
missing = df.isnull().sum().sort_values(ascending=False)

print(missing)
corr = df.corr(numeric_only=True)

