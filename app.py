"""
ShopEasy Smart Notifications - FastAPI Application
Serves API routes, session simulation state, policy engine integration,
and static web files (plain HTML/CSS/vanilla JS).
"""

import os
import copy
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from engine.scenarios import (
    CUSTOMERS,
    generate_week_notifications,
    get_scripted_action_for_customer,
    WEEK_SCHEDULE
)
from engine.policy import (
    PolicyEngine,
    ALL_TYPES,
    TYPE_DISPLAY_NAMES,
    STANDARD_BUNDLE_VOLUME,
    FREQUENCY_LOW_RISK,
    FREQUENCY_MEDIUM_RISK,
    FREQUENCY_HIGH_RISK
)
from engine.messages import get_message_for_customer

app = FastAPI(title="ShopEasy Smart Notifications")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
MODEL_PATH = os.path.join(BASE_DIR, "models", "risk_model.joblib")

# Initialize Policy Engine
policy_engine = PolicyEngine(model_path=MODEL_PATH)

# =====================================================================
# IN-MEMORY DEMO STATE
# =====================================================================

def init_customer_state(cust_meta):
    cid = cust_meta["id"]
    return {
        "id": cid,
        "name": cust_meta["name"],
        "initials": cust_meta["initials"],
        "role_hint": cust_meta["role_hint"],
        "current_week": 1,
        "is_finished": False,
        "is_unsubscribed": False,
        "history": [],
        "active_week_notifications": generate_week_notifications(cid, 1),
        "continued_rounds": 0,
        "continued_notifications": None,
        "analysis": None
    }


def create_initial_state():
    customers_dict = {}
    for c in CUSTOMERS:
        customers_dict[c["id"]] = init_customer_state(c)

    return {
        "customers": customers_dict,
        "selected_customer_id": "aarav",
        "system_run": False,
        "standard_bundle": generate_standard_bundle()
    }


def generate_standard_bundle():
    """Generates the generic 12-notification broadcast bundle before personalization."""
    bundle_types = [
        "offer", "offer", "new_arrival", "offer", "price_drop", "order_update",
        "offer", "new_arrival", "offer", "new_arrival", "price_drop", "order_update"
    ]
    bundle = []
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    times = ["9:00 AM", "11:30 AM", "2:15 PM", "5:00 PM", "7:30 PM", "8:45 PM"]
    for i, t in enumerate(bundle_types):
        bundle.append({
            "id": f"std_{i+1}",
            "type": t,
            "type_name": TYPE_DISPLAY_NAMES[t],
            "day": days[i % len(days)],
            "time": times[i % len(times)],
            "text": get_message_for_customer("broadcast", t, i)
        })
    return bundle


STATE = create_initial_state()


def compute_summary_metrics():
    counts = {
        "engaged": 0,
        "losing_interest": 0,
        "at_risk": 0,
        "unsubscribed": 0,
        "not_played": 0,
        "total_avoided": 0
    }
    for cid, cust in STATE["customers"].items():
        if cust.get("analysis"):
            status = cust["analysis"]["status"]
            counts[status] = counts.get(status, 0) + 1
            if status != "unsubscribed":
                counts["total_avoided"] += cust["analysis"].get("avoided_notifications", 0)
        else:
            counts["not_played"] += 1
    return counts


# =====================================================================
# API ROUTES
# =====================================================================

@app.get("/api/state")
def get_state():
    """Returns the current simulation and analysis state."""
    cust_list = []
    for cid, c in STATE["customers"].items():
        summary_card = {
            "id": c["id"],
            "name": c["name"],
            "initials": c["initials"],
            "role_hint": c["role_hint"],
            "current_week": c["current_week"],
            "is_finished": c["is_finished"],
            "is_unsubscribed": c["is_unsubscribed"],
            "status": c["analysis"]["status"] if c.get("analysis") else "not_played",
            "status_label": c["analysis"]["status_label"] if c.get("analysis") else "Not played",
            "frequency": c["analysis"]["frequency"] if c.get("analysis") else 0
        }
        cust_list.append(summary_card)

    sel_id = STATE["selected_customer_id"]
    sel_cust = STATE["customers"].get(sel_id)

    return {
        "customers": cust_list,
        "selected_customer": sel_cust,
        "system_run": STATE["system_run"],
        "summary_metrics": compute_summary_metrics(),
        "standard_bundle": STATE["standard_bundle"]
    }


@app.post("/api/customer/{customer_id}/select")
def select_customer(customer_id: str):
    if customer_id not in STATE["customers"]:
        raise HTTPException(status_code=404, detail="Customer not found")
    STATE["selected_customer_id"] = customer_id
    return {"ok": True, "selected_customer_id": customer_id}


class WeekSubmission(BaseModel):
    actions: List[Dict[str, Any]]


@app.post("/api/customer/{customer_id}/submit-week")
def submit_week(customer_id: str, submission: WeekSubmission):
    cust = STATE["customers"].get(customer_id)
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")

    if cust["is_finished"]:
        return {"ok": True, "message": "Customer already completed"}

    # Update active week notifications with submitted actions
    active_notifs = cust["active_week_notifications"]
    actions_map = {a["id"]: a for a in submission.actions}

    for n in active_notifs:
        if n["id"] in actions_map:
            act_info = actions_map[n["id"]]
            n["action"] = act_info.get("action", "ignored")
            n["duration"] = act_info.get("duration", "few_seconds")
            n["timing"] = act_info.get("timing", "right_away")
            n["clicked"] = bool(act_info.get("clicked", False))
            n["saved"] = bool(act_info.get("saved", False))

            if n["action"] == "unsubscribed":
                cust["is_unsubscribed"] = True

    # Save to history
    cust["history"].append({
        "week": cust["current_week"],
        "notifications": active_notifs
    })

    if cust["is_unsubscribed"] or cust["current_week"] >= 5:
        cust["is_finished"] = True
        cust["active_week_notifications"] = []
    else:
        cust["current_week"] += 1
        cust["active_week_notifications"] = generate_week_notifications(customer_id, cust["current_week"])

    # If system is already running, re-analyze immediately
    if STATE["system_run"]:
        cust["analysis"] = policy_engine.analyze_customer(
            customer_id, cust["name"], cust["history"], cust["is_unsubscribed"]
        )
        generate_next_week_notifications(cust)

    return {"ok": True, "customer": cust}


@app.post("/api/customer/{customer_id}/auto-play")
def auto_play_customer(customer_id: str):
    cust = STATE["customers"].get(customer_id)
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")

    # If guest, guest plays with balanced engagement
    while not cust["is_finished"]:
        w = cust["current_week"]
        notifs = generate_week_notifications(customer_id, w)
        for n in notifs:
            act = get_scripted_action_for_customer(customer_id, w, n)
            n.update(act)
            if n["action"] == "unsubscribed":
                cust["is_unsubscribed"] = True

        cust["history"].append({"week": w, "notifications": notifs})
        if cust["is_unsubscribed"] or w >= 5:
            cust["is_finished"] = True
            cust["active_week_notifications"] = []
            break
        else:
            cust["current_week"] += 1

    if STATE["system_run"]:
        cust["analysis"] = policy_engine.analyze_customer(
            customer_id, cust["name"], cust["history"], cust["is_unsubscribed"]
        )
        generate_next_week_notifications(cust)

    return {"ok": True, "customer": cust}


@app.post("/api/sample-behaviour")
def load_sample_behaviour():
    """Applies scripted sample behavior for the 10 scripted personas (Guest untouched)."""
    for cid, cust in STATE["customers"].items():
        if cid == "guest":
            continue
        # Reset and replay 5 weeks deterministically
        cust_meta = next(c for c in CUSTOMERS if c["id"] == cid)
        fresh = init_customer_state(cust_meta)
        for w in range(1, 6):
            if fresh["is_unsubscribed"]:
                break
            notifs = generate_week_notifications(cid, w)
            for n in notifs:
                act = get_scripted_action_for_customer(cid, w, n)
                n.update(act)
                if n["action"] == "unsubscribed":
                    fresh["is_unsubscribed"] = True
            fresh["history"].append({"week": w, "notifications": notifs})
            if fresh["is_unsubscribed"] or w >= 5:
                fresh["is_finished"] = True
                fresh["current_week"] = w
                fresh["active_week_notifications"] = []
                break
            else:
                fresh["current_week"] = w + 1

        STATE["customers"][cid] = fresh

    return {"ok": True, "message": "Sample behaviour loaded for 10 customers"}


@app.post("/api/run-system")
def run_system():
    """Runs policy & ML risk scoring for all finished customers."""
    STATE["system_run"] = True
    for cid, cust in STATE["customers"].items():
        if cust["is_finished"] or len(cust["history"]) > 0:
            analysis = policy_engine.analyze_customer(
                cid, cust["name"], cust["history"], cust["is_unsubscribed"]
            )
            cust["analysis"] = analysis
            generate_next_week_notifications(cust)
        else:
            cust["analysis"] = None

    return {
        "ok": True,
        "summary_metrics": compute_summary_metrics()
    }


def generate_next_week_notifications(cust):
    """
    Generates the upcoming tailored notification schedule for Tab 2
    based on policy decisions. Includes periodic re-check opportunities.
    """
    analysis = cust.get("analysis")
    if not analysis or cust.get("is_unsubscribed"):
        cust["continued_notifications"] = []
        return

    freq = analysis["frequency"]
    cont_types = [c["type"] for c in analysis["continued_types"]]
    paused_types = [p["type"] for p in analysis["paused_types"]]

    if not cont_types:
        cust["continued_notifications"] = []
        return

    # Check for occasional re-check notification:
    # Every second continued round, if there are paused promotional types, insert one re-check
    round_idx = cust.get("continued_rounds", 0) + 1
    has_recheck = False
    recheck_type = None
    if round_idx % 2 == 0 and paused_types:
        promo_paused = [p for p in paused_types if p != "order_update"]
        if promo_paused:
            recheck_type = promo_paused[0]
            has_recheck = True

    # Assemble sequence
    notif_list = []
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    times = ["10:15 AM", "2:30 PM", "6:45 PM", "11:20 AM", "5:10 PM", "1:00 PM", "4:20 PM", "7:00 PM"]

    type_cycle = []
    # If order updates present, ensure at least 1-2 order updates
    order_in = "order_update" in cont_types
    other_types = [t for t in cont_types if t != "order_update"]

    while len(type_cycle) < freq:
        if other_types:
            for ot in other_types:
                if len(type_cycle) < freq:
                    type_cycle.append(ot)
        if order_in and len(type_cycle) < freq:
            type_cycle.append("order_update")
        if not other_types and not order_in:
            break

    # If re-check, replace one promotional alert with re-check
    if has_recheck and len(type_cycle) > 1:
        type_cycle[-1] = recheck_type

    cid = cust["id"]
    for i, t in enumerate(type_cycle):
        msg = get_message_for_customer(cid, t, (round_idx + 10) * 10 + i)
        notif_list.append({
            "id": f"cont_{cid}_{round_idx}_{i+1}",
            "type": t,
            "type_name": TYPE_DISPLAY_NAMES[t],
            "day": days[i % len(days)],
            "time": times[i % len(times)],
            "text": msg,
            "is_recheck": (t == recheck_type),
            "action": None
        })

    cust["continued_notifications"] = notif_list


@app.post("/api/customer/{customer_id}/continue-act")
def submit_continued_round(customer_id: str, submission: WeekSubmission):
    """
    Submits actions for the continued week in Tab 2 and re-analyzes immediately.
    If the customer engages with a re-check alert, that type is restored!
    """
    cust = STATE["customers"].get(customer_id)
    if not cust or not cust.get("continued_notifications"):
        raise HTTPException(status_code=404, detail="No continued notifications")

    actions_map = {a["id"]: a for a in submission.actions}
    cont_notifs = cust["continued_notifications"]

    restored_types = []
    for n in cont_notifs:
        if n["id"] in actions_map:
            act_info = actions_map[n["id"]]
            n["action"] = act_info.get("action", "ignored")
            n["duration"] = act_info.get("duration", "few_seconds")
            n["timing"] = act_info.get("timing", "right_away")
            n["clicked"] = bool(act_info.get("clicked", False))
            n["saved"] = bool(act_info.get("saved", False))

            if n["action"] == "unsubscribed":
                cust["is_unsubscribed"] = True

            # If customer engaged with a re-check, note type to restore
            if n.get("is_recheck") and n["action"] == "opened":
                restored_types.append(n["type"])

    cust["continued_rounds"] = cust.get("continued_rounds", 0) + 1
    # Add to history
    new_w = len(cust["history"]) + 1
    cust["history"].append({
        "week": new_w,
        "notifications": cont_notifs
    })

    # Re-run policy analysis immediately
    cust["analysis"] = policy_engine.analyze_customer(
        customer_id, cust["name"], cust["history"], cust["is_unsubscribed"]
    )

    generate_next_week_notifications(cust)

    return {
        "ok": True,
        "customer": cust,
        "restored_types": restored_types,
        "summary_metrics": compute_summary_metrics()
    }


@app.post("/api/reset")
def reset_demo():
    global STATE
    STATE = create_initial_state()
    return {"ok": True, "message": "Demo state successfully reset"}


# Serve Static Files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
