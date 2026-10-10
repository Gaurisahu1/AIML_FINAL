"""
ShopEasy Smart Notifications - Acceptance Test Suite
Verifies all 10 scripted personas, edge cases, integrity checks,
and ensures that all customer states match specification requirements.
"""

import os
import sys
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.scenarios import CUSTOMERS, generate_week_notifications, get_scripted_action_for_customer
from engine.policy import PolicyEngine

MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "risk_model.joblib")


@pytest.fixture(scope="module")
def engine():
    return PolicyEngine(model_path=MODEL_PATH)


def simulate_full_history(customer_id):
    """Simulates 5 weeks for customer_id using get_scripted_action_for_customer."""
    history = []
    is_unsubscribed = False
    for w in range(1, 6):
        if is_unsubscribed:
            break
        notifs = generate_week_notifications(customer_id, w)
        for n in notifs:
            act_data = get_scripted_action_for_customer(customer_id, w, n)
            n.update(act_data)
            if n["action"] == "unsubscribed":
                is_unsubscribed = True
        history.append({"week": w, "notifications": notifs})
        if is_unsubscribed:
            break
    return history, is_unsubscribed


def test_aarav_loves_offers(engine):
    history, unsub = simulate_full_history("aarav")
    res = engine.analyze_customer("aarav", "Aarav", history, unsub)
    # Aarav gets offers, new arrivals and order updates (green)
    cont_types = [c["type"] for c in res["continued_types"]]
    assert res["risk_level"] == "Low"
    assert res["status"] == "engaged"
    assert "offer" in cont_types
    assert "new_arrival" in cont_types
    assert "order_update" in cont_types
    assert "price_drop" not in cont_types


def test_diya_order_only(engine):
    history, unsub = simulate_full_history("diya")
    res = engine.analyze_customer("diya", "Diya", history, unsub)
    # Diya gets order updates only
    cont_types = [c["type"] for c in res["continued_types"]]
    assert cont_types == ["order_update"]


def test_kabir_price_drops(engine):
    history, unsub = simulate_full_history("kabir")
    res = engine.analyze_customer("kabir", "Kabir", history, unsub)
    # Kabir gets price drops and order updates with offers paused
    cont_types = [c["type"] for c in res["continued_types"]]
    paused_types = [p["type"] for p in res["paused_types"]]
    assert "price_drop" in cont_types
    assert "order_update" in cont_types
    assert "offer" in paused_types
    assert "offer" not in cont_types


def test_ishita_declining(engine):
    history, unsub = simulate_full_history("ishita")
    res = engine.analyze_customer("ishita", "Ishita", history, unsub)
    # Ishita is Declining with offers and new arrivals paused and reduced frequency (amber/red)
    cont_types = [c["type"] for c in res["continued_types"]]
    paused_types = [p["type"] for p in res["paused_types"]]
    assert res["trend"] == "Declining"
    assert "offer" in paused_types
    assert "new_arrival" in paused_types
    assert res["frequency"] <= 5
    assert res["status"] in ["losing_interest", "at_risk"]


def test_rohan_ignores_from_week_2(engine):
    history, unsub = simulate_full_history("rohan")
    res = engine.analyze_customer("rohan", "Rohan", history, unsub)
    # Rohan is red with order updates only and the action "Send a re-engagement message"
    cont_types = [c["type"] for c in res["continued_types"]]
    assert res["status"] == "at_risk"
    assert res["risk_level"] == "High"
    assert cont_types == ["order_update"]
    assert res["recommended_action"] == "Send a re-engagement message"


def test_meera_recovering_with_offers(engine):
    history, unsub = simulate_full_history("meera")
    res = engine.analyze_customer("meera", "Meera", history, unsub)
    # Meera is Recovering with offers present again
    cont_types = [c["type"] for c in res["continued_types"]]
    assert res["trend"] == "Recovering"
    assert "offer" in cont_types


def test_sanya_fan_of_new_arrivals(engine):
    history, unsub = simulate_full_history("sanya")
    res = engine.analyze_customer("sanya", "Sanya", history, unsub)
    # Sanya gets new arrivals and order updates
    cont_types = [c["type"] for c in res["continued_types"]]
    assert "new_arrival" in cont_types
    assert "order_update" in cont_types
    assert "offer" not in cont_types


def test_vivaan_steady_green(engine):
    history, unsub = simulate_full_history("vivaan")
    res = engine.analyze_customer("vivaan", "Vivaan", history, unsub)
    # Vivaan is green and gets nearly every type
    cont_types = [c["type"] for c in res["continued_types"]]
    assert res["status"] == "engaged"
    assert res["risk_level"] == "Low"
    assert len(cont_types) >= 3


def test_anaya_taps_price_drops(engine):
    history, unsub = simulate_full_history("anaya")
    res = engine.analyze_customer("anaya", "Anaya", history, unsub)
    # Anaya gets price drops and order updates prioritised
    cont_types = [c["type"] for c in res["continued_types"]]
    assert "price_drop" in cont_types
    assert "order_update" in cont_types


def test_arjun_unsubscribed(engine):
    history, unsub = simulate_full_history("arjun")
    res = engine.analyze_customer("arjun", "Arjun", history, unsub)
    # Arjun is unsubscribed with no notifications
    assert res["is_unsubscribed"] is True
    assert res["status"] == "unsubscribed"
    assert res["frequency"] == 0
    assert len(res["continued_types"]) == 0
    assert res["avoided_notifications"] == 0


def test_customer_diversity(engine):
    # The ten customers must not all look alike in Tab 2 and Tab 3
    results = [engine.analyze_customer(c["id"], c["name"], *simulate_full_history(c["id"])) for c in CUSTOMERS if c["id"] != "guest"]
    statuses = set(r["status"] for r in results)
    trends = set(r["trend"] for r in results)
    frequencies = set(r["frequency"] for r in results)
    assert len(statuses) >= 3  # Green, Amber, Red, Grey present
    assert len(trends) >= 3    # Steady, Declining, Recovering, Inactive
    assert len(frequencies) >= 3  # Multiple distinct frequencies


def test_edge_case_guest_ignores_everything(engine):
    history = []
    for w in range(1, 6):
        notifs = generate_week_notifications("guest", w)
        for n in notifs:
            n["action"] = "ignored"
        history.append({"week": w, "notifications": notifs})
    res = engine.analyze_customer("guest", "Guest", history, False)
    assert res["status"] == "at_risk"
    assert [c["type"] for c in res["continued_types"]] == ["order_update"]


def test_edge_case_guest_clicks_everything(engine):
    history = []
    for w in range(1, 6):
        notifs = generate_week_notifications("guest", w)
        for n in notifs:
            n.update({"action": "opened", "duration": "read_fully", "timing": "right_away", "clicked": True, "saved": True})
        history.append({"week": w, "notifications": notifs})
    res = engine.analyze_customer("guest", "Guest", history, False)
    assert res["status"] == "engaged"
    assert res["risk_level"] == "Low"
    assert len(res["continued_types"]) == 4


def test_edge_case_unsubscribe_week_1(engine):
    notifs = generate_week_notifications("guest", 1)
    notifs[0]["action"] = "unsubscribed"
    history = [{"week": 1, "notifications": [notifs[0]]}]
    res = engine.analyze_customer("guest", "Guest", history, True)
    assert res["is_unsubscribed"] is True
    assert res["frequency"] == 0
    assert len(res["continued_types"]) == 0


def test_edge_case_partially_completed_weeks(engine):
    history = [{"week": 1, "notifications": generate_week_notifications("guest", 1)}]
    for n in history[0]["notifications"]:
        n["action"] = "opened"
    res = engine.analyze_customer("guest", "Guest", history, False)
    assert not any(v != v for v in res["week_engagements"])  # No NaN
    assert res["frequency"] > 0


def test_edge_case_no_crash_or_nan(engine):
    for c in CUSTOMERS:
        h, u = simulate_full_history(c["id"])
        res = engine.analyze_customer(c["id"], c["name"], h, u)
        for eng in res["week_engagements"]:
            assert eng is not None and not (eng != eng)
        for t, data in res["interests"].items():
            assert not (data["score"] != data["score"])
        assert res["likely_behavior"]
        assert len(res["observations"]) >= 3
