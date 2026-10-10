"""
ShopEasy Smart Notifications - Synthetic Dataset Generator
Simulates 600 customers over 90 days with realistic engagement mechanics,
fatigue effects, muting, and unsubscribe patterns. Fully reproducible (seed=42).
"""

import os
import math
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SEED = 42

PERSONAS = {
    "steady_engaged": 0.20,
    "offer_lover": 0.14,
    "price_drop_hunter": 0.12,
    "new_arrival_browser": 0.08,
    "order_only": 0.12,
    "fading": 0.14,
    "dormant": 0.08,
    "recovering": 0.08,
    "quick_quitter": 0.04
}

BASE_PROBS = {
    "steady_engaged":      {"offer": 0.55, "new_arrival": 0.50, "price_drop": 0.60, "order_update": 0.95},
    "offer_lover":         {"offer": 0.85, "new_arrival": 0.45, "price_drop": 0.40, "order_update": 0.95},
    "price_drop_hunter":   {"offer": 0.20, "new_arrival": 0.35, "price_drop": 0.85, "order_update": 0.95},
    "new_arrival_browser": {"offer": 0.25, "new_arrival": 0.80, "price_drop": 0.35, "order_update": 0.95},
    "order_only":          {"offer": 0.05, "new_arrival": 0.05, "price_drop": 0.08, "order_update": 0.92},
    "fading":              {"offer": 0.70, "new_arrival": 0.60, "price_drop": 0.65, "order_update": 0.95},
    "dormant":             {"offer": 0.06, "new_arrival": 0.05, "price_drop": 0.08, "order_update": 0.70},
    "recovering":          {"offer": 0.60, "new_arrival": 0.55, "price_drop": 0.60, "order_update": 0.95},
    "quick_quitter":       {"offer": 0.50, "new_arrival": 0.40, "price_drop": 0.45, "order_update": 0.95}
}

FAVORITE_TYPE = {
    "steady_engaged": "price_drop",
    "offer_lover": "offer",
    "price_drop_hunter": "price_drop",
    "new_arrival_browser": "new_arrival",
    "order_only": "order_update",
    "fading": "offer",
    "dormant": "order_update",
    "recovering": "offer",
    "quick_quitter": "offer"
}

TYPE_MIX = [
    ("offer", 0.40),
    ("new_arrival", 0.25),
    ("price_drop", 0.15),
    ("order_update", 0.20)
]

WINDOWS = {
    "morning": (8, 11),
    "afternoon": (12, 16),
    "evening": (18, 22)
}


def generate_dataset(output_dir="data", reports_dir="reports", total_customers=600, total_days=90):
    random.seed(SEED)
    np.random.seed(SEED)

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    # 1. Create customers
    customers = []
    c_id = 1
    window_names = list(WINDOWS.keys())

    for persona, share in PERSONAS.items():
        count = int(round(total_customers * share))
        for _ in range(count):
            pref_window = random.choice(window_names)
            signup_day = random.randint(0, 3)
            # Fading tau drawn uniformly 20 to 45
            tau = random.uniform(20.0, 45.0) if persona == "fading" else None
            customers.append({
                "customer_id": f"C{c_id:04d}",
                "persona": persona,
                "signup_day": signup_day,
                "preferred_window": pref_window,
                "tau": tau
            })
            c_id += 1

    # Adjust if rounding difference
    while len(customers) < total_customers:
        customers.append({
            "customer_id": f"C{c_id:04d}",
            "persona": "steady_engaged",
            "signup_day": 0,
            "preferred_window": "afternoon",
            "tau": None
        })
        c_id += 1
    customers = customers[:total_customers]

    cust_df = pd.DataFrame(customers)
    # Save customers.csv without internal fields
    cust_df[["customer_id", "persona", "signup_day", "preferred_window"]].to_csv(
        os.path.join(output_dir, "customers.csv"), index=False
    )

    # 2. Simulate notifications over 90 days
    notifications = []
    # Track state per customer
    # state: consecutive_promo_ignores, consecutive_ignores_by_type, muted_types, unsubscribed
    type_names = [t[0] for t in TYPE_MIX]
    type_weights = [t[1] for t in TYPE_MIX]

    for cust in customers:
        cid = cust["customer_id"]
        persona = cust["persona"]
        pref_win = cust["preferred_window"]
        win_start, win_end = WINDOWS[pref_win]
        tau = cust["tau"]
        signup = cust["signup_day"]

        consecutive_promo_ignores = 0
        consecutive_ignores_by_type = {t: 0 for t in type_names}
        muted_types = set()
        unsubscribed = False

        for day in range(signup, total_days):
            if unsubscribed:
                break

            # Daily unsubscribe check
            if persona == "quick_quitter":
                if consecutive_promo_ignores >= 4 and random.random() < 0.40:
                    unsubscribed = True
                    break
            else:
                if consecutive_promo_ignores >= 10 and random.random() < 0.25:
                    unsubscribed = True
                    break

            # Volume: Poisson(1.6) capped at 3
            n_notifs = min(3, np.random.poisson(1.6))
            if n_notifs == 0:
                continue

            for notif_idx in range(n_notifs):
                # Filter available types (remove muted promotional types)
                available_types = [t for t in type_names if t not in muted_types]
                if not available_types:
                    available_types = ["order_update"]

                # Renormalize weights
                avail_weights = [dict(TYPE_MIX)[t] for t in available_types]
                total_w = sum(avail_weights)
                norm_weights = [w / total_w for w in avail_weights]
                chosen_type = np.random.choice(available_types, p=norm_weights)

                # Hour of sending (sample mostly waking hours 8-22, slight chance outside)
                if random.random() < 0.70:
                    hour = random.randint(win_start, win_end)
                else:
                    hour = random.randint(8, 22)

                # Compute base probability
                base_p = BASE_PROBS[persona][chosen_type]

                # Persona dynamic multiplier
                if persona == "fading":
                    if chosen_type == "order_update":
                        base_p = max(0.60, 0.95 - (0.35 * (day / 90.0)))
                    else:
                        base_p = base_p * math.exp(-day / tau)
                elif persona == "recovering":
                    if chosen_type != "order_update":
                        if 25 <= day < 60:
                            base_p = base_p * 0.15
                        elif 60 <= day <= 75:
                            # Linear from 0.15 to 1.0
                            alpha = (day - 60) / 15.0
                            mult = 0.15 + (1.0 - 0.15) * alpha
                            base_p = base_p * mult

                # Preferred window multiplier
                is_in_window = win_start <= hour <= win_end
                win_mult = 1.2 if is_in_window else 0.7
                p = base_p * win_mult

                # Fatigue effect
                if chosen_type != "order_update":
                    fatigue_mult = max(0.40, (0.96 ** consecutive_promo_ignores))
                    p = p * fatigue_mult

                # Daily volume penalty if more than 2 in a day
                if notif_idx >= 2:
                    p = p * (0.85 ** (notif_idx - 1))

                # Add small noise (+/- 0.05, clipped to [0.01, 0.99])
                noise = random.uniform(-0.05, 0.05)
                p = float(np.clip(p + noise, 0.01, 0.99))

                # Open decision
                is_opened = random.random() < p

                if is_opened:
                    action = "opened"
                    # Reset streaks
                    if chosen_type != "order_update":
                        consecutive_promo_ignores = 0
                    consecutive_ignores_by_type[chosen_type] = 0

                    # Delay (median 25 min; interested faster)
                    is_fav = (chosen_type == FAVORITE_TYPE[persona])
                    delay_median = 12.0 if is_fav else 25.0
                    delay_mu = math.log(delay_median)
                    response_delay = float(np.random.lognormal(mean=delay_mu, sigma=0.6))
                    response_delay = round(max(1.0, min(1440.0, response_delay)), 1)

                    # View seconds
                    # skew towards longer if base >= 0.6
                    high_base = (BASE_PROBS[persona][chosen_type] >= 0.60)
                    r_view = random.random()
                    if high_base:
                        # 20% quick, 40% few seconds, 40% read fully
                        if r_view < 0.20:
                            view_sec = random.randint(1, 3)
                        elif r_view < 0.60:
                            view_sec = random.randint(4, 10)
                        else:
                            view_sec = random.randint(11, 40)
                    else:
                        # 35% quick, 40% few seconds, 25% read fully
                        if r_view < 0.35:
                            view_sec = random.randint(1, 3)
                        elif r_view < 0.75:
                            view_sec = random.randint(4, 10)
                        else:
                            view_sec = random.randint(11, 40)

                    # Click probability given open
                    click_base_rates = {
                        "price_drop": 0.45,
                        "offer": 0.30,
                        "new_arrival": 0.25,
                        "order_update": 0.15
                    }
                    click_prob = click_base_rates[chosen_type]
                    if is_fav:
                        click_prob = click_prob * 1.3
                    clicked = 1 if (random.random() < click_prob) else 0

                    # Save for later given open
                    save_base_rates = {
                        "price_drop": 0.20,
                        "new_arrival": 0.10,
                        "offer": 0.05,
                        "order_update": 0.05
                    }
                    save_prob = save_base_rates[chosen_type]
                    saved = 1 if (random.random() < save_prob) else 0

                    muted_event = 0

                else:
                    # Not opened: 70% ignored, 30% dismissed
                    action = "ignored" if (random.random() < 0.70) else "dismissed"
                    response_delay = None
                    view_sec = 0
                    clicked = 0
                    saved = 0

                    if chosen_type != "order_update":
                        consecutive_promo_ignores += 1
                    consecutive_ignores_by_type[chosen_type] += 1

                    # Muting check: after 6 consecutive ignored of this type, 15% chance
                    muted_event = 0
                    if chosen_type != "order_update" and consecutive_ignores_by_type[chosen_type] >= 6:
                        if random.random() < 0.15:
                            muted_types.add(chosen_type)
                            muted_event = 1

                notifications.append({
                    "customer_id": cid,
                    "day": day,
                    "hour": hour,
                    "notification_type": chosen_type,
                    "action": action,
                    "response_delay_minutes": response_delay,
                    "view_seconds": view_sec,
                    "clicked": clicked,
                    "saved": saved,
                    "muted_type": muted_event,
                    "unsubscribed": 1 if unsubscribed else 0
                })

    notif_df = pd.DataFrame(notifications)
    notif_df.to_csv(os.path.join(output_dir, "notifications.csv"), index=False)

    # 3. Print Data Summary
    print("=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)
    print(f"Total customers simulated: {len(cust_df)}")
    print(f"Total notification events: {len(notif_df)}")
    open_rate_overall = (notif_df['action'] == 'opened').mean()
    print(f"Overall open rate: {open_rate_overall:.2%}")
    print("\nOpen rate per persona:")
    merged = notif_df.merge(cust_df[['customer_id', 'persona']], on='customer_id')
    persona_stats = merged.groupby('persona')[['action', 'clicked']].apply(
        lambda g: pd.Series({
            'total_notifs': len(g),
            'open_rate': (g['action'] == 'opened').mean(),
            'click_rate_opened': g.loc[g['action'] == 'opened', 'clicked'].mean()
        }),
        include_groups=False
    )
    for p_name, row in persona_stats.iterrows():
        print(f"  {p_name:20s}: Open Rate {row['open_rate']:.1%}, Clicks/Open {row['click_rate_opened']:.1%}")

    # 4. Generate Reports & Plots
    # Chart 1: Average weekly open rate per persona
    merged['week'] = merged['day'] // 7
    weekly_persona_open = merged.groupby(['week', 'persona'])['action'].apply(
        lambda g: (g == 'opened').mean()
    ).unstack('persona')

    plt.figure(figsize=(10, 6))
    for col in weekly_persona_open.columns:
        plt.plot(weekly_persona_open.index, weekly_persona_open[col], label=col, linewidth=2)
    plt.title("Average Weekly Open Rate by Persona (90 Days)", fontsize=14, fontweight='bold')
    plt.xlabel("Week", fontsize=12)
    plt.ylabel("Open Rate", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()
    chart1_path = os.path.join(reports_dir, "open_rates_by_persona.png")
    plt.savefig(chart1_path, dpi=150)
    plt.close()
    print(f"Saved chart: {chart1_path}")

    # Chart 2: Share unsubscribed over time
    # For each day, count how many customers have stopped receiving notifications because of unsubscribe
    # We find unsubscribe day for each customer who unsubscribed
    unsub_records = notif_df.groupby('customer_id')['unsubscribed'].max()
    unsub_customers = set(unsub_records[unsub_records == 1].index)
    # The day after last notification is unsubscribe day (or day where unsubscribed==1)
    last_day_per_cust = notif_df.groupby('customer_id')['day'].max()

    days_axis = list(range(total_days))
    unsub_shares = []
    for d in days_axis:
        churned_so_far = sum(1 for cid in unsub_customers if last_day_per_cust[cid] <= d)
        unsub_shares.append(churned_so_far / total_customers)

    plt.figure(figsize=(8, 5))
    plt.plot(days_axis, unsub_shares, color='#dc2626', linewidth=2.5)
    plt.title("Cumulative Share Unsubscribed Over Time", fontsize=14, fontweight='bold')
    plt.xlabel("Day", fontsize=12)
    plt.ylabel("Share of Customers Unsubscribed", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    chart2_path = os.path.join(reports_dir, "unsubscribed_over_time.png")
    plt.savefig(chart2_path, dpi=150)
    plt.close()
    print(f"Saved chart: {chart2_path}")
    print("=" * 60)

    return cust_df, notif_df


if __name__ == "__main__":
    generate_dataset()
