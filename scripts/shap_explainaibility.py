import joblib
import shap
import matplotlib.pyplot as plt

from pathlib import Path

# =====================================================
# Project Paths
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = PROJECT_ROOT / "models" / "lightgbm_model.pkl"

DATA_PATH = PROJECT_ROOT / "data" / "processed"

REPORT_PATH = PROJECT_ROOT / "reports"

# =====================================================
# Load Model
# =====================================================

model = joblib.load(MODEL_PATH)

# =====================================================
# Load Data
# =====================================================

X_train = joblib.load(DATA_PATH / "X_train.pkl")

X_test = joblib.load(DATA_PATH / "X_test.pkl")

# =====================================================
# Create SHAP Explainer
# =====================================================

explainer = shap.TreeExplainer(model)

# =====================================================
# Calculate SHAP Values
# =====================================================

shap_values = explainer.shap_values(X_test)

print("SHAP values calculated successfully!")

# =====================================================
# Summary Plot
# =====================================================

plt.figure(figsize=(12,8))

shap.summary_plot(
    shap_values,
    X_test,
    show=False
)

plt.tight_layout()

plt.savefig(
    REPORT_PATH / "shap_summary.png",
    dpi=300
)

plt.close()

# =====================================================
# Bar Plot
# =====================================================

plt.figure(figsize=(12,8))

shap.summary_plot(
    shap_values,
    X_test,
    plot_type="bar",
    show=False
)

plt.tight_layout()

plt.savefig(
    REPORT_PATH / "shap_bar.png",
    dpi=300
)

plt.close()

# =====================================================
# Waterfall Plot
# =====================================================

sample_index = 0

explanation = shap.Explanation(

    values=shap_values[sample_index],

    base_values=explainer.expected_value,

    data=X_test.iloc[sample_index],

    feature_names=X_test.columns

)

plt.figure(figsize=(10,8))

shap.plots.waterfall(
    explanation,
    show=False
)

plt.savefig(
    REPORT_PATH / "shap_waterfall.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("SHAP plots saved successfully!")