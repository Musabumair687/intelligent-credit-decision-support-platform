import pandas as pd
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_data.csv"

df = pd.read_csv(DATA_PATH)

print(df.head())

df["term"]=df["term"].str.replace("months","").astype(int)
print(df["term"].head())

print(sorted(df["emp_length"].unique()))
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
    "10+ years": 10
}

df["emp_length"] = df["emp_length"].map(emp_length_mapping)

loan_status_mapping = {
    "Charged Off": 1,   # Positive class (default)
    "Fully Paid": 0     # Negative class
}

df["loan_status"] = df["loan_status"].map(loan_status_mapping)

print(df["emp_length"].head())
categorical_columns = [
    "sub_grade",
    "home_ownership",
    "verification_status",
    "purpose",
    "initial_list_status",
    "application_type"
]
from sklearn.preprocessing import LabelEncoder

label_encoder = LabelEncoder()

for col in categorical_columns:
    df[col] = label_encoder.fit_transform(df[col])

print(df.head())
print(df.dtypes)

print(df["earliest_cr_line"].head())
print(df["earliest_cr_line"].nunique())

df = df.drop("earliest_cr_line", axis=1) 


FEATURE_PATH = PROJECT_ROOT / "data" / "processed" / "feature_engineered_data.csv"

df.to_csv(FEATURE_PATH, index=False)

print("Feature engineered dataset saved successfully!")
