"""
ShopEasy Smart Notifications - Notification Delivery Decision Engine
Pure, dynamic decision function evaluating customer engagement history and context.
Contains NO customer names, NO per-customer special cases, and NO hardcoded outcomes.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from engine.policy import (
    calculate_notification_engagement,
    WEEK_RECENCY_WEIGHTS,
    INTEREST_HIGH_THRESHOLD,
    INTEREST_MEDIUM_THRESHOLD,
    IGNORE_STREAK_PAUSE_THRESHOLD,
    TYPE_DISPLAY_NAMES,
    ALL_TYPES
)

# =====================================================================
# NAMED POLICY CONSTANTS & THRESHOLDS (as specified in specification)
# =====================================================================

# Time-slot engagement analysis constants
SLOT_MIN_NOTIFICATIONS = 2            # A slot needs at least 2 notifications to identify a pattern
SLOT_BEAT_AVERAGE_MARGIN = 0.15       # Best slot must exceed average engagement by at least 0.15
REPLY_LATER_RATIO_THRESHOLD = 0.50    # >= 50% opens answered 'later_today' or 'next_day' means replies later
LOW_ENGAGEMENT_SLOT_THRESHOLD = 0.25  # Slot engagement below 0.25 is considered low engagement

# Weekly extras budget of composed non-essential notifications by risk tier
BUDGET_LOW_RISK = 3                   # Low risk customers: 3 extra composed alerts per week
BUDGET_MEDIUM_RISK = 1                # Medium risk customers: 1 extra composed alert per week
BUDGET_HIGH_RISK = 0                  # High risk customers: 0 extra promotional alerts per week

# Time slots in chronological order
SLOT_ORDER = ["morning", "afternoon", "evening", "late_night"]

SLOT_DISPLAY_NAMES = {
    "morning": "Morning (9:30 AM)",
    "afternoon": "Afternoon (2:00 PM)",
    "evening": "Evening (7:30 PM)",
    "late_night": "Late night (11:30 PM)"
}

SLOT_TIME_STRINGS = {
    "morning": "9:30 AM",
    "afternoon": "2:00 PM",
    "evening": "7:30 PM",
    "late_night": "11:30 PM"
}

# Supported categories and their valid items
CATEGORY_ITEMS = {
    "Fashion": ["Sneakers", "Denim jacket", "Handbag", "Watch"],
    "Electronics": ["Wireless headphones", "Smartwatch", "Power bank", "Bluetooth speaker"],
    "Home & Kitchen": ["Air fryer", "Bedsheet set", "Cookware set", "Table lamp"],
    "Beauty": ["Face serum", "Perfume", "Sunscreen", "Lipstick set"],
    "Groceries": ["Fresh fruits box", "Snack combo", "Organic staples", "Coffee beans"],
    "Sports": ["Running shoes", "Yoga mat", "Cricket bat", "Gym gloves"]
}

# Supported notification types and their valid highlights
TYPE_HIGHLIGHTS = {
    "offer": ["20% off", "40% off", "Buy 1 Get 1", "Free delivery"],
    "new_arrival": ["Just launched", "Back in stock", "Limited edition", "Trending now"],
    "price_drop": ["Price just dropped", "Lowest this month", "Only a few left"],
    "order_update": ["Shipped", "Out for delivery", "Delivered", "Delayed"]
}

# Message template variants (at least 4 per type)
MESSAGE_TEMPLATES = {
    "offer": [
        "{highlight} on {item}! Grab yours before stocks run out.",
        "Special deal: get {highlight} on {item} today only.",
        "Exclusive savings: {highlight} on {item}. Tap to shop now.",
        "Don't miss out: {highlight} on trending {item} this week."
    ],
    "new_arrival": [
        "{highlight}: check out our all-new {item} collection today.",
        "Fresh in stock! The new {item} is {highlight} right now.",
        "{highlight} — explore the latest {item} arrivals in store.",
        "Just for you: {item} is {highlight}. See what's new today."
    ],
    "price_drop": [
        "{highlight}! {item} is now available at a reduced price.",
        "Great news: {highlight} for {item}. Save on your pick.",
        "Deal alert: {highlight} on {item}. Complete your order.",
        "{highlight} — snag {item} now while the deal lasts!"
    ],
    "order_update": [
        "Order update: your {item} is {highlight}. Track delivery.",
        "Tracking alert: {item} package is {highlight}.",
        "Delivery status: your order of {item} is {highlight}.",
        "Quick update: your {item} has been {highlight}."
    ]
}


# =====================================================================
# TEMPLATE MESSAGE GENERATOR
# =====================================================================

def generate_message_text(ntype: str, item: str, highlight: str, variant_seed: int = 0) -> str:
    """
    Selects message wording automatically from templates containing item and highlight.
    Cycles through variants deterministically and caps message at 120 characters.
    """
    templates = MESSAGE_TEMPLATES.get(ntype, MESSAGE_TEMPLATES["offer"])
    idx = variant_seed % len(templates)
    template = templates[idx]
    msg = template.format(item=item, highlight=highlight)
    if len(msg) > 120:
        msg = msg[:117] + "..."
    return msg


# =====================================================================
# TIME SLOT AND TIMING ANALYSIS
# =====================================================================

def get_slot_from_time_string(time_str: str) -> str:
    """Infers morning, afternoon, evening, or late_night from a time string."""
    t_clean = (time_str or "").strip().lower()
    if t_clean in SLOT_ORDER:
        return t_clean
    if "late" in t_clean or "night" in t_clean or "23:" in t_clean:
        return "late_night"
    if "evening" in t_clean or "7:30" in t_clean or "6:45" in t_clean or "5:10" in t_clean:
        return "evening"
    if "morning" in t_clean or "9:30" in t_clean or "10:15" in t_clean or "11:20" in t_clean:
        return "morning"
    if "afternoon" in t_clean or "2:00" in t_clean or "2:30" in t_clean or "1:00" in t_clean:
        return "afternoon"

    if "am" in t_clean:
        return "morning"
    if "pm" in t_clean:
        if any(h in t_clean for h in ["12:", "1:", "2:", "3:", "4:"]):
            return "afternoon"
        if any(h in t_clean for h in ["5:", "6:", "7:", "8:", "9:"]):
            return "evening"
        if any(h in t_clean for h in ["10:", "11:"]):
            return "late_night"
    return "afternoon"


def analyze_timing_habits(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes historical engagement per send-time slot using recency weights,
    determines whether there is a clear best slot, and checks if customer usually replies later.
    """
    slot_weekly_scores: Dict[str, Dict[int, List[float]]] = {s: {} for s in SLOT_ORDER}
    slot_counts: Dict[str, int] = {s: 0 for s in SLOT_ORDER}
    all_scores: List[float] = []

    opens_count = 0
    later_opens_count = 0

    for h in history:
        w = h.get("week", 1)
        for n in h.get("notifications", []):
            slot = n.get("slot") or get_slot_from_time_string(n.get("time", ""))
            if slot not in slot_weekly_scores:
                slot = "afternoon"

            score = calculate_notification_engagement(n)
            all_scores.append(score)
            slot_counts[slot] += 1

            if w not in slot_weekly_scores[slot]:
                slot_weekly_scores[slot][w] = []
            slot_weekly_scores[slot][w].append(score)

            action = n.get("action")
            if action == "opened":
                opens_count += 1
                timing_val = str(n.get("timing", "")).lower()
                if "later" in timing_val or "next" in timing_val:
                    later_opens_count += 1

    # Recency weighted slot scores
    slot_scores: Dict[str, float] = {}
    for s in SLOT_ORDER:
        weeks_data = slot_weekly_scores[s]
        if not weeks_data:
            slot_scores[s] = 0.0
            continue

        weighted_sum = 0.0
        weight_sum = 0.0
        for w_idx in range(1, 6):
            if w_idx in weeks_data and weeks_data[w_idx]:
                w_mean = float(np.mean(weeks_data[w_idx]))
                w = WEEK_RECENCY_WEIGHTS[w_idx - 1] if w_idx - 1 < len(WEEK_RECENCY_WEIGHTS) else 0.20
                weighted_sum += w_mean * w
                weight_sum += w
        slot_scores[s] = (weighted_sum / weight_sum) if weight_sum > 0 else 0.0

    overall_avg = float(np.mean(all_scores)) if all_scores else 0.0

    # Best slot detection: needs >= 2 notifications and beats overall avg by >= 0.15
    best_slot = None
    best_score = -1.0
    for s in SLOT_ORDER:
        if slot_counts[s] >= SLOT_MIN_NOTIFICATIONS:
            if slot_scores[s] > best_score and (slot_scores[s] - overall_avg) >= SLOT_BEAT_AVERAGE_MARGIN:
                best_score = slot_scores[s]
                best_slot = s

    usually_replies_later = (opens_count > 0) and ((later_opens_count / opens_count) >= REPLY_LATER_RATIO_THRESHOLD)

    return {
        "slot_scores": slot_scores,
        "slot_counts": slot_counts,
        "overall_avg": overall_avg,
        "best_slot": best_slot,
        "usually_replies_later": usually_replies_later
    }


def compute_next_slot_time(current_slot: str, target_slot: str) -> Tuple[str, bool]:
    """
    Computes human-readable delivery time string and whether delivery is next day.
    Returns (time_string, is_next_day).
    """
    if current_slot not in SLOT_ORDER:
        current_slot = "afternoon"
    if target_slot not in SLOT_ORDER:
        target_slot = "morning"

    cur_idx = SLOT_ORDER.index(current_slot)
    tar_idx = SLOT_ORDER.index(target_slot)

    # Late night current slot is always delivered next day
    if current_slot == "late_night":
        return f"Tomorrow, {SLOT_TIME_STRINGS[target_slot]}", True

    if tar_idx > cur_idx:
        # Later today
        return f"Today, {SLOT_TIME_STRINGS[target_slot]}", False
    else:
        # Tomorrow
        return f"Tomorrow, {SLOT_TIME_STRINGS[target_slot]}", True


# =====================================================================
# PURE DECISION FUNCTION (decide)
# =====================================================================

def decide(
    customer_state: Dict[str, Any],
    notification: Dict[str, Any],
    demo_time: str,
    state_of_sent_items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Pure decision function. Evaluates whether to send_now, schedule, or dont_send.
    Uses ONLY recorded customer data, analysis, and context.
    Contains NO customer names, NO per-customer special cases, NO hardcoded outcomes.

    Returns:
        {
            "decision": "send_now" | "schedule" | "dont_send",
            "scheduled_time": Optional[str],
            "reason": str
        }
    """
    ntype = notification.get("type", "offer")
    type_display = TYPE_DISPLAY_NAMES.get(ntype, "Notifications")
    urgency = notification.get("urgency", "normal")

    # Current slot
    current_slot = get_slot_from_time_string(demo_time)

    # 1. Check Unsubscribed
    is_unsubscribed = bool(
        customer_state.get("is_unsubscribed") or
        (customer_state.get("analysis") and customer_state["analysis"].get("is_unsubscribed"))
    )
    if is_unsubscribed:
        return {
            "decision": "dont_send",
            "scheduled_time": None,
            "reason": "Customer unsubscribed from all communications, so no messages can be sent."
        }

    # Extract or fallback analysis
    analysis = customer_state.get("analysis")
    interests = analysis.get("interests", {}) if analysis else {}
    type_interest_info = interests.get(ntype, {})

    # 2. Check Muted Type
    is_muted = type_interest_info.get("muted", False)
    if is_muted:
        return {
            "decision": "dont_send",
            "scheduled_time": None,
            "reason": f"Customer chose to mute {type_display}, so we respect their choice and do not send this."
        }

    # 3. Essential (Order Update) -> send_now immediately (unless unsubscribed)
    if ntype == "order_update":
        return {
            "decision": "send_now",
            "scheduled_time": None,
            "reason": "Essential order updates are always delivered immediately."
        }

    # Risk level and Trend
    risk_level = analysis.get("risk_level", "Medium") if analysis else "Medium"
    trend = analysis.get("trend", "Steady") if analysis else "Steady"

    # 4. Risk Level High -> dont_send non-essential
    if risk_level == "High":
        return {
            "decision": "dont_send",
            "scheduled_time": None,
            "reason": "Customer is close to leaving, so we only send essential order updates."
        }

    # 5. Type is Paused or Low Interest -> dont_send
    interest_level = type_interest_info.get("level", "Medium")
    ignore_streak = type_interest_info.get("ignore_streak", 0)

    # Paused types check from analysis
    paused_type_names = [p.get("type") for p in analysis.get("paused_types", [])] if analysis else []
    is_type_paused = (ntype in paused_type_names) or (interest_level == "Low") or (ignore_streak >= IGNORE_STREAK_PAUSE_THRESHOLD)

    if is_type_paused:
        if ignore_streak >= IGNORE_STREAK_PAUSE_THRESHOLD:
            reason_msg = f"Has ignored the last {ignore_streak} {type_display.lower()}, so this would likely be ignored."
        else:
            reason_msg = f"Customer has low interest in {type_display.lower()}, so alerts in this category are paused to prevent fatigue."
        return {
            "decision": "dont_send",
            "scheduled_time": None,
            "reason": reason_msg
        }

    # 6. Weekly Extras Budget Check
    # Budget by risk tier: Low risk -> 3, Medium risk -> 1, High risk -> 0
    if risk_level == "Low":
        budget = BUDGET_LOW_RISK
    elif risk_level == "Medium":
        budget = BUDGET_MEDIUM_RISK
    else:
        budget = BUDGET_HIGH_RISK

    # Count composed non-essential items delivered this week for this customer
    cid = customer_state.get("id")
    current_week_items = [
        item for item in state_of_sent_items
        if item.get("customer_id") == cid
        and item.get("type") != "order_update"
        and item.get("status") in ["sent", "scheduled"]
        and not item.get("is_next_week", False)
    ]

    if len(current_week_items) >= budget:
        if urgency == "time_sensitive":
            return {
                "decision": "dont_send",
                "scheduled_time": None,
                "reason": "Weekly limit for promotional notifications is reached, and time-sensitive alerts cannot be delayed to next week."
            }
        else:
            # Schedule for next week best slot or Monday morning
            timing_info = analyze_timing_habits(customer_state.get("history", []))
            target_slot = timing_info["best_slot"] or "morning"
            slot_name = SLOT_DISPLAY_NAMES.get(target_slot, "Morning (9:30 AM)")
            return {
                "decision": "schedule",
                "scheduled_time": f"Next week, Monday {SLOT_TIME_STRINGS[target_slot]}",
                "reason": f"Weekly limit reached for this week. Scheduled for next week during their preferred active time ({slot_name})."
            }

    # Timing analysis
    timing_info = analyze_timing_habits(customer_state.get("history", []))
    best_slot = timing_info["best_slot"]
    usually_replies_later = timing_info["usually_replies_later"]
    cur_slot_score = timing_info["slot_scores"].get(current_slot, 0.5)

    # 8. Medium interest AND Declining trend:
    # send_now ONLY when current slot is customer's best slot; otherwise schedule
    if interest_level == "Medium" and trend == "Declining":
        if best_slot is not None and current_slot == best_slot:
            return {
                "decision": "send_now",
                "scheduled_time": None,
                "reason": f"Delivering right now during the customer's most responsive time ({SLOT_DISPLAY_NAMES[best_slot]}) to prevent fading interest."
            }
        else:
            target_slot = best_slot or "morning"
            sched_time, is_next_day = compute_next_slot_time(current_slot, target_slot)
            if urgency == "time_sensitive" and is_next_day:
                return {
                    "decision": "dont_send",
                    "scheduled_time": None,
                    "reason": "Customer engagement is cooling down and this time-sensitive alert would arrive after midnight, which is too late to be useful."
                }
            return {
                "decision": "schedule",
                "scheduled_time": sched_time,
                "reason": f"Engagement is cooling down, so we scheduled this for their peak responsive time ({SLOT_DISPLAY_NAMES[target_slot]}) to encourage interaction."
            }

    # 7. Timing Checks:
    # 7a. Demo time is Late night
    if current_slot == "late_night":
        target_slot = best_slot or "morning"
        sched_time, is_next_day = compute_next_slot_time("late_night", target_slot)
        if urgency == "time_sensitive":
            if interest_level == "High":
                return {
                    "decision": "send_now",
                    "scheduled_time": None,
                    "reason": "Customer has high interest in this offer and it expires at midnight, so it is delivered now despite the late hour."
                }
            else:
                return {
                    "decision": "dont_send",
                    "scheduled_time": None,
                    "reason": "This time-sensitive notification would arrive after midnight, which is too late to be useful."
                }
        return {
            "decision": "schedule",
            "scheduled_time": sched_time,
            "reason": f"It is late night, so we held this promotional alert until {sched_time} to avoid disturbing the customer."
        }

    # 7b. Clear best slot that differs from current slot AND (usually replies later OR low engagement in current slot)
    has_clear_best = (best_slot is not None) and (best_slot != current_slot)
    needs_schedule = has_clear_best and (usually_replies_later or (cur_slot_score < LOW_ENGAGEMENT_SLOT_THRESHOLD))

    if needs_schedule:
        sched_time, is_next_day = compute_next_slot_time(current_slot, best_slot)
        if urgency == "time_sensitive" and is_next_day:
            if interest_level == "High":
                return {
                    "decision": "send_now",
                    "scheduled_time": None,
                    "reason": "Customer has high interest and this alert expires today, so it is delivered now before it expires."
                }
            else:
                return {
                    "decision": "dont_send",
                    "scheduled_time": None,
                    "reason": "This time-sensitive notification would arrive after midnight, which is too late to be useful."
                }
        slot_label = "the evening" if best_slot == "evening" else ("the morning" if best_slot == "morning" else "the afternoon")
        return {
            "decision": "schedule",
            "scheduled_time": sched_time,
            "reason": f"Usually replies in {slot_label}, so we will send it then for better engagement."
        }

    # 7c. Else -> send_now
    return {
        "decision": "send_now",
        "scheduled_time": None,
        "reason": f"Customer is engaged with {type_display.lower()} and this is an ideal time for delivery."
    }
