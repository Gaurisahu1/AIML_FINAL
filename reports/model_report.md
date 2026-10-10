# ShopEasy Risk Prediction Model Report

## 1. Executive Summary
This internal technical report documents the machine learning risk prediction model that detects customer churn and promotional fatigue in the ShopEasy Smart Notifications platform.

Customers who are drifting away from engagement are flagged as high risk so that notification volumes and content can be proactively adapted before they unsubscribe.

---

## 2. Dataset and Snapshot Configuration
- **Total Customers**: 600
- **Total Snapshots Generated**: 4800
- **Window Length**: Trailing 21 days for feature computation.
- **Snapshot Cadence**: Every 7 days from day 21 to day 76.
- **Target Label**: `1` if customer unsubscribes or opens < 5% of promotional notifications in the subsequent 14 days, else `0`.
- **Temporal Train/Test Split**:
  - **Train Set (Snapshots <= Day 55)**: 3000 samples (33.6% positive class)
  - **Test Set (Snapshots > Day 55)**: 1800 samples (46.6% positive class)

---

## 3. Model Comparison Table
The evaluation below reflects test set performance on unseen future snapshots (temporal split):

| Model | Precision | Recall | F1 Score | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Logistic Regression (Selected)** | 0.961 | 0.970 | **0.966** | Standardized baseline |
| **Decision Tree** | 0.932 | 0.983 | **0.957** | Optimal hyperparams via 5-fold CV |
| **K-Nearest Neighbors** | 0.978 | 0.954 | **0.966** | Standardized baseline |

---

## 4. Winning Model Confusion Matrix (Logistic Regression)
- **True Negatives (TN)**: 928 (Active customers correctly predicted active)
- **False Positives (FP)**: 33 (Active customers flagged as at-risk)
- **False Negatives (FN)**: 25 (At-risk customers missed)
- **True Positives (TP)**: 814 (At-risk customers correctly intercepted)

```
                Predicted Active (0)    Predicted At-Risk (1)
Actual Active (0)       928                     33             
Actual At-Risk (1)      25                      814            
```

---

## 5. Feature Importances & Decision Logic
### Feature Importance Ranking (Decision Tree)
- `consecutive_ignore_streak`: 0.9034 ███████████████████████████
- `open_rate_21d            `: 0.0729 ██
- `days_since_last_open     `: 0.0237 
- `open_rate_7d             `: 0.0000 
- `trend_7d_vs_14d          `: 0.0000 
- `open_rate_offer          `: 0.0000 
- `open_rate_new_arrival    `: 0.0000 
- `open_rate_price_drop     `: 0.0000 
- `open_rate_order_update   `: 0.0000 
- `avg_view_seconds         `: 0.0000 
- `click_rate               `: 0.0000 
- `mute_count               `: 0.0000 
- `dismissed_share          `: 0.0000 

### Decision Tree Top Rules (Truncated View)
```
|--- consecutive_ignore_streak <= 4.50
|   |--- open_rate_21d <= 0.36
|   |   |--- days_since_last_open <= 4.50
|   |   |   |--- class: 1
|   |   |--- days_since_last_open >  4.50
|   |   |   |--- class: 1
|   |--- open_rate_21d >  0.36
|   |   |--- days_since_last_open <= 5.50
|   |   |   |--- class: 0
|   |   |--- days_since_last_open >  5.50
|   |   |   |--- class: 1
|--- consecutive_ignore_streak >  4.50
|   |--- consecutive_ignore_streak <= 8.50
|   |   |--- open_rate_21d <= 0.31
|   |   |   |--- class: 1
|   |   |--- open_rate_21d >  0.31
|   |   |   |--- class: 1
|   |--- consecutive_ignore_streak >  8.50
|   |   |--- consecutive_ignore_streak <= 9.50
|   |   |   |--- class: 1
|   |   |--- consecutive_ignore_streak >  9.50
|   |   |   |--- class: 1

```

---

## 6. Risk Level Calibration for Application Runtime
The winning model outputs calibrated probability $p \in [0, 1]$ which is categorized into three business action tiers:
- **Low Risk ($p < 0.35$)**: High natural engagement; receive balanced personalized notifications (8–10/week).
- **Medium Risk ($0.35 \le p \le 0.65$)**: Cooling engagement; reduce volume (4–5/week) and focus on favorite types.
- **High Risk ($p > 0.65$)**: Immediate churn risk; pause all promotional alerts, sending only essential order updates (2/week) and optional re-engagement message.
