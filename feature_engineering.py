"""Deterministic behavioural feature engineering for each user."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import FEATURES_DIR, DATA_DIR

TRADES_FILE = DATA_DIR / "trades.json"
CALENDAR_FILE = DATA_DIR / "economic_calendar.json"

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def parse_ts(ts_str):
    return datetime.strptime(ts_str, ISO_FMT).replace(tzinfo=timezone.utc)


def load_data():
    with open(TRADES_FILE) as f:
        trades_data = json.load(f)["trades"]
    with open(CALENDAR_FILE) as f:
        calendar = json.load(f)
    return trades_data, calendar


def get_high_impact_times(calendar, window_minutes=5):
    """Return list of (event_start, event_end) UTC datetimes for high-impact events."""
    window = timedelta(minutes=window_minutes)
    times = []
    for ev in calendar:
        if ev.get("impact") == "high":
            dt = parse_ts(ev["datetime_utc"])
            times.append((dt - window, dt + window))
    return times


def is_near_news(trade_open, high_impact_windows):
    to = parse_ts(trade_open)
    return any(start <= to <= end for start, end in high_impact_windows)


def group_sessions(trades, max_gap_minutes=30):
    """Group trades into sessions (gap > max_gap_minutes separates sessions)."""
    if not trades:
        return []
    sessions = [[trades[0]]]
    gap = timedelta(minutes=max_gap_minutes)
    for t in trades[1:]:
        prev_close = parse_ts(trades[-1]["close_ts"])
        cur_open = parse_ts(t["open_ts"])
        if cur_open - prev_close <= gap:
            sessions[-1].append(t)
        else:
            sessions.append([t])
    return sessions


def compute_features_for_user(user_id, trades, high_impact_windows):
    """Compute all behavioural features for a single user (deterministic)."""
    if not trades:
        return None

    # Sort by open_ts
    trades_sorted = sorted(trades, key=lambda t: parse_ts(t["open_ts"]))

    total_trades = len(trades_sorted)
    stakes = [t["stake_usd"] for t in trades_sorted]
    total_stake = sum(stakes)
    average_stake = round(total_stake / total_trades, 2)

    # Win/loss
    wins = [t for t in trades_sorted if t["result"] == "win"]
    losses = [t for t in trades_sorted if t["result"] == "loss"]
    win_rate = round((len(wins) / total_trades) * 100, 2) if total_trades else 0

    # Net profit/loss
    total_net = round(sum(t["payout_usd"] - t["stake_usd"] for t in trades_sorted), 2)

    # Trading duration
    first_open = parse_ts(trades_sorted[0]["open_ts"])
    last_open = parse_ts(trades_sorted[-1]["open_ts"])
    total_trading_minutes = max((last_open - first_open).total_seconds() / 60, 1)
    trades_per_minute = round(total_trades / total_trading_minutes, 4)

    # Stake escalation after losses
    escalation_pairs = []
    for i, t in enumerate(trades_sorted[:-1]):
        if t["result"] == "loss":
            next_stake = trades_sorted[i + 1]["stake_usd"]
            ratio = round(next_stake / t["stake_usd"], 4) if t["stake_usd"] > 0 else 1.0
            escalation_pairs.append({
                "loss_trade_id": t["trade_id"],
                "next_trade_id": trades_sorted[i + 1]["trade_id"],
                "ratio": ratio,
            })
    escalation_ratios = [p["ratio"] for p in escalation_pairs]
    stake_escalation_ratio = round(sum(escalation_ratios) / len(escalation_ratios), 4) if escalation_ratios else 1.0

    # Revenge interval (time between losing trade close and next trade open)
    revenge_intervals = []
    for i, t in enumerate(trades_sorted[:-1]):
        if t["result"] == "loss":
            close_t = parse_ts(t["close_ts"])
            next_open = parse_ts(trades_sorted[i + 1]["open_ts"])
            interval = (next_open - close_t).total_seconds()
            revenge_intervals.append({
                "loss_trade_id": t["trade_id"],
                "next_trade_id": trades_sorted[i + 1]["trade_id"],
                "interval_seconds": round(interval, 2),
            })
    avg_revenge_interval = (
        round(sum(r["interval_seconds"] for r in revenge_intervals) / len(revenge_intervals), 2)
        if revenge_intervals else None
    )

    # Longest losing streak
    max_streak = 0
    current_streak = 0
    streak_sequences = []
    current_seq = []
    for t in trades_sorted:
        if t["result"] == "loss":
            current_streak += 1
            current_seq.append(t["trade_id"])
        else:
            if current_streak > max_streak:
                max_streak = current_streak
                streak_sequences = [list(current_seq)]
            elif current_streak == max_streak and current_streak > 0:
                streak_sequences.append(list(current_seq))
            current_streak = 0
            current_seq = []
    if current_streak > max_streak:
        max_streak = current_streak
        streak_sequences = [list(current_seq)]
    elif current_streak == max_streak and current_streak > 0:
        streak_sequences.append(list(current_seq))

    # Trades near high-impact news
    near_news = []
    for t in trades_sorted:
        if is_near_news(t["open_ts"], high_impact_windows):
            near_news.append({
                "trade_id": t["trade_id"],
                "open_ts": t["open_ts"],
            })
    pct_near_news = round((len(near_news) / total_trades) * 100, 2) if total_trades else 0

    # Session duration
    sessions = group_sessions(trades_sorted)
    session_durations = []
    for sess in sessions:
        if len(sess) > 1:
            dur = (parse_ts(sess[-1]["close_ts"]) - parse_ts(sess[0]["open_ts"])).total_seconds() / 60
            session_durations.append(round(dur, 2))
    avg_session_duration = (
        round(sum(session_durations) / len(session_durations), 2)
        if session_durations else None
    )

    return {
        "user_id": user_id,
        "total_trades": total_trades,
        "average_stake": average_stake,
        "total_stake_usd": total_stake,
        "stake_escalation_ratio_after_losses": stake_escalation_ratio,
        "escalation_pairs": escalation_pairs,
        "trades_per_minute": trades_per_minute,
        "total_trading_minutes": round(total_trading_minutes, 2),
        "pct_trades_near_high_impact_news": pct_near_news,
        "near_news_count": len(near_news),
        "near_news_trades": near_news,
        "win_rate": win_rate,
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "revenge_interval_seconds": avg_revenge_interval,
        "revenge_intervals": revenge_intervals,
        "longest_losing_streak": max_streak,
        "losing_streak_sequences": streak_sequences,
        "total_net_profit_loss": total_net,
        "average_session_duration_minutes": avg_session_duration,
        "session_count": len(sessions),
        "session_durations": session_durations,
    }


def main():
    trades_data, calendar = load_data()

    # Build high-impact windows once
    high_impact_windows = get_high_impact_times(calendar, window_minutes=5)

    # Group trades by user
    user_trades = {}
    for t in trades_data:
        uid = t["user_id"]
        user_trades.setdefault(uid, []).append(t)

    FEATURES_DIR.mkdir(exist_ok=True)

    for user_id, trades in user_trades.items():
        features = compute_features_for_user(user_id, trades, high_impact_windows)
        if features:
            out_file = FEATURES_DIR / f"{user_id}.json"
            with open(out_file, "w") as f:
                json.dump(features, f, indent=2)
            print(f"Features saved: {out_file}")

    print(f"\nComputed features for {len(user_trades)} users")


if __name__ == "__main__":
    main()
