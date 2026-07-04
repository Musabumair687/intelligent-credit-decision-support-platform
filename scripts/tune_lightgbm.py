import joblib
from pathlib import Path

from lightgbm import LGBMClassifier

from sklearn.model_selection import RandomizedSearchCV

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix
)

# =====================================================
# Project Paths
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = PROJECT_ROOT / "data" / "processed"

MODEL_PATH = PROJECT_ROOT / "models"

# =====================================================
# Load Dataset
# =====================================================

X_train = joblib.load(DATA_PATH / "X_train.pkl")
X_test = joblib.load(DATA_PATH / "X_test.pkl")

y_train = joblib.load(DATA_PATH / "y_train.pkl")
y_test = joblib.load(DATA_PATH / "y_test.pkl")

print("Training Shape :", X_train.shape)
print("Testing Shape  :", X_test.shape)

# =====================================================
# Base LightGBM Model
# =====================================================

model = LGBMClassifier(
    class_weight="balanced",
    random_state=42,
    verbose=-1
)

# =====================================================
# Hyperparameter Search Space
# =====================================================

param_grid = {

    "n_estimators": [100, 200, 300, 500],

    "learning_rate": [0.01, 0.03, 0.05, 0.1],

    "num_leaves": [31, 50, 70, 100],

    "max_depth": [-1, 5, 10, 15],

    "min_child_samples": [20, 30, 50],

    "subsample": [0.8, 0.9, 1.0],

    "colsample_bytree": [0.8, 0.9, 1.0],

    "reg_alpha": [0, 0.1, 1],

    "reg_lambda": [0, 0.1, 1]
}

# =====================================================
# Random Search
# =====================================================

random_search = RandomizedSearchCV(

    estimator=model,

    param_distributions=param_grid,

    n_iter=25,

    scoring="roc_auc",

    cv=5,

    verbose=2,

    random_state=42,

    n_jobs=-1

)

print("\nStarting Hyperparameter Tuning...\n")

random_search.fit(X_train, y_train)

# =====================================================
# Best Parameters
# =====================================================

print("\nBest Parameters\n")
print(random_search.best_params_)

print("\nBest Cross Validation ROC-AUC\n")
print(random_search.best_score_)

# =====================================================
# Best Model
# =====================================================

best_model = random_search.best_estimator_

# =====================================================
# Prediction
# =====================================================

y_pred = best_model.predict(X_test)

y_prob = best_model.predict_proba(X_test)[:, 1]

# =====================================================
# Evaluation
# =====================================================

print("\n========== Test Results ==========\n")

print(f"Accuracy : {accuracy_score(y_test, y_pred):.4f}")
from sklearn.metrics import roc_auc_score

probs = model.predict_proba(X_test)[:, 1]

print(roc_auc_score(y_test, probs))



print("\nClassification Report\n")

print(classification_report(y_test, y_pred))

print("\nConfusion Matrix\n")

print(confusion_matrix(y_test, y_pred))

# =====================================================
# Save Model
# =====================================================

joblib.dump(
    best_model,
    MODEL_PATH / "best_lightgbm_model.pkl"
)

print("\nBest model saved successfully!")