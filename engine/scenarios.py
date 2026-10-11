"""
ShopEasy Smart Notifications - Scripted Customer Personas & Scenarios
Defines the 11 demo personas, deterministically generates their 5 weeks of notifications,
and provides seeded sample actions that satisfy all acceptance criteria.
"""

import random
from engine.messages import get_message_for_customer

CUSTOMERS = [
    {"id": "aarav",  "name": "Aarav",  "initials": "AA", "role_hint": "loves offers"},
    {"id": "diya",   "name": "Diya",   "initials": "DI", "role_hint": "only cares about order updates"},
    {"id": "kabir",  "name": "Kabir",  "initials": "KA", "role_hint": "likes price drops, ignores offers"},
    {"id": "ishita", "name": "Ishita", "initials": "IS", "role_hint": "interested at first, fades every week"},
    {"id": "rohan",  "name": "Rohan",  "initials": "RO", "role_hint": "ignores everything from week 2"},
    {"id": "meera",  "name": "Meera",  "initials": "ME", "role_hint": "ignores at first, starts opening offers in week 4"},
    {"id": "sanya",  "name": "Sanya",  "initials": "SA", "role_hint": "fan of new arrivals"},
    {"id": "vivaan", "name": "Vivaan", "initials": "VI", "role_hint": "steady, opens most things"},
    {"id": "anaya",  "name": "Anaya",  "initials": "AN", "role_hint": "skims quickly, taps price drops"},
    {"id": "arjun",  "name": "Arjun",  "initials": "AR", "role_hint": "unsubscribes in week 4 if flooded"},
    {"id": "guest",  "name": "Guest",  "initials": "GU", "role_hint": "free play"}
]

# Days and hours distribution for a week's 6 notifications
WEEK_SCHEDULE = [
    {"day_name": "Mon", "time": "10:15 AM", "slot": "morning"},
    {"day_name": "Tue", "time": "2:30 PM", "slot": "afternoon"},
    {"day_name": "Wed", "time": "6:45 PM", "slot": "evening"},
    {"day_name": "Thu", "time": "11:20 AM", "slot": "morning"},
    {"day_name": "Fri", "time": "5:10 PM", "slot": "evening"},
    {"day_name": "Sat", "time": "1:00 PM", "slot": "afternoon"}
]


def generate_week_notifications(customer_id, week_num):
    """
    Generates 6 notifications for week_num (1..5):
    Mix: about 2-3 offers, 1-2 new arrivals, 1 price drop, 1 order update.
    Deterministic based on customer_id and week_num.
    """
    types_by_week = {
        1: ["offer", "new_arrival", "offer", "order_update", "price_drop", "offer"],
        2: ["offer", "new_arrival", "price_drop", "order_update", "new_arrival", "offer"],
        3: ["new_arrival", "offer", "order_update", "price_drop", "offer", "offer"],
        4: ["offer", "price_drop", "new_arrival", "order_update", "new_arrival", "offer"],
        5: ["price_drop", "offer", "new_arrival", "order_update", "offer", "offer"]
    }
    types_list = types_by_week.get(week_num, types_by_week[1])

    notifs = []
    for i, ntype in enumerate(types_list):
        sched = WEEK_SCHEDULE[i]
        # Unique non-repeating message index: week * 10 + i
        msg = get_message_for_customer(customer_id, ntype, (week_num - 1) * 6 + i)
        notifs.append({
            "id": f"{customer_id}_w{week_num}_n{i+1}",
            "type": ntype,
            "text": msg,
            "day_name": sched["day_name"],
            "time": sched["time"],
            "slot": sched.get("slot", "afternoon"),
            "action": None,  # User fills this
            "duration": "few_seconds",
            "timing": "right_away",
            "clicked": False,
            "saved": False
        })
    return notifs


def get_scripted_action_for_customer(customer_id, week_num, notif_item):
    """
    Returns seeded deterministic action for the 10 scripted personas.
    """
    ntype = notif_item["type"]

    if customer_id == "aarav":
        # Loves offers, opens new arrivals & order updates, ignores price drops
        if ntype == "offer":
            return {"action": "opened", "duration": "read_fully", "timing": "right_away", "clicked": True, "saved": False}
        elif ntype in ["new_arrival", "order_update"]:
            return {"action": "opened", "duration": "few_seconds", "timing": "right_away", "clicked": False, "saved": False}
        else:
            return {"action": "ignored"}

    elif customer_id == "diya":
        # Only cares about order updates
        if ntype == "order_update":
            return {"action": "opened", "duration": "few_seconds", "timing": "right_away", "clicked": False, "saved": False}
        else:
            return {"action": "ignored"}

    elif customer_id == "kabir":
        # Likes price drops, ignores offers
        if ntype == "price_drop":
            return {"action": "opened", "duration": "read_fully", "timing": "right_away", "clicked": True, "saved": True}
        elif ntype == "order_update":
            return {"action": "opened", "duration": "few_seconds", "timing": "right_away", "clicked": False, "saved": False}
        elif ntype == "offer":
            return {"action": "ignored"}
        else:
            return {"action": "dismissed"}

    elif customer_id == "ishita":
        # Interested at first, fades every week
        if week_num == 1:
            if ntype in ["offer", "new_arrival"]:
                return {"action": "opened", "duration": "read_fully", "timing": "right_away", "clicked": True, "saved": False}
            elif ntype == "order_update":
                return {"action": "opened", "duration": "few_seconds", "timing": "right_away", "clicked": False, "saved": False}
            else:
                return {"action": "opened", "duration": "few_seconds", "timing": "later_today", "clicked": False, "saved": False}
        elif week_num == 2:
            if ntype == "offer":
                return {"action": "opened", "duration": "few_seconds", "timing": "later_today", "clicked": False, "saved": False}
            elif ntype == "order_update":
                return {"action": "opened", "duration": "few_seconds", "timing": "right_away", "clicked": False, "saved": False}
            else:
                return {"action": "ignored"}
        elif week_num == 3:
            if ntype == "order_update":
                return {"action": "opened", "duration": "few_seconds", "timing": "right_away", "clicked": False, "saved": False}
            elif ntype == "offer":
                return {"action": "dismissed"}
            else:
                return {"action": "ignored"}
        else:  # weeks 4 and 5
            if ntype == "order_update":
                return {"action": "opened", "duration": "quick_glance", "timing": "right_away", "clicked": False, "saved": False}
            else:
                return {"action": "ignored"}

    elif customer_id == "rohan":
        # Ignores everything from week 2
        if week_num == 1:
            if ntype in ["offer", "order_update"]:
                return {"action": "opened", "duration": "quick_glance", "timing": "later_today", "clicked": False, "saved": False}
            else:
                return {"action": "ignored"}
        else:
            return {"action": "ignored"}

    elif customer_id == "meera":
        # Ignores at first, starts opening offers in week 4
        if week_num in [1, 2, 3]:
            return {"action": "ignored"}
        elif week_num == 4:
            if ntype == "offer":
                return {"action": "opened", "duration": "read_fully", "timing": "right_away", "clicked": True, "saved": False}
            elif ntype == "order_update":
                return {"action": "opened", "duration": "few_seconds", "timing": "right_away", "clicked": False, "saved": False}
            else:
                return {"action": "ignored"}
        else:  # week 5
            if ntype == "offer":
                return {"action": "opened", "duration": "read_fully", "timing": "right_away", "clicked": True, "saved": True}
            elif ntype == "order_update":
                return {"action": "opened", "duration": "few_seconds", "timing": "right_away", "clicked": False, "saved": False}
            else:
                return {"action": "ignored"}

    elif customer_id == "sanya":
        # Fan of new arrivals
        if ntype == "new_arrival":
            return {"action": "opened", "duration": "read_fully", "timing": "right_away", "clicked": True, "saved": True}
        elif ntype == "order_update":
            return {"action": "opened", "duration": "few_seconds", "timing": "right_away", "clicked": False, "saved": False}
        else:
            return {"action": "ignored"}

    elif customer_id == "vivaan":
        # Steady, opens most things
        if ntype == "order_update":
            return {"action": "opened", "duration": "few_seconds", "timing": "right_away", "clicked": False, "saved": False}
        elif ntype == "offer":
            return {"action": "opened", "duration": "few_seconds", "timing": "right_away", "clicked": True, "saved": False}
        elif ntype == "new_arrival":
            return {"action": "opened", "duration": "few_seconds", "timing": "right_away", "clicked": False, "saved": False}
        else:  # price_drop
            return {"action": "opened", "duration": "read_fully", "timing": "right_away", "clicked": True, "saved": False}

    elif customer_id == "anaya":
        # Skims quickly, taps price drops
        if ntype == "price_drop":
            return {"action": "opened", "duration": "quick_glance", "timing": "right_away", "clicked": True, "saved": False}
        elif ntype == "order_update":
            return {"action": "opened", "duration": "quick_glance", "timing": "right_away", "clicked": False, "saved": False}
        else:
            return {"action": "ignored"}

    elif customer_id == "arjun":
        # Unsubscribes in week 4 if flooded
        if week_num in [1, 2, 3]:
            if ntype == "order_update":
                return {"action": "opened", "duration": "few_seconds", "timing": "right_away", "clicked": False, "saved": False}
            else:
                return {"action": "ignored"}
        elif week_num == 4:
            # Unsubscribe on first notification in week 4
            return {"action": "unsubscribed"}
        else:
            return {"action": "unsubscribed"}

    # Default fallback
    return {"action": "ignored"}
