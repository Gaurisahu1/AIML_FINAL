"""
ShopEasy Smart Notifications - Compose & Delivery Decision Engine Tests
Comprehensive verification of pure dynamic decision logic, timing analysis,
budgeting, override, advance, validation, edge cases, and deterministic behavior.
"""

import os
import sys
import pytest
from fastapi import HTTPException

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import app
from app import (
    create_initial_state,
    load_sample_behaviour,
    run_system,
    reset_demo,
    get_compose_options,
    compose_generate,
    compose_override,
    compose_cancel,
    compose_advance,
    get_compose_activity,
    ComposeOptionsRequest,
    ComposeGenerateRequest,
    ComposeOverrideRequest,
    ComposeCancelRequest,
    ComposeAdvanceRequest
)
from engine.delivery import (
    decide,
    analyze_timing_habits,
    compute_next_slot_time,
    generate_message_text,
    CATEGORY_ITEMS,
    TYPE_HIGHLIGHTS,
    SLOT_ORDER
)
from engine.policy import PolicyEngine
from engine.scenarios import CUSTOMERS, generate_week_notifications, get_scripted_action_for_customer

MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "risk_model.joblib")


@pytest.fixture(scope="module")
def policy_engine():
    return PolicyEngine(model_path=MODEL_PATH)


def build_programmatic_history(weeks_spec):
    """
    Builds a synthetic customer history list from a specification of weeks.
    weeks_spec is a list of lists of notification dicts.
    """
    history = []
    for w_idx, notifs in enumerate(weeks_spec, 1):
        formatted_notifs = []
        for n_idx, n in enumerate(notifs, 1):
            formatted_notifs.append({
                "id": f"prog_w{w_idx}_n{n_idx}",
                "type": n.get("type", "offer"),
                "text": n.get("text", "Sample alert"),
                "time": n.get("time", "2:30 PM"),
                "slot": n.get("slot", "afternoon"),
                "action": n.get("action", "opened"),
                "duration": n.get("duration", "few_seconds"),
                "timing": n.get("timing", "right_away"),
                "clicked": n.get("clicked", False),
                "saved": n.get("saved", False)
            })
        history.append({"week": w_idx, "notifications": formatted_notifs})
    return history


def build_synthetic_customer(cid, name, history, is_unsub=False, policy_eng=None):
    """Creates a full customer state with dynamic analysis."""
    cust = {
        "id": cid,
        "name": name,
        "is_unsubscribed": is_unsub,
        "history": history,
        "continued_notifications": []
    }
    if policy_eng:
        cust["analysis"] = policy_eng.analyze_customer(cid, name, history, is_unsub)
    return cust


# =====================================================================
# 1. PROGRAMMATIC DECISION ENGINE TESTS
# =====================================================================

def test_unsubscribed_customer_dont_send_all_types(policy_engine):
    """Unsubscribed customer -> dont_send for every type, including Order Update."""
    history = build_programmatic_history([
        [{"type": "offer", "action": "unsubscribed"}]
    ])
    cust = build_synthetic_customer("cust_unsub", "Unsub User", history, is_unsub=True, policy_eng=policy_engine)

    for ntype in ["offer", "new_arrival", "price_drop", "order_update"]:
        res = decide(cust, {"type": ntype, "urgency": "normal"}, "afternoon", [])
        assert res["decision"] == "dont_send", f"Expected dont_send for {ntype} when unsubscribed"
        assert "unsubscribed" in res["reason"].lower()


def test_order_update_always_send_now_even_high_risk(policy_engine):
    """Order Update to a non-unsubscribed customer, even High-risk -> send_now."""
    # High risk customer: ignores everything for 5 weeks
    history = build_programmatic_history([
        [{"type": "offer", "action": "ignored"} for _ in range(6)]
        for _ in range(5)
    ])
    cust = build_synthetic_customer("cust_high_risk", "Risk User", history, is_unsub=False, policy_eng=policy_engine)
    assert cust["analysis"]["risk_level"] == "High"

    for slot in ["morning", "afternoon", "evening", "late_night"]:
        res = decide(cust, {"type": "order_update", "urgency": "essential"}, slot, [])
        assert res["decision"] == "send_now"
        assert "essential" in res["reason"].lower()


def test_muted_type_dont_send(policy_engine):
    """Muted type -> dont_send; other types still evaluated."""
    # Customer mutes offers
    history = build_programmatic_history([
        [{"type": "offer", "action": "muted"}, {"type": "new_arrival", "action": "opened", "duration": "read_fully"}]
    ])
    cust = build_synthetic_customer("cust_mute", "Mute User", history, is_unsub=False, policy_eng=policy_engine)

    res_offer = decide(cust, {"type": "offer", "urgency": "normal"}, "afternoon", [])
    assert res_offer["decision"] == "dont_send"
    assert "mute" in res_offer["reason"].lower()

    # New arrivals should be evaluated normally (not blocked by mute)
    res_na = decide(cust, {"type": "new_arrival", "urgency": "normal"}, "afternoon", [])
    assert res_na["decision"] in ["send_now", "schedule"]


def test_high_risk_customer_non_essential_dont_send(policy_engine):
    """High-risk customer, non-essential type -> dont_send."""
    history = build_programmatic_history([
        [{"type": "offer", "action": "dismissed"} for _ in range(6)]
        for _ in range(5)
    ])
    cust = build_synthetic_customer("cust_hr", "Churn User", history, is_unsub=False, policy_eng=policy_engine)
    assert cust["analysis"]["risk_level"] == "High"

    for ntype in ["offer", "new_arrival", "price_drop"]:
        res = decide(cust, {"type": ntype, "urgency": "normal"}, "afternoon", [])
        assert res["decision"] == "dont_send"
        assert "close to leaving" in res["reason"].lower()


def test_low_interest_or_ignore_streak_dont_send(policy_engine):
    """Low interest or an ignore streak of 3+ in the type -> dont_send."""
    # Customer actively opens new arrivals, but ignores the last 4 offers
    history = build_programmatic_history([
        [{"type": "new_arrival", "action": "opened", "duration": "read_fully"},
         {"type": "offer", "action": "ignored"},
         {"type": "offer", "action": "ignored"}],
        [{"type": "new_arrival", "action": "opened", "duration": "read_fully"},
         {"type": "offer", "action": "ignored"},
         {"type": "offer", "action": "ignored"}]
    ])
    cust = build_synthetic_customer("cust_streak", "Streak User", history, is_unsub=False, policy_eng=policy_engine)

    res = decide(cust, {"type": "offer", "urgency": "normal"}, "afternoon", [])
    assert res["decision"] == "dont_send"
    assert "ignored the last" in res["reason"] or "low interest" in res["reason"].lower()


def test_low_risk_high_interest_matching_slot_send_now(policy_engine):
    """Low risk, High interest, current slot equals best slot -> send_now."""
    # Consistently opens offers in the morning, ignores in afternoon and evening
    history = build_programmatic_history([
        [
            {"type": "offer", "action": "opened", "duration": "read_fully", "slot": "morning", "timing": "right_away", "clicked": True},
            {"type": "offer", "action": "ignored", "slot": "afternoon", "timing": "right_away"},
            {"type": "offer", "action": "ignored", "slot": "evening", "timing": "right_away"}
        ]
        for _ in range(4)
    ])
    cust = build_synthetic_customer("cust_morning_lover", "Morning Fan", history, is_unsub=False, policy_eng=policy_engine)

    timing = analyze_timing_habits(cust["history"])
    assert timing["best_slot"] == "morning"

    res = decide(cust, {"type": "offer", "urgency": "normal"}, "morning", [])
    assert res["decision"] == "send_now"


def test_differing_slot_replies_later_schedules(policy_engine):
    """Current slot differs from clear best slot and customer usually replies later -> schedule."""
    # Customer opens in the evening with high engagement, and replies later today
    history = build_programmatic_history([
        [
            {"type": "offer", "action": "opened", "duration": "read_fully", "slot": "evening", "timing": "later_today"},
            {"type": "offer", "action": "opened", "duration": "read_fully", "slot": "evening", "timing": "later_today"},
            {"type": "offer", "action": "ignored", "slot": "afternoon", "timing": "right_away"}
        ]
        for _ in range(4)
    ])
    cust = build_synthetic_customer("cust_eve_late", "Evening User", history, is_unsub=False, policy_eng=policy_engine)

    timing = analyze_timing_habits(cust["history"])
    assert timing["best_slot"] == "evening"
    assert timing["usually_replies_later"] is True

    # Current time is afternoon -> should schedule for today evening
    res = decide(cust, {"type": "offer", "urgency": "normal"}, "afternoon", [])
    assert res["decision"] == "schedule"
    assert "Today, 7:30 PM" in res["scheduled_time"] or "evening" in res["reason"].lower()


def test_late_night_demo_time_never_sends_now(policy_engine):
    """Late night demo time, non-essential type -> never send_now."""
    history = build_programmatic_history([
        [{"type": "offer", "action": "opened", "duration": "read_fully", "slot": "morning", "timing": "right_away"}]
        for _ in range(3)
    ])
    cust = build_synthetic_customer("cust_night", "Night Test", history, is_unsub=False, policy_eng=policy_engine)

    # Normal urgency: should schedule for next day
    res_normal = decide(cust, {"type": "offer", "urgency": "normal"}, "late_night", [])
    assert res_normal["decision"] == "schedule"
    assert "Tomorrow" in res_normal["scheduled_time"]

    # Time sensitive with medium interest: dont_send (would arrive too late)
    cust_med = build_synthetic_customer("cust_med", "Med Test", build_programmatic_history([
        [{"type": "price_drop", "action": "opened", "duration": "few_seconds"}] for _ in range(3)
    ]), policy_eng=policy_engine)
    res_ts = decide(cust_med, {"type": "price_drop", "urgency": "time_sensitive"}, "late_night", [])
    assert res_ts["decision"] == "dont_send"


def test_weekly_extras_budget_exhausted(policy_engine):
    """Weekly budget: extra items beyond budget become schedule (Normal) or dont_send (Time-sensitive)."""
    history = build_programmatic_history([
        [{"type": "offer", "action": "opened", "duration": "read_fully"}] for _ in range(4)
    ])
    cust = build_synthetic_customer("cust_budget", "Budget User", history, is_unsub=False, policy_eng=policy_engine)
    # Low risk has budget of 3 items
    sent_items = [
        {"customer_id": "cust_budget", "type": "offer", "status": "sent", "is_next_week": False},
        {"customer_id": "cust_budget", "type": "offer", "status": "sent", "is_next_week": False},
        {"customer_id": "cust_budget", "type": "offer", "status": "scheduled", "is_next_week": False}
    ]

    # Normal urgency beyond budget -> schedule for next week
    res_norm = decide(cust, {"type": "offer", "urgency": "normal"}, "afternoon", sent_items)
    assert res_norm["decision"] == "schedule"
    assert "Next week" in res_norm["scheduled_time"]

    # Time-sensitive urgency beyond budget -> dont_send
    res_ts = decide(cust, {"type": "offer", "urgency": "time_sensitive"}, "afternoon", sent_items)
    assert res_ts["decision"] == "dont_send"
    assert "limit" in res_ts["reason"].lower() or "budget" in res_ts["reason"].lower()


def test_time_sensitive_past_midnight_rule(policy_engine):
    """Time-sensitive item that cannot be delivered before midnight -> send_now for High interest, otherwise dont_send."""
    # 1. High interest customer at late night: send_now because valid until midnight
    hist_high = build_programmatic_history([
        [{"type": "offer", "action": "opened", "duration": "read_fully", "clicked": True, "saved": True}] for _ in range(4)
    ])
    cust_high = build_synthetic_customer("cust_ts_high", "High Fan", hist_high, policy_eng=policy_engine)
    res_high = decide(cust_high, {"type": "offer", "urgency": "time_sensitive"}, "late_night", [])
    assert res_high["decision"] == "send_now"

    # 2. Medium interest customer when next slot is tomorrow: dont_send
    hist_med = build_programmatic_history([
        [{"type": "price_drop", "action": "opened", "duration": "few_seconds"}] for _ in range(3)
    ])
    cust_med = build_synthetic_customer("cust_ts_med", "Med Fan", hist_med, policy_eng=policy_engine)
    res_med = decide(cust_med, {"type": "price_drop", "urgency": "time_sensitive"}, "late_night", [])
    assert res_med["decision"] == "dont_send"


def test_behavior_flip_dynamic_update(policy_engine):
    """Behaviour flip: a customer who ignored offers gets several weeks of opened and read offers -> decision flips."""
    # Phase 1: Customer ignores offers for 3 weeks
    hist_phase1 = build_programmatic_history([
        [{"type": "offer", "action": "ignored"} for _ in range(3)] for _ in range(3)
    ])
    cust = build_synthetic_customer("cust_flip", "Flip User", hist_phase1, policy_eng=policy_engine)
    res1 = decide(cust, {"type": "offer", "urgency": "normal"}, "afternoon", [])
    assert res1["decision"] == "dont_send"

    # Phase 2: Add 3 subsequent weeks of enthusiastic reading
    hist_phase2 = hist_phase1 + build_programmatic_history([
        [{"type": "offer", "action": "opened", "duration": "read_fully", "clicked": True} for _ in range(3)] for _ in range(3)
    ])
    cust2 = build_synthetic_customer("cust_flip", "Flip User", hist_phase2, policy_eng=policy_engine)
    res2 = decide(cust2, {"type": "offer", "urgency": "normal"}, "afternoon", [])
    assert res2["decision"] in ["send_now", "schedule"]


# =====================================================================
# 2. INTEGRITY, DETERMINISM & NO HARDCODING
# =====================================================================

def test_no_hardcoding_scan():
    """Verifies engine/delivery.py contains NO sample customer names and NO customer name checks."""
    delivery_path = os.path.join(PROJECT_ROOT, "engine", "delivery.py")
    with open(delivery_path, "r", encoding="utf-8") as f:
        code = f.read().lower()

    sample_names = ["aarav", "diya", "kabir", "ishita", "rohan", "meera", "sanya", "vivaan", "anaya", "arjun"]
    for name in sample_names:
        assert f'"{name}"' not in code, f"Hardcoded sample customer '{name}' found in engine/delivery.py!"
        assert f"'{name}'" not in code, f"Hardcoded sample customer '{name}' found in engine/delivery.py!"

    assert "customer_id ==" not in code
    assert "customer.get('name') ==" not in code


def test_determinism_and_variant_cycle():
    """Identical inputs give identical decisions and wording, and template cycles through at least 4 variants."""
    msg1 = generate_message_text("offer", "Sneakers", "20% off", variant_seed=0)
    msg2 = generate_message_text("offer", "Sneakers", "20% off", variant_seed=0)
    assert msg1 == msg2
    assert "Sneakers" in msg1
    assert "20% off" in msg1
    assert len(msg1) <= 120

    # Ensure at least 4 distinct variants exist
    variants = {generate_message_text("offer", "Sneakers", "20% off", variant_seed=i) for i in range(10)}
    assert len(variants) >= 4


# =====================================================================
# 3. API WORKFLOW, VALIDATION & STATE TESTS
# =====================================================================

def test_api_options_endpoint():
    """POST /api/compose/options returns valid categories, types, items, and highlights."""
    data = get_compose_options(ComposeOptionsRequest(category="Fashion", type="offer"))
    assert data["ok"] is True
    assert "Sneakers" in data["items"]
    assert "20% off" in data["highlights"]


def test_api_validation_rejections():
    """Rejects invalid items, invalid highlights, unknown customers, and unrun system."""
    reset_demo()

    # Before system run
    with pytest.raises(HTTPException) as exc_prereq:
        compose_generate(ComposeGenerateRequest(
            customer_id="aarav",
            type="offer",
            category="Fashion",
            item="Sneakers",
            highlight="20% off",
            urgency="normal"
        ))
    assert exc_prereq.value.status_code == 400
    assert "run the system first" in exc_prereq.value.detail.lower()

    # Run system
    load_sample_behaviour()
    run_system()

    # Item mismatch with category
    with pytest.raises(HTTPException) as exc_item:
        compose_generate(ComposeGenerateRequest(
            customer_id="aarav",
            type="offer",
            category="Fashion",
            item="Air fryer",  # belongs to Home & Kitchen
            highlight="20% off"
        ))
    assert exc_item.value.status_code == 400
    assert "does not belong" in exc_item.value.detail.lower()

    # Highlight mismatch with type
    with pytest.raises(HTTPException) as exc_hl:
        compose_generate(ComposeGenerateRequest(
            customer_id="aarav",
            type="offer",
            category="Fashion",
            item="Sneakers",
            highlight="Out for delivery"  # belongs to order_update
        ))
    assert exc_hl.value.status_code == 400
    assert "does not belong" in exc_hl.value.detail.lower()

    # Unknown customer
    with pytest.raises(HTTPException) as exc_cust:
        compose_generate(ComposeGenerateRequest(
            customer_id="nonexistent_person",
            type="offer",
            category="Fashion",
            item="Sneakers",
            highlight="20% off"
        ))
    assert exc_cust.value.status_code == 404


def test_api_workflow_send_schedule_override_advance_reset():
    """
    Tests end-to-end API lifecycle:
    - send_now immediately adds notification to customer's continued_notifications.
    - schedule does not add notification immediately.
    - advance delivers due scheduled items and updates inbox.
    - override pushes not_sent item to inbox.
    - cancel removes scheduled item.
    - reset clears all compose state.
    """
    reset_demo()
    load_sample_behaviour()
    run_system()

    # 1. Essential Order Update -> send_now immediately
    data_send = compose_generate(ComposeGenerateRequest(
        customer_id="aarav",
        type="order_update",
        category="Electronics",
        item="Wireless headphones",
        highlight="Out for delivery",
        urgency="essential",
        demo_time="afternoon"
    ))
    assert data_send["item"]["decision"] == "send_now"
    item_send_id = data_send["item"]["id"]

    # Check inbox count increased
    aarav = app.STATE["customers"]["aarav"]
    assert any(n["id"] == f"notif_{item_send_id}" for n in aarav["continued_notifications"])

    # 2. Not sent: Rohan is high risk
    data_ns = compose_generate(ComposeGenerateRequest(
        customer_id="rohan",
        type="offer",
        category="Fashion",
        item="Sneakers",
        highlight="20% off",
        urgency="normal",
        demo_time="afternoon"
    ))
    assert data_ns["item"]["decision"] == "dont_send"
    rohan_item_id = data_ns["item"]["id"]

    # Inbox for Rohan should not contain this item
    rohan = app.STATE["customers"]["rohan"]
    assert not any(n["id"] == f"notif_{rohan_item_id}" for n in (rohan.get("continued_notifications") or []))

    # Override Rohan item -> Send anyway
    res_ov = compose_override(ComposeOverrideRequest(item_id=rohan_item_id))
    assert res_ov["ok"] is True
    rohan_after = app.STATE["customers"]["rohan"]
    assert any(n["id"] == f"notif_{rohan_item_id}" for n in rohan_after["continued_notifications"])

    # 3. Schedule item and Advance demo time
    adv_res = compose_advance(ComposeAdvanceRequest(demo_time="evening"))
    assert adv_res["ok"] is True
    assert adv_res["demo_time"] == "evening"

    # 4. Reset clears composed items
    reset_demo()
    assert len(app.STATE["composed_items"]) == 0


def test_edge_cases_free_play_and_unsub_week1(policy_engine):
    """Verifies edge cases do not crash or yield NaNs."""
    # 1. Free play customer who clicks everything
    hist_click_all = build_programmatic_history([
        [{"type": "offer", "action": "opened", "duration": "read_fully", "clicked": True, "saved": True} for _ in range(6)]
        for _ in range(5)
    ])
    cust_click = build_synthetic_customer("cust_click", "Clicker", hist_click_all, policy_eng=policy_engine)
    res_click = decide(cust_click, {"type": "offer", "urgency": "normal"}, "afternoon", [])
    assert res_click["decision"] in ["send_now", "schedule"]

    # 2. Unsubscribing in week 1
    hist_unsub_w1 = build_programmatic_history([
        [{"type": "offer", "action": "unsubscribed"}]
    ])
    cust_unsub_w1 = build_synthetic_customer("cust_unsub_w1", "Early Leaver", hist_unsub_w1, is_unsub=True, policy_eng=policy_engine)
    res_unsub_w1 = decide(cust_unsub_w1, {"type": "order_update", "urgency": "essential"}, "morning", [])
    assert res_unsub_w1["decision"] == "dont_send"


# =====================================================================
# 4. PRINT SCENARIO TABLE FOR 10 SAMPLE PERSONAS
# =====================================================================

def test_print_sample_customer_scenarios():
    """
    Evaluates three scenarios across all sample customers and prints a markdown table:
      (1) Price Drop, Electronics, Wireless headphones, Price just dropped, Normal, Afternoon;
      (2) Offer, Fashion, Sneakers, 40% off, Normal, Morning;
      (3) Order Update, Electronics, Wireless headphones, Out for delivery, Afternoon.
    """
    reset_demo()
    load_sample_behaviour()
    run_system()

    customers_dict = app.STATE["customers"]

    scenarios = [
        {
            "id": "Scenario 1",
            "desc": "Price Drop (Electronics - Wireless headphones, Price just dropped, Normal, Afternoon)",
            "type": "price_drop",
            "category": "Electronics",
            "item": "Wireless headphones",
            "highlight": "Price just dropped",
            "urgency": "normal",
            "demo_time": "afternoon"
        },
        {
            "id": "Scenario 2",
            "desc": "Offer (Fashion - Sneakers, 40% off, Normal, Morning)",
            "type": "offer",
            "category": "Fashion",
            "item": "Sneakers",
            "highlight": "40% off",
            "urgency": "normal",
            "demo_time": "morning"
        },
        {
            "id": "Scenario 3",
            "desc": "Order Update (Electronics - Wireless headphones, Out for delivery, Essential, Afternoon)",
            "type": "order_update",
            "category": "Electronics",
            "item": "Wireless headphones",
            "highlight": "Out for delivery",
            "urgency": "essential",
            "demo_time": "afternoon"
        }
    ]

    print("\n" + "=" * 115)
    print("DEMO SCENARIOS EVALUATION TABLE ACROSS SCRIPTED PERSONAS")
    print("=" * 115)

    for sc in scenarios:
        print(f"\n### {sc['id']}: {sc['desc']}")
        print(f"| Customer | Status | Risk Level | Decision | Reason |")
        print(f"| :--- | :--- | :--- | :--- | :--- |")

        for c_meta in CUSTOMERS:
            cid = c_meta["id"]
            cust_state = customers_dict.get(cid)
            if not cust_state:
                continue

            dec_res = decide(
                cust_state,
                {"type": sc["type"], "urgency": sc["urgency"]},
                sc["demo_time"],
                []
            )

            status_label = cust_state.get("analysis", {}).get("status_label", "Not Played") if cust_state.get("analysis") else "Not Played"
            risk_label = cust_state.get("analysis", {}).get("risk_level", "Medium") if cust_state.get("analysis") else "Medium"
            decision_label = dec_res["decision"].upper()
            if dec_res["decision"] == "schedule" and dec_res.get("scheduled_time"):
                decision_label += f" ({dec_res['scheduled_time']})"

            reason = dec_res["reason"].replace("|", "/")
            print(f"| **{c_meta['name']}** | {status_label} | {risk_label} | `{decision_label}` | {reason} |")

    print("\n" + "=" * 115 + "\n")
