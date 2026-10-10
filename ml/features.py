"""
ShopEasy Smart Notifications - Feature Engineering Module
Computes rate-based rolling features both for offline training snapshots
and for live 5-round interactive sessions.
"""

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "open_rate_7d",
    "open_rate_21d",
    "trend_7d_vs_14d",
    "open_rate_offer",
    "open_rate_new_arrival",
    "open_rate_price_drop",
    "open_rate_order_update",
    "consecutive_ignore_streak",
    "days_since_last_open",
    "avg_view_seconds",
    "click_rate",
    "mute_count",
    "dismissed_share"
]


def extract_snapshot_features_from_events(events, snapshot_day):
    """
    Fast feature extraction from pre-sorted list of events:
    each event is a dict or named tuple with:
    day, hour, notification_type, action, response_delay_minutes, view_seconds, clicked, saved, muted_type, unsubscribed
    """
    # events up to snapshot_day
    prior = [e for e in events if e["day"] < snapshot_day]
    w21 = [e for e in prior if e["day"] >= snapshot_day - 21]
    w7 = [e for e in prior if e["day"] >= snapshot_day - 7]
    w14 = [e for e in prior if snapshot_day - 21 <= e["day"] < snapshot_day - 7]

    n_w7 = len(w7)
    open_7d = sum(1 for e in w7 if e["action"] == "opened")
    open_rate_7d = (open_7d / n_w7) if n_w7 > 0 else 0.0

    n_w21 = len(w21)
    open_21d = sum(1 for e in w21 if e["action"] == "opened")
    open_rate_21d = (open_21d / n_w21) if n_w21 > 0 else 0.0

    n_w14 = len(w14)
    open_14d = sum(1 for e in w14 if e["action"] == "opened")
    open_rate_14d = (open_14d / n_w14) if n_w14 > 0 else open_rate_21d

    trend_7d_vs_14d = open_rate_7d - open_rate_14d

    def get_type_rate(type_name):
        type_events = [e for e in w21 if e["notification_type"] == type_name]
        if not type_events:
            return 0.5
        return sum(1 for e in type_events if e["action"] == "opened") / len(type_events)

    open_rate_offer = get_type_rate("offer")
    open_rate_new_arrival = get_type_rate("new_arrival")
    open_rate_price_drop = get_type_rate("price_drop")
    open_rate_order_update = get_type_rate("order_update")

    # Consecutive promo ignore streak
    promo_prior = [e for e in prior if e["notification_type"] != "order_update"]
    streak = 0
    for e in reversed(promo_prior):
        if e["action"] != "opened":
            streak += 1
        else:
            break

    # Days since last open
    opened_prior = [e for e in prior if e["action"] == "opened"]
    if opened_prior:
        last_day = max(e["day"] for e in opened_prior)
        days_since_last_open = min(21.0, float(snapshot_day - last_day))
    else:
        days_since_last_open = 21.0

    # View seconds and clicks in 21d
    opened_21 = [e for e in w21 if e["action"] == "opened"]
    if opened_21:
        avg_view_seconds = sum(e["view_seconds"] for e in opened_21) / len(opened_21)
        click_rate = sum(e["clicked"] for e in opened_21) / len(opened_21)
    else:
        avg_view_seconds = 0.0
        click_rate = 0.0

    mute_count = float(sum(e["muted_type"] for e in prior))
    dismissed_share = (sum(1 for e in w21 if e["action"] == "dismissed") / n_w21) if n_w21 > 0 else 0.0

    return {
        "open_rate_7d": float(open_rate_7d),
        "open_rate_21d": float(open_rate_21d),
        "trend_7d_vs_14d": float(trend_7d_vs_14d),
        "open_rate_offer": float(open_rate_offer),
        "open_rate_new_arrival": float(open_rate_new_arrival),
        "open_rate_price_drop": float(open_rate_price_drop),
        "open_rate_order_update": float(open_rate_order_update),
        "consecutive_ignore_streak": float(streak),
        "days_since_last_open": float(days_since_last_open),
        "avg_view_seconds": float(avg_view_seconds),
        "click_rate": float(click_rate),
        "mute_count": float(mute_count),
        "dismissed_share": float(dismissed_share)
    }


def extract_snapshot_features(cust_notifs, snapshot_day):
    events = cust_notifs.to_dict("records")
    return extract_snapshot_features_from_events(events, snapshot_day)


def extract_live_features(history):
    """
    Extracts the same rate-based feature vector from the live interactive session.
    history is a list of weekly records:
    [
      {
        "week": 1..5,
        "notifications": [
          {
            "type": "offer"|"new_arrival"|"price_drop"|"order_update",
            "action": "opened"|"ignored"|"dismissed"|"muted"|"unsubscribed",
            "view_seconds": int,
            "clicked": 0|1,
            "saved": 0|1
          }, ...
        ]
      }, ...
    ]
    """
    flat = []
    # In live simulation, week 1..5. Week = 7 days.
    # Last 7 days = week 5 (or latest completed week).
    # Trailing 21 days = last 3 weeks (weeks 3, 4, 5).
    # Earlier 14 days = weeks 3 and 4.
    if not history:
        return {col: 0.0 for col in FEATURE_COLUMNS}

    max_week = max(h["week"] for h in history)
    all_notifs = []
    for h in history:
        w = h["week"]
        for n in h.get("notifications", []):
            item = dict(n)
            item["week"] = w
            all_notifs.append(item)

    if not all_notifs:
        return {col: 0.0 for col in FEATURE_COLUMNS}

    df = pd.DataFrame(all_notifs)

    # w7: latest week
    w7 = df[df["week"] == max_week]
    # w21: last 3 weeks
    w21 = df[df["week"] >= max(1, max_week - 2)]
    # w14: weeks before latest week inside w21
    w14 = df[(df["week"] >= max(1, max_week - 2)) & (df["week"] < max_week)]

    def calc_open_rate(sub_df):
        if len(sub_df) == 0:
            return 0.0
        return (sub_df["action"] == "opened").mean()

    open_rate_7d = calc_open_rate(w7)
    open_rate_21d = calc_open_rate(w21)
    open_rate_14d = calc_open_rate(w14) if len(w14) > 0 else open_rate_21d
    trend_7d_vs_14d = open_rate_7d - open_rate_14d

    def get_type_open_rate(sub_df, ntype):
        subset = sub_df[sub_df["type"] == ntype]
        if len(subset) == 0:
            return 0.5
        return (subset["action"] == "opened").mean()

    open_rate_offer = get_type_open_rate(w21, "offer")
    open_rate_new_arrival = get_type_open_rate(w21, "new_arrival")
    open_rate_price_drop = get_type_open_rate(w21, "price_drop")
    open_rate_order_update = get_type_open_rate(w21, "order_update")

    # Consecutive promo ignore streak
    promo_df = df[df["type"] != "order_update"]
    streak = 0
    for _, row in promo_df.iloc[::-1].iterrows():
        if row["action"] != "opened":
            streak += 1
        else:
            break

    # Days since last open (approx: each week has 7 days, max_week * 7)
    opened_all = df[df["action"] == "opened"]
    if len(opened_all) > 0:
        latest_open_week = opened_all["week"].max()
        weeks_ago = max_week - latest_open_week
        days_since_last_open = min(21.0, float(weeks_ago * 7.0))
    else:
        days_since_last_open = 21.0

    opened_w21 = w21[w21["action"] == "opened"]
    avg_view_seconds = opened_w21["view_seconds"].mean() if len(opened_w21) > 0 and "view_seconds" in opened_w21 else 0.0
    if pd.isna(avg_view_seconds):
        avg_view_seconds = 0.0

    click_rate = opened_w21["clicked"].mean() if len(opened_w21) > 0 and "clicked" in opened_w21 else 0.0
    if pd.isna(click_rate):
        click_rate = 0.0

    # Mute count
    mute_count = float((df["action"] == "muted").sum())

    # Dismissed share
    dismissed_share = (w21["action"] == "dismissed").mean() if len(w21) > 0 else 0.0

    return {
        "open_rate_7d": float(open_rate_7d),
        "open_rate_21d": float(open_rate_21d),
        "trend_7d_vs_14d": float(trend_7d_vs_14d),
        "open_rate_offer": float(open_rate_offer),
        "open_rate_new_arrival": float(open_rate_new_arrival),
        "open_rate_price_drop": float(open_rate_price_drop),
        "open_rate_order_update": float(open_rate_order_update),
        "consecutive_ignore_streak": float(streak),
        "days_since_last_open": float(days_since_last_open),
        "avg_view_seconds": float(avg_view_seconds),
        "click_rate": float(click_rate),
        "mute_count": float(mute_count),
        "dismissed_share": float(dismissed_share)
    }
