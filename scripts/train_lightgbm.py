import joblib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = PROJECT_ROOT / "data" / "processed"

X_train = joblib.load(DATA_PATH / "X_train.pkl")
X_test = joblib.load(DATA_PATH / "X_test.pkl")
y_train = joblib.load(DATA_PATH / "y_train.pkl")
y_test = joblib.load(DATA_PATH / "y_test.pkl")

print(X_train.shape)
print(X_test.shape)


from lightgbm import LGBMClassifier
model = LGBMClassifier(
    class_weight="balanced",
    random_state=42,
    subsample=0.9,
    reg_lambda= 0,
    reg_alpha=1,
    num_leaves=31,
    n_estimators=300,
    min_child_samples= 20,
    max_depth= 5,
    learning_rate= 0.1,
    colsample_bytree=0.9

)

model.fit(
    X_train,
    y_train
)

y_pred = model.predict(X_test)



joblib.dump(
    model,
    PROJECT_ROOT / "models" / "lightgbm_model.pkl"
)
y_prob = model.predict_proba(X_test)[:, 1]

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

print("Accuracy :", accuracy_score(y_test, y_pred))

print(classification_report(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))

from sklearn.metrics import roc_auc_score

probs = model.predict_proba(X_test)[:, 1]

print(roc_auc_score(y_test, probs))

