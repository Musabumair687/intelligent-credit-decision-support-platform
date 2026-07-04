import joblib
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path

# =====================================================
# Project Paths
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = PROJECT_ROOT / "models" / "lightgbm_model.pkl"

DATA_PATH = PROJECT_ROOT / "data" / "processed" / "X_train.pkl"

REPORT_PATH = PROJECT_ROOT / "reports"

# =====================================================
# Load Model and Training Features
# =====================================================

model = joblib.load(MODEL_PATH)

X_train = joblib.load(DATA_PATH)

# =====================================================
# Get Feature Importance
# =====================================================

importance = model.feature_importances_

# =====================================================
# Create DataFrame
# =====================================================

feature_df = pd.DataFrame({

    "Feature": X_train.columns,

    "Importance": importance

})

# =====================================================
# Sort Features
# =====================================================

feature_df = feature_df.sort_values(
    by="Importance",
    ascending=False
)

print(feature_df)

# =====================================================
# Save CSV
# =====================================================

feature_df.to_csv(
    REPORT_PATH / "feature_importance.csv",
    index=False
)

# =====================================================
# Plot Graph
# =====================================================

plt.figure(figsize=(10,8))

plt.barh(
    feature_df["Feature"],
    feature_df["Importance"]
)

plt.gca().invert_yaxis()

plt.title("LightGBM Feature Importance")

plt.xlabel("Importance Score")

plt.tight_layout()

plt.savefig(
    REPORT_PATH / "feature_importance.png",
    dpi=300
)

plt.show()

print("Feature importance saved successfully.")