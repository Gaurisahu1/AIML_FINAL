# ShopEasy Smart Notifications

> **"Send less. Mean more."**
> A modern, demo-ready intelligent e-commerce notification system that learns individual engagement habits, detects fading interest early, and personalizes alert categories and frequency to prevent customer churn.

---

## 3 Short Steps to Run

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the application**:
   ```bash
   python run.py
   ```
   *(This automatically generates the dataset, trains the model if needed, starts the FastAPI server on `http://127.0.0.1:8000`, and opens your web browser).*

3. **Run automated acceptance tests**:
   ```bash
   pytest tests/test_scenarios.py
   ```

## Deploy to Vercel

The FastAPI app can be deployed from the repository root using Vercel's Python
runtime. The `.python-version` file selects Python 3.12, and the scikit-learn
version is pinned to match the saved model.

```bash
npx vercel
```

Follow the CLI prompts to log in and link or create a Vercel project. Deploy to
production with:

```bash
npx vercel --prod
```

The demo stores simulation state in memory, so state changes are temporary and
may not be shared across server instances.

---

## Architecture Overview
- **Backend**: Python 3.10+, FastAPI, pandas, scikit-learn, joblib.
- **Frontend**: Standalone HTML5, CSS3, and Vanilla JavaScript (offline-ready, zero build step, zero CDN, inline SVGs, system fonts).
- **Intelligence Engine**: 21-day rolling feature extraction, scikit-learn risk prediction model, and a recency-weighted policy decision layer.
- **Reports & Artifacts**:
  - `reports/model_report.md`: Detailed offline machine learning comparison and feature importances.
  - `reports/open_rates_by_persona.png`: Weekly open rates by persona over 90 days.
  - `reports/unsubscribed_over_time.png`: Cumulative unsubscribe rate over time.
