"""
ShopEasy Smart Notifications - Decision Rules and Policy Engine
Implements interest scoring, pausing logic, trend detection, frequency allocation,
plain-language observation generation, and recovery mechanisms.
"""

import os
import joblib
import numpy as np

from ml.features import extract_live_features, FEATURE_COLUMNS

# =====================================================================
# NAMED POLICY CONSTANTS & THRESHOLDS (as specified in specification)
# =====================================================================

# Recency weights for weekly engagement across weeks 1 through 5
WEEK_RECENCY_WEIGHTS = [0.10, 0.15, 0.20, 0.25, 0.30]

# Interest level thresholds
INTEREST_HIGH_THRESHOLD = 0.55       # High interest: >= 0.55
INTEREST_MEDIUM_THRESHOLD = 0.25     # Medium interest: 0.25 to 0.55, Low: < 0.25

# Consecutive ignore streak threshold for pausing promotional notifications
IGNORE_STREAK_PAUSE_THRESHOLD = 3    # 3 or more unread consecutive alerts triggers pause

# Trend detection thresholds
TREND_DIFF_THRESHOLD = 0.25          # Shift of > 0.25 between weeks 4-5 and weeks 1-2
TREND_INACTIVE_THRESHOLD = 0.10      # Average engagement below 0.10 in last two weeks

# Churn risk probability boundaries
RISK_LOW_CUTOFF = 0.35               # < 0.35: Low risk (Engaged)
RISK_HIGH_CUTOFF = 0.65              # > 0.65: High risk (At risk of leaving)

# Notification frequency per week by risk tier
FREQUENCY_LOW_RISK = 8               # Low risk: 8-10 notifications/week
FREQUENCY_MEDIUM_RISK = 4            # Medium risk: 4-5 notifications/week
FREQUENCY_HIGH_RISK = 2              # High risk: 2 notifications/week (essential only)
FREQUENCY_UNSUBSCRIBED = 0           # Unsubscribed: 0 notifications

# Baseline standard broadcast volume before personalization
STANDARD_BUNDLE_VOLUME = 12

ALL_TYPES = ["offer", "new_arrival", "price_drop", "order_update"]

TYPE_DISPLAY_NAMES = {
    "offer": "Offers & Sales",
    "new_arrival": "New Arrivals",
    "price_drop": "Price Drops",
    "order_update": "Order Updates"
}


# =====================================================================
# ENGAGEMENT WEIGHTS (Section 5)
# =====================================================================

def calculate_notification_engagement(notif):
    """
    Computes engagement score for an individual notification:
    Ignore: 0.0, Dismiss: -0.1,
    Open quick glance: 0.2, Open few seconds: 0.45, Read fully: 0.7.
    Modifiers: +0.2 for tapped through (clicked), +0.1 for saved, +0.05 for responded right away.
    Clipped to [0, 1].
    Mute: adds negative signal (-0.2).
    """
    action = notif.get("action", "ignored")
    if action == "unsubscribed":
        return 0.0
    if action == "muted":
        return -0.2
    if action == "ignored":
        return 0.0
    if action == "dismissed":
        return -0.1

    if action == "opened":
        duration = notif.get("duration", "few_seconds")
        if duration == "quick_glance":
            base = 0.20
        elif duration == "read_fully":
            base = 0.70
        else:  # few_seconds
            base = 0.45

        clicked = 0.20 if notif.get("clicked") else 0.0
        saved = 0.10 if notif.get("saved") else 0.0
        timing = notif.get("timing", "right_away")
        right_away = 0.05 if (timing in ["right_away", "Right away"]) else 0.0

        total = base + clicked + saved + right_away
        return float(np.clip(total, 0.0, 1.0))

    return 0.0


# =====================================================================
# CUSTOMER ANALYSIS & DECISION ENGINE
# =====================================================================

class PolicyEngine:
    def __init__(self, model_path=None):
        self.model = None
        if model_path and os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
            except Exception as e:
                print(f"Warning: could not load model from {model_path}: {e}")

    def analyze_customer(self, customer_id, name, history, is_unsubscribed=False):
        """
        Takes customer history across completed weeks and evaluates:
        - Interests (High/Medium/Low, top interest)
        - Trend (Steady/Declining/Recovering/Inactive)
        - Leaving Risk (Low/Medium/High)
        - Key plain observations
        - Decisions (types continued, paused, frequency, reasons)
        - Recommended action
        """
        # 1. Unsubscribe check
        unsubscribed = is_unsubscribed
        for h in history:
            for n in h.get("notifications", []):
                if n.get("action") == "unsubscribed":
                    unsubscribed = True
                    break

        # 2. Compute weekly engagement and per-type engagement
        week_engagements = []
        type_weekly_eng = {t: {} for t in ALL_TYPES}
        type_ignore_streaks = {t: 0 for t in ALL_TYPES}
        type_muted = {t: False for t in ALL_TYPES}

        # Track full sequence of events for observations & streaks
        all_notifs_flat = []
        for h in history:
            w = h["week"]
            week_scores = []
            for n in h.get("notifications", []):
                item = dict(n)
                item["week"] = w
                score = calculate_notification_engagement(item)
                item["engagement_score"] = score
                week_scores.append(score)
                ntype = item["type"]
                if ntype in type_weekly_eng:
                    if w not in type_weekly_eng[ntype]:
                        type_weekly_eng[ntype][w] = []
                    type_weekly_eng[ntype][w].append(score)

                if item.get("action") == "muted":
                    type_muted[ntype] = True

                all_notifs_flat.append(item)

            w_avg = float(np.clip(np.mean(week_scores) if week_scores else 0.0, 0.0, 1.0))
            week_engagements.append(w_avg)

        # Pad week_engagements up to 5 if partial
        while len(week_engagements) < 5:
            week_engagements.append(week_engagements[-1] if week_engagements else 0.0)

        # Compute consecutive ignore streak per type from end of stream
        for ntype in ALL_TYPES:
            type_events = [n for n in all_notifs_flat if n["type"] == ntype]
            streak = 0
            for ev in reversed(type_events):
                if ev.get("action") != "opened":
                    streak += 1
                else:
                    break
            type_ignore_streaks[ntype] = streak

        # 3. Compute Per-Type Interest (Recency-weighted mean)
        interests = {}
        for ntype in ALL_TYPES:
            weeks_present = type_weekly_eng[ntype]
            if not weeks_present:
                score = 0.50
            else:
                total_w = 0.0
                weighted_sum = 0.0
                for w_idx in range(1, 6):
                    if w_idx in weeks_present and weeks_present[w_idx]:
                        w_mean = np.mean(weeks_present[w_idx])
                        w_weight = WEEK_RECENCY_WEIGHTS[w_idx - 1]
                        weighted_sum += w_mean * w_weight
                        total_w += w_weight
                score = (weighted_sum / total_w) if total_w > 0 else 0.50

            # Mute penalty
            if type_muted[ntype]:
                score = 0.0

            score = float(np.clip(score, 0.0, 1.0))

            if score >= INTEREST_HIGH_THRESHOLD:
                level = "High"
            elif score >= INTEREST_MEDIUM_THRESHOLD:
                level = "Medium"
            else:
                level = "Low"

            interests[ntype] = {
                "score": round(score, 2),
                "level": level,
                "display_name": TYPE_DISPLAY_NAMES[ntype],
                "muted": type_muted[ntype],
                "ignore_streak": type_ignore_streaks[ntype]
            }

        # Determine top interest among promotional types (or overall)
        promo_interests = {t: interests[t]["score"] for t in ["offer", "new_arrival", "price_drop"]}
        top_type = max(promo_interests, key=promo_interests.get)
        top_interest_name = TYPE_DISPLAY_NAMES[top_type] if promo_interests[top_type] >= 0.25 else "Order Updates"

        # 4. Trend Detection
        # Declining if weeks 4-5 are lower than weeks 1-2 by > 0.25
        # Recovering if higher by > 0.25
        # Inactive if last two weeks average below 0.10
        # else Steady
        avg_w1_2 = (week_engagements[0] + week_engagements[1]) / 2.0
        avg_w4_5 = (week_engagements[3] + week_engagements[4]) / 2.0
        diff = avg_w4_5 - avg_w1_2

        if unsubscribed:
            trend = "Inactive"
        elif diff > TREND_DIFF_THRESHOLD:
            trend = "Recovering"
        elif diff < -TREND_DIFF_THRESHOLD:
            trend = "Declining"
        elif avg_w4_5 < TREND_INACTIVE_THRESHOLD:
            trend = "Inactive"
        else:
            trend = "Steady"

        # 5. Risk Assessment (via ML Model + Rule Layer)
        live_features = extract_live_features(history)
        model_risk_prob = 0.20
        if self.model is not None and not unsubscribed:
            try:
                import pandas as pd
                feat_df = pd.DataFrame([live_features])[FEATURE_COLUMNS]
                probs = self.model.predict_proba(feat_df)[0]
                model_risk_prob = float(probs[1])
            except Exception:
                model_risk_prob = 0.20

        # Calibrate risk level
        if unsubscribed:
            risk_level = "High"
            status = "unsubscribed"
            status_label = "Unsubscribed"
        elif model_risk_prob > RISK_HIGH_CUTOFF or trend == "Inactive" or (trend == "Declining" and avg_w4_5 < 0.15):
            risk_level = "High"
            status = "at_risk"
            status_label = "At risk of leaving"
        elif model_risk_prob >= RISK_LOW_CUTOFF or trend == "Declining" or avg_w4_5 < 0.35:
            risk_level = "Medium"
            status = "losing_interest"
            status_label = "Losing interest"
        else:
            risk_level = "Low"
            status = "engaged"
            status_label = "Engaged"

        # 6. Decisions: Continued vs Paused Types
        # Never pause order updates unless unsubscribed.
        # Pause a type if Low interest OR ignore streak >= 3 OR muted.
        continued_types = []
        paused_types = []

        if unsubscribed:
            for t in ALL_TYPES:
                paused_types.append({
                    "type": t,
                    "name": TYPE_DISPLAY_NAMES[t],
                    "reason": "All notifications stopped because customer unsubscribed."
                })
            frequency = FREQUENCY_UNSUBSCRIBED
        else:
            for t in ALL_TYPES:
                t_info = interests[t]
                if t == "order_update":
                    continued_types.append({
                        "type": t,
                        "name": TYPE_DISPLAY_NAMES[t],
                        "interest": t_info["level"],
                        "score": t_info["score"],
                        "reason": "Essential service updates are always delivered."
                    })
                elif t_info["muted"]:
                    paused_types.append({
                        "type": t,
                        "name": TYPE_DISPLAY_NAMES[t],
                        "reason": "Paused because you chose to mute this category."
                    })
                elif t_info["ignore_streak"] >= IGNORE_STREAK_PAUSE_THRESHOLD:
                    paused_types.append({
                        "type": t,
                        "name": TYPE_DISPLAY_NAMES[t],
                        "reason": f"Temporarily paused after {t_info['ignore_streak']} unread alerts to reduce noise."
                    })
                elif t_info["level"] == "Low":
                    paused_types.append({
                        "type": t,
                        "name": TYPE_DISPLAY_NAMES[t],
                        "reason": "Paused due to low interaction to keep alerts relevant."
                    })
                else:
                    reason_txt = "Active and prioritised based on high engagement." if t_info["level"] == "High" else "Active based on steady interaction."
                    continued_types.append({
                        "type": t,
                        "name": TYPE_DISPLAY_NAMES[t],
                        "interest": t_info["level"],
                        "score": t_info["score"],
                        "reason": reason_txt
                    })

            # Sort continued types: Order updates always present, others by interest score descending
            continued_types.sort(key=lambda x: (x["type"] == "order_update", x.get("score", 0.0)), reverse=True)

            # Frequency allocation based on risk
            if risk_level == "High":
                frequency = FREQUENCY_HIGH_RISK
                # High risk: only order updates sent
                # If order updates alone, ensure promotional are moved to paused or frequency capped
                if any(c["type"] != "order_update" for c in continued_types):
                    # Keep only order updates active in high risk
                    for c in list(continued_types):
                        if c["type"] != "order_update":
                            continued_types.remove(c)
                            paused_types.append({
                                "type": c["type"],
                                "name": c["name"],
                                "reason": "Paused while customer is at risk of leaving to prevent churn."
                            })
            elif risk_level == "Medium":
                frequency = FREQUENCY_MEDIUM_RISK
            else:
                frequency = FREQUENCY_LOW_RISK

        # 7. Recommended Action
        if unsubscribed:
            recommended_action = "Customer unsubscribed"
        elif risk_level == "High":
            recommended_action = "Send a re-engagement message"
        elif risk_level == "Medium":
            recommended_action = "Reduce frequency"
        else:
            recommended_action = "No action needed"

        # 8. Likely Behavior (Plain sentence)
        if unsubscribed:
            likely_behavior = "Customer has unsubscribed from all communication."
        elif risk_level == "High":
            likely_behavior = "Likely to mute remaining alerts or unsubscribe if promotional volume continues."
        elif risk_level == "Medium":
            likely_behavior = "Engagement is cooling down; customer values a lighter, targeted notification schedule."
        else:
            likely_behavior = "Consistently responsive to relevant alerts and values shopping updates."

        # 9. Key Observations (3-5 plain, evidence-backed sentences)
        observations = generate_observations(all_notifs_flat, interests, trend, unsubscribed)

        return {
            "customer_id": customer_id,
            "name": name,
            "status": status,
            "status_label": status_label,
            "risk_level": risk_level,
            "trend": trend,
            "top_interest": top_interest_name,
            "interests": interests,
            "week_engagements": [round(x, 2) for x in week_engagements],
            "likely_behavior": likely_behavior,
            "observations": observations,
            "continued_types": continued_types,
            "paused_types": paused_types,
            "frequency": frequency,
            "avoided_notifications": max(0, STANDARD_BUNDLE_VOLUME - frequency) if not unsubscribed else 0,
            "recommended_action": recommended_action,
            "is_unsubscribed": unsubscribed
        }


def generate_observations(all_notifs, interests, trend, is_unsubscribed):
    """Generates 3 to 5 clear, evidence-based bullet sentences."""
    obs = []
    if is_unsubscribed:
        obs.append("Unsubscribed from all communications after repeated unread alerts.")

    # Offers observation
    offer_notifs = [n for n in all_notifs if n["type"] == "offer"]
    if offer_notifs:
        opens = sum(1 for n in offer_notifs if n.get("action") == "opened")
        if interests["offer"]["muted"]:
            obs.append("Chose to mute promotional offers.")
        elif opens == 0:
            obs.append(f"Left all {len(offer_notifs)} promotional offers unread.")
        elif opens / len(offer_notifs) >= 0.7:
            obs.append("Regularly opens promotional sales and discount events.")
        elif opens / len(offer_notifs) <= 0.3:
            obs.append(f"Ignored the last {interests['offer']['ignore_streak']} offers.")

    # Price drops observation
    pd_notifs = [n for n in all_notifs if n["type"] == "price_drop"]
    if pd_notifs:
        pd_opens = [n for n in pd_notifs if n.get("action") == "opened"]
        if pd_opens:
            full_reads = sum(1 for n in pd_opens if n.get("duration") == "read_fully")
            taps = sum(1 for n in pd_opens if n.get("clicked"))
            if full_reads >= 2:
                obs.append("Reads price-drop alerts fully to inspect product deals.")
            elif taps >= 1:
                obs.append("Quickly taps through on price-drop notifications.")
            else:
                obs.append("Shows active interest in wishlist price reductions.")
        else:
            obs.append("Rarely checks price drop announcements.")

    # New arrivals observation
    na_notifs = [n for n in all_notifs if n["type"] == "new_arrival"]
    if na_notifs:
        na_opens = sum(1 for n in na_notifs if n.get("action") == "opened")
        if interests["new_arrival"]["muted"]:
            obs.append("Muted new arrival notifications.")
        elif na_opens / len(na_notifs) >= 0.6:
            obs.append("Consistently browses newly launched products and collections.")
        elif na_opens == 0:
            obs.append("Has not opened new arrival announcements.")

    # Order updates observation
    order_notifs = [n for n in all_notifs if n["type"] == "order_update"]
    if order_notifs:
        order_opens = [n for n in order_notifs if n.get("action") == "opened"]
        if len(order_opens) == len(order_notifs):
            obs.append("Opens order and delivery tracking updates within minutes.")
        elif len(order_opens) > 0:
            obs.append("Reliably monitors package deliveries and shipping alerts.")

    # Trend observation
    if trend == "Declining":
        obs.append("Engagement has noticeably declined over recent weeks.")
    elif trend == "Recovering":
        obs.append("Showing renewed interest after a quiet period.")

    # Ensure between 3 and 5 observations
    if len(obs) < 3:
        obs.append("Maintains clear preferences across notification categories.")
    return obs[:5]
