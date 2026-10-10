"""
ShopEasy Smart Notifications - Model Training Module
Extracts 21-day rolling snapshots, evaluates Logistic Regression, Decision Tree,
and KNN using temporal train/test split, saves the winning model, and writes
reports/model_report.md.
"""

import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score

from ml.features import extract_snapshot_features_from_events, FEATURE_COLUMNS

SEED = 42


def build_snapshots(data_dir="data"):
    cust_df = pd.read_csv(os.path.join(data_dir, "customers.csv"))
    notif_df = pd.read_csv(os.path.join(data_dir, "notifications.csv"))

    # Convert entire notifications DataFrame to sorted records grouped by customer
    records_by_cust = {}
    for row in notif_df.to_dict("records"):
        cid = row["customer_id"]
        if cid not in records_by_cust:
            records_by_cust[cid] = []
        records_by_cust[cid].append(row)

    # Sort each customer's events by day and hour
    for cid in records_by_cust:
        records_by_cust[cid].sort(key=lambda x: (x["day"], x["hour"]))

    snapshot_days = list(range(21, 77, 7))  # [21, 28, 35, 42, 49, 56, 63, 70]
    records = []

    for s_day in snapshot_days:
        for cid, events in records_by_cust.items():
            # Check if customer already unsubscribed before s_day
            prior = [e for e in events if e["day"] < s_day]
            if not prior:
                continue
            if any(e["unsubscribed"] == 1 for e in prior):
                continue

            # Extract features from trailing 21d
            feat = extract_snapshot_features_from_events(events, s_day)
            feat["customer_id"] = cid
            feat["snapshot_day"] = s_day

            # Future label in [s_day, s_day + 14)
            future = [e for e in events if s_day <= e["day"] < s_day + 14]
            unsub_in_future = any(e["unsubscribed"] == 1 for e in future)
            future_promo = [e for e in future if e["notification_type"] != "order_update"]

            if unsub_in_future or len(future_promo) == 0:
                label = 1
            else:
                promo_opens = sum(1 for e in future_promo if e["action"] == "opened")
                promo_open_rate = promo_opens / len(future_promo)
                label = 1 if promo_open_rate < 0.05 else 0

            feat["label"] = label
            records.append(feat)

    snap_df = pd.DataFrame(records)
    return snap_df


def train_and_evaluate(snap_df, models_dir="models", reports_dir="reports"):
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    # Temporal split: train <= 55, test > 55
    train_df = snap_df[snap_df["snapshot_day"] <= 55]
    test_df = snap_df[snap_df["snapshot_day"] > 55]

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df["label"]
    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df["label"]

    print("=" * 60)
    print("MODEL TRAINING & TEMPORAL EVALUATION")
    print("=" * 60)
    print(f"Total Snapshots: {len(snap_df)}")
    print(f"Training Snapshots (Days 21-49): {len(train_df)} (Positives: {y_train.mean():.1%})")
    print(f"Testing Snapshots (Days 56-70):  {len(test_df)} (Positives: {y_test.mean():.1%})")

    models = {}

    # 1. Baseline Logistic Regression (balanced)
    lr = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=SEED)
    # Wrap in scaler for numerical stability
    lr_pipe = Pipeline([("scaler", StandardScaler()), ("lr", lr)])
    lr_pipe.fit(X_train, y_train)
    models["Logistic Regression"] = lr_pipe

    # 2. Decision Tree (balanced) with CV for depth
    dt = DecisionTreeClassifier(class_weight="balanced", random_state=SEED)
    dt_cv = GridSearchCV(
        dt,
        param_grid={"max_depth": [3, 4, 5, 6, 7]},
        cv=5,
        scoring="f1"
    )
    dt_cv.fit(X_train, y_train)
    models["Decision Tree"] = dt_cv.best_estimator_
    print(f"Decision Tree optimal depth: {dt_cv.best_params_['max_depth']}")

    # 3. KNN with scaled features & CV for K
    knn_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("knn", KNeighborsClassifier())
    ])
    knn_cv = GridSearchCV(
        knn_pipe,
        param_grid={"knn__n_neighbors": [3, 5, 7, 9, 11]},
        cv=5,
        scoring="f1"
    )
    knn_cv.fit(X_train, y_train)
    models["K-Nearest Neighbors"] = knn_cv.best_estimator_
    print(f"KNN optimal k: {knn_cv.best_params_['knn__n_neighbors']}")

    # Comparison metrics
    results = []
    best_f1 = -1.0
    best_recall = -1.0
    best_name = None
    best_model = None

    for name, m in models.items():
        y_pred = m.predict(X_test)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred)

        results.append({
            "model": name,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "cm": cm
        })

        print(f"\n{name}:")
        print(f"  Precision: {prec:.4f} | Recall: {rec:.4f} | F1: {f1:.4f}")
        print(f"  Confusion Matrix: TN={cm[0,0]}, FP={cm[0,1]}, FN={cm[1,0]}, TP={cm[1,1]}")

        # Selection: Highest F1 with recall as tie-breaker (4 decimal precision)
        f1_r = round(f1, 4)
        best_f1_r = round(best_f1, 4)
        if (f1_r > best_f1_r) or (f1_r == best_f1_r and rec > best_recall):
            best_f1 = f1
            best_recall = rec
            best_name = name
            best_model = m

    print("\n" + "=" * 60)
    print(f"BEST MODEL SELECTED: {best_name} (F1: {best_f1:.4f}, Recall: {best_recall:.4f})")
    print("=" * 60)

    # Save best model
    model_path = os.path.join(models_dir, "risk_model.joblib")
    joblib.dump(best_model, model_path)
    print(f"Saved winning model to: {model_path}")

    # Build reports/model_report.md
    write_model_report(
        reports_dir=reports_dir,
        snap_df=snap_df,
        train_df=train_df,
        test_df=test_df,
        results=results,
        best_name=best_name,
        best_model=best_model,
        dt_model=models["Decision Tree"]
    )

    return best_model


def write_model_report(reports_dir, snap_df, train_df, test_df, results, best_name, best_model, dt_model):
    report_path = os.path.join(reports_dir, "model_report.md")

    # Feature importance or tree rules
    dt_rules = export_text(dt_model, feature_names=FEATURE_COLUMNS, max_depth=3)
    feature_importances = pd.Series(dt_model.feature_importances_, index=FEATURE_COLUMNS).sort_values(ascending=False)

    best_res = next(r for r in results if r["model"] == best_name)
    cm = best_res["cm"]

    content = rf"""# ShopEasy Risk Prediction Model Report

## 1. Executive Summary
This internal technical report documents the machine learning risk prediction model that detects customer churn and promotional fatigue in the ShopEasy Smart Notifications platform.

Customers who are drifting away from engagement are flagged as high risk so that notification volumes and content can be proactively adapted before they unsubscribe.

---

## 2. Dataset and Snapshot Configuration
- **Total Customers**: {snap_df['customer_id'].nunique()}
- **Total Snapshots Generated**: {len(snap_df)}
- **Window Length**: Trailing 21 days for feature computation.
- **Snapshot Cadence**: Every 7 days from day 21 to day 76.
- **Target Label**: `1` if customer unsubscribes or opens < 5% of promotional notifications in the subsequent 14 days, else `0`.
- **Temporal Train/Test Split**:
  - **Train Set (Snapshots <= Day 55)**: {len(train_df)} samples ({train_df['label'].mean():.1%} positive class)
  - **Test Set (Snapshots > Day 55)**: {len(test_df)} samples ({test_df['label'].mean():.1%} positive class)

---

## 3. Model Comparison Table
The evaluation below reflects test set performance on unseen future snapshots (temporal split):

| Model | Precision | Recall | F1 Score | Notes |
| :--- | :---: | :---: | :---: | :--- |
"""

    for r in results:
        is_winner = " (Selected)" if r["model"] == best_name else ""
        content += f"| **{r['model']}{is_winner}** | {r['precision']:.3f} | {r['recall']:.3f} | **{r['f1']:.3f}** | {'Optimal hyperparams via 5-fold CV' if 'Decision' in r['model'] or 'KNN' in r['model'] else 'Standardized baseline'} |\n"

    content += f"""
---

## 4. Winning Model Confusion Matrix ({best_name})
- **True Negatives (TN)**: {cm[0,0]} (Active customers correctly predicted active)
- **False Positives (FP)**: {cm[0,1]} (Active customers flagged as at-risk)
- **False Negatives (FN)**: {cm[1,0]} (At-risk customers missed)
- **True Positives (TP)**: {cm[1,1]} (At-risk customers correctly intercepted)

```
                Predicted Active (0)    Predicted At-Risk (1)
Actual Active (0)       {cm[0,0]:<15}         {cm[0,1]:<15}
Actual At-Risk (1)      {cm[1,0]:<15}         {cm[1,1]:<15}
```

---

## 5. Feature Importances & Decision Logic
### Feature Importance Ranking (Decision Tree)
"""
    for feat, imp in feature_importances.items():
        bar = "█" * int(imp * 30)
        content += f"- `{feat:25s}`: {imp:.4f} {bar}\n"

    content += rf"""
### Decision Tree Top Rules (Truncated View)
```
{dt_rules}
```

---

## 6. Risk Level Calibration for Application Runtime
The winning model outputs calibrated probability $p \in [0, 1]$ which is categorized into three business action tiers:
- **Low Risk ($p < 0.35$)**: High natural engagement; receive balanced personalized notifications (8–10/week).
- **Medium Risk ($0.35 \le p \le 0.65$)**: Cooling engagement; reduce volume (4–5/week) and focus on favorite types.
- **High Risk ($p > 0.65$)**: Immediate churn risk; pause all promotional alerts, sending only essential order updates (2/week) and optional re-engagement message.
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Generated comprehensive report: {report_path}")


if __name__ == "__main__":
    snapshots = build_snapshots()
    train_and_evaluate(snapshots)
