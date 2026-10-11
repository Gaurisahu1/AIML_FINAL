"""
ShopEasy Smart Notifications - FastAPI Application
Serves API routes, session simulation state, policy engine integration,
and static web files (plain HTML/CSS/vanilla JS).
"""

import os
import copy
from typing import Dict, Any, List, Optional
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
from engine.delivery import (
    CATEGORY_ITEMS,
    TYPE_HIGHLIGHTS,
    decide,
    generate_message_text,
    get_slot_from_time_string,
    SLOT_ORDER,
    SLOT_DISPLAY_NAMES,
    SLOT_TIME_STRINGS
)

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
        "standard_bundle": generate_standard_bundle(),
        "demo_time": "afternoon",
        "composed_items": [],
        "compose_variant_seed": 0
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
        "standard_bundle": STATE["standard_bundle"],
        "demo_time": STATE.get("demo_time", "afternoon")
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


# =====================================================================
# COMPOSE & NOTIFICATION DELIVERY API
# =====================================================================

class ComposeOptionsRequest(BaseModel):
    type: Optional[str] = None
    category: Optional[str] = None


@app.post("/api/compose/options")
def get_compose_options(req: Optional[ComposeOptionsRequest] = None):
    req_type = req.type if req else None
    req_cat = req.category if req else None

    if req_cat and req_cat not in CATEGORY_ITEMS:
        raise HTTPException(status_code=400, detail=f"Category '{req_cat}' is not recognized.")
    if req_type and req_type not in TYPE_HIGHLIGHTS:
        raise HTTPException(status_code=400, detail=f"Notification type '{req_type}' is not recognized.")

    items = CATEGORY_ITEMS.get(req_cat, []) if req_cat else []
    highlights = TYPE_HIGHLIGHTS.get(req_type, []) if req_type else []

    return {
        "ok": True,
        "categories": list(CATEGORY_ITEMS.keys()),
        "types": list(TYPE_HIGHLIGHTS.keys()),
        "items": items,
        "highlights": highlights
    }


class ComposeGenerateRequest(BaseModel):
    customer_id: str
    type: str
    category: str
    item: str
    highlight: str
    urgency: Optional[str] = "normal"
    demo_time: Optional[str] = "afternoon"


DEMO_LEVELS = {
    "morning": 1,
    "afternoon": 2,
    "evening": 3,
    "late_night": 4,
    "next_morning": 5,
    "next_afternoon": 6,
    "next_evening": 7
}


def get_scheduled_item_level(scheduled_time_str: Optional[str]) -> int:
    if not scheduled_time_str:
        return 999
    s = scheduled_time_str.lower()
    if "next week" in s:
        return 100
    if "today" in s:
        if "evening" in s or "7:30" in s:
            return 3
        if "afternoon" in s or "2:00" in s:
            return 2
        if "morning" in s or "9:30" in s or "9:00" in s:
            return 1
        return 3
    if "tomorrow" in s or "next day" in s:
        if "evening" in s or "7:30" in s:
            return 7
        if "afternoon" in s or "2:00" in s:
            return 6
        if "morning" in s or "9:30" in s or "9:00" in s:
            return 5
        return 5
    return 999


@app.post("/api/compose/generate")
def compose_generate(req: ComposeGenerateRequest):
    if not STATE.get("system_run"):
        raise HTTPException(status_code=400, detail="Run the system first so we can learn what each customer likes.")

    cust = STATE["customers"].get(req.customer_id)
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")

    if req.category not in CATEGORY_ITEMS:
        raise HTTPException(status_code=400, detail=f"Category '{req.category}' is not valid.")
    if req.item not in CATEGORY_ITEMS[req.category]:
        raise HTTPException(status_code=400, detail=f"Item '{req.item}' does not belong to category '{req.category}'.")

    if req.type not in TYPE_HIGHLIGHTS:
        raise HTTPException(status_code=400, detail=f"Notification type '{req.type}' is not valid.")
    if req.highlight not in TYPE_HIGHLIGHTS[req.type]:
        raise HTTPException(status_code=400, detail=f"Highlight '{req.highlight}' does not belong to notification type '{req.type}'.")

    urgency = "essential" if req.type == "order_update" else (req.urgency or "normal")
    demo_time = req.demo_time or STATE.get("demo_time", "afternoon")

    # Generate message text using seeded variant cycle
    STATE["compose_variant_seed"] = STATE.get("compose_variant_seed", 0) + 1
    msg_text = generate_message_text(req.type, req.item, req.highlight, STATE["compose_variant_seed"])

    # Decision engine evaluation
    decision_result = decide(
        cust,
        {"type": req.type, "urgency": urgency},
        demo_time,
        STATE.get("composed_items", [])
    )

    item_id = f"comp_{len(STATE.get('composed_items', [])) + 1}"
    decision = decision_result["decision"]
    status = "sent" if decision == "send_now" else ("scheduled" if decision == "schedule" else "not_sent")

    comp_item = {
        "id": item_id,
        "customer_id": req.customer_id,
        "customer_name": cust["name"],
        "type": req.type,
        "type_name": TYPE_DISPLAY_NAMES.get(req.type, req.type),
        "category": req.category,
        "item": req.item,
        "highlight": req.highlight,
        "urgency": urgency,
        "text": msg_text,
        "decision": decision,
        "scheduled_time": decision_result.get("scheduled_time"),
        "reason": decision_result["reason"],
        "status": status,
        "created_time": "Just now",
        "demo_time": demo_time
    }

    if decision == "send_now":
        if cust.get("continued_notifications") is None:
            cust["continued_notifications"] = []
        new_notif = {
            "id": f"notif_{item_id}",
            "type": req.type,
            "type_name": TYPE_DISPLAY_NAMES.get(req.type, req.type),
            "day": "Today",
            "time": "Just now",
            "text": msg_text,
            "action": None
        }
        cust["continued_notifications"].insert(0, new_notif)

    STATE.setdefault("composed_items", []).append(comp_item)

    inbox_count = len(cust.get("continued_notifications") or [])
    return {
        "ok": True,
        "item": comp_item,
        "customer": cust,
        "inbox_count": inbox_count
    }


class ComposeOverrideRequest(BaseModel):
    item_id: str


@app.post("/api/compose/override")
def compose_override(req: ComposeOverrideRequest):
    item = next((i for i in STATE.get("composed_items", []) if i["id"] == req.item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item["status"] = "sent"
    item["decision"] = "send_now"

    cust = STATE["customers"].get(item["customer_id"])
    if cust:
        if cust.get("continued_notifications") is None:
            cust["continued_notifications"] = []
        notif_id = f"notif_{item['id']}"
        if not any(n.get("id") == notif_id for n in cust["continued_notifications"]):
            new_notif = {
                "id": notif_id,
                "type": item["type"],
                "type_name": TYPE_DISPLAY_NAMES.get(item["type"], item["type"]),
                "day": "Today",
                "time": "Just now",
                "text": item["text"],
                "action": None
            }
            cust["continued_notifications"].insert(0, new_notif)

    inbox_count = len(cust.get("continued_notifications") or []) if cust else 0
    return {"ok": True, "item": item, "customer": cust, "inbox_count": inbox_count}


class ComposeCancelRequest(BaseModel):
    item_id: str


@app.post("/api/compose/cancel")
def compose_cancel(req: ComposeCancelRequest):
    item = next((i for i in STATE.get("composed_items", []) if i["id"] == req.item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.get("status") == "scheduled":
        item["status"] = "cancelled"

    return {"ok": True, "item": item}


class ComposeAdvanceRequest(BaseModel):
    demo_time: str


@app.post("/api/compose/advance")
def compose_advance(req: ComposeAdvanceRequest):
    new_lvl = DEMO_LEVELS.get(req.demo_time, 2)
    old_lvl = DEMO_LEVELS.get(STATE.get("demo_time", "afternoon"), 2)
    STATE["demo_time"] = req.demo_time

    delivered_items = []
    if new_lvl > old_lvl:
        for item in STATE.get("composed_items", []):
            if item.get("status") == "scheduled":
                item_lvl = get_scheduled_item_level(item.get("scheduled_time"))
                if item_lvl <= new_lvl:
                    item["status"] = "sent"
                    cust = STATE["customers"].get(item["customer_id"])
                    if cust:
                        if cust.get("continued_notifications") is None:
                            cust["continued_notifications"] = []
                        notif_id = f"notif_{item['id']}"
                        if not any(n.get("id") == notif_id for n in cust["continued_notifications"]):
                            new_notif = {
                                "id": notif_id,
                                "type": item["type"],
                                "type_name": TYPE_DISPLAY_NAMES.get(item["type"], item["type"]),
                                "day": "Today",
                                "time": "Just now",
                                "text": item["text"],
                                "action": None
                            }
                            cust["continued_notifications"].insert(0, new_notif)
                    delivered_items.append(item)

    return {
        "ok": True,
        "demo_time": req.demo_time,
        "delivered_items": delivered_items,
        "selected_customer": STATE["customers"].get(STATE["selected_customer_id"])
    }


@app.get("/api/compose/activity")
def get_compose_activity(customer_id: str):
    if customer_id not in STATE["customers"]:
        raise HTTPException(status_code=404, detail="Customer not found")
    all_items = [i for i in STATE.get("composed_items", []) if i.get("customer_id") == customer_id]
    return {"ok": True, "items": list(reversed(all_items))[:5]}


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
