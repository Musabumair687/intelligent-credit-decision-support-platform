# import pandas as pd
# from pathlib import Path

# from sklearn.model_selection import train_test_split



# PROJECT_ROOT = Path(__file__).resolve().parent.parent

# DATA_PATH = PROJECT_ROOT / "data" / "processed" / "feature_engineered_data.csv"

# df = pd.read_csv(DATA_PATH)

# X = df.drop("loan_status", axis=1)

# y = df["loan_status"]


# print(X.shape)
# print(y.shape)

# X_train, X_test, y_train, y_test = train_test_split(
#     X,
#     y,
#     test_size=0.2,
#     random_state=42,
#     stratify=y
# )
# print(f"X_train: {X_train.shape}")
# print(f"X_test : {X_test.shape}")
# print(f"y_train: {y_train.shape}")
# print(f"y_test : {y_test.shape}")
# print(y_train.value_counts(normalize=True))
# print()




# import joblib

# SAVE_PATH = PROJECT_ROOT / "data" / "processed"

# joblib.dump(X_train, SAVE_PATH / "X_train.pkl")
# joblib.dump(X_test, SAVE_PATH / "X_test.pkl")

# joblib.dump(y_train, SAVE_PATH / "y_train.pkl")
# joblib.dump(y_test, SAVE_PATH / "y_test.pkl")

# print("Train-Test split saved successfully!")

import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
import joblib

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "feature_engineered_data.csv"
df = pd.read_csv(DATA_PATH)

X = df.drop("loan_status", axis=1)
y = df["loan_status"]

print(X.shape)
print(y.shape)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"X_train: {X_train.shape}")
print(f"X_test : {X_test.shape}")
print(f"y_train: {y_train.shape}")
print(f"y_test : {y_test.shape}")
print(y_train.value_counts(normalize=True))
print()

SAVE_PATH = PROJECT_ROOT / "data" / "processed"
joblib.dump(X_train, SAVE_PATH / "X_train.pkl")
joblib.dump(X_test, SAVE_PATH / "X_test.pkl")
joblib.dump(y_train, SAVE_PATH / "y_train.pkl")
joblib.dump(y_test, SAVE_PATH / "y_test.pkl")

# Save feature order as a lightweight artifact for inference
FEATURE_ORDER_PATH = PROJECT_ROOT / "models" / "feature_order.pkl"
joblib.dump(list(X_train.columns), FEATURE_ORDER_PATH)

print("Train-Test split saved successfully!")
print(f"Feature order saved to: {FEATURE_ORDER_PATH}")