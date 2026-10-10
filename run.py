"""
ShopEasy Smart Notifications - One-Command Entry Point
Automatically checks and prepares datasets and trained artifacts,
launches the FastAPI application, and opens the interactive dashboard in your browser.
"""

import os
import sys
import threading
import time
import webbrowser

# Add current folder to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    print("=" * 65)
    print("      ShopEasy Smart Notifications - Prototype Runner")
    print("      'Send less. Mean more.'")
    print("=" * 65)

    # 1. Check / generate dataset
    notif_csv = os.path.join(PROJECT_ROOT, "data", "notifications.csv")
    cust_csv = os.path.join(PROJECT_ROOT, "data", "customers.csv")
    if not (os.path.exists(notif_csv) and os.path.exists(cust_csv)):
        print("\n[Step 1/3] Synthetic dataset missing. Generating now...")
        from data.generate_data import generate_dataset
        generate_dataset(
            output_dir=os.path.join(PROJECT_ROOT, "data"),
            reports_dir=os.path.join(PROJECT_ROOT, "reports")
        )
    else:
        print("\n[Step 1/3] Dataset verified: data/notifications.csv present.")

    # 2. Check / train model
    model_path = os.path.join(PROJECT_ROOT, "models", "risk_model.joblib")
    if not os.path.exists(model_path):
        print("\n[Step 2/3] Risk prediction model missing. Training now...")
        from ml.train_model import build_snapshots, train_and_evaluate
        snap_df = build_snapshots(data_dir=os.path.join(PROJECT_ROOT, "data"))
        train_and_evaluate(
            snap_df,
            models_dir=os.path.join(PROJECT_ROOT, "models"),
            reports_dir=os.path.join(PROJECT_ROOT, "reports")
        )
    else:
        print("[Step 2/3] Model verified: models/risk_model.joblib present.")

    # 3. Launch server and open browser
    url = "http://127.0.0.1:8000"
    print(f"\n[Step 3/3] Starting ShopEasy server at {url}...")

    def open_browser():
        time.sleep(1.2)
        print(f"Opening browser at {url}...")
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False, log_level="info")


if __name__ == "__main__":
    main()
