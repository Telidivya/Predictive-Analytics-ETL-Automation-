"""Train a simple baseline model to estimate transaction failure probability."""
from pathlib import Path
import json
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.metrics import confusion_matrix
import joblib
from src.etl_pipeline import load_data, transform_data, ROOT, DATA

REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

def main():
    df = transform_data(load_data())
    features = ["transaction_hour", "amount", "risk_score", "payment_method",
                "bank", "region", "device_type", "is_weekend", "amount_band", "time_band"]
    X, y = df[features], df["is_failed"]
    numeric = ["transaction_hour", "amount", "risk_score", "is_weekend"]
    categorical = [c for c in features if c not in numeric]
    preprocessor = ColumnTransformer([
        ("num", Pipeline([("imputer", SimpleImputer(strategy="median")),
                          ("scale", StandardScaler())]), numeric),
        ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                          ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical)
    ])
    model = Pipeline([("prep", preprocessor),
                      ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced"))])
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model.fit(X_train, y_train)
    prob = model.predict_proba(X_test)[:, 1]
    pred = (prob >= 0.5).astype(int)
    metrics = {
        "test_rows": int(len(y_test)),
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, prob)),
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
        "note": "Metrics are from synthetic demo data; they are not evidence of production performance."
    }
    (REPORTS / "model_metrics.json").write_text(json.dumps(metrics, indent=2))
    joblib.dump(model, REPORTS / "failure_prediction_model.joblib")
    scored = df.copy()
    scored["predicted_failure_probability"] = model.predict_proba(X)[:, 1]
    scored.to_csv(DATA / "scored_transactions.csv", index=False)
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
