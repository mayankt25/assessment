"""Generate synthetic trading data: 800 trades across 8 users with distinct behavior profiles."""

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────
random.seed(42)

NUM_USERS = 8
TRADES_PER_USER = 100
TOTAL_TRADES = NUM_USERS * TRADES_PER_USER

INSTRUMENTS = [
    "Volatility 75 Index", "Volatility 100 Index", "EURUSD", "GBPUSD",
    "USDJPY", "Gold", "Crude Oil", "Nasdaq 100", "Bitcoin/USD",
]
DIRECTION = ["rise", "fall"]
RESULTS = ["win", "loss"]

BASE_DATE = datetime(2025, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
CALENDAR_END = datetime(2025, 8, 30, 23, 59, 59, tzinfo=timezone.utc)

TRADES_FILE = Path("data/trades.json")
CALENDAR_FILE = Path("data/economic_calendar.json")


# ── Helpers ────────────────────────────────────────────────────────────
def iso(ts):
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def make_trade(user_id, trade_num, open_ts, result, stake, instrument, direction, session_id):
    close_ts = open_ts + timedelta(seconds=random.randint(20, 50))
    payout = round(stake * 1.9, 2) if result == "win" else 0
    return {
        "user_id": user_id,
        "trade_id": f"t_{trade_num:05d}",
        "open_ts": iso(open_ts),
        "close_ts": iso(close_ts),
        "instrument": instrument,
        "direction": direction,
        "stake_usd": stake,
        "payout_usd": payout,
        "result": result,
        "session_id": session_id,
    }


# ── User profile generators ────────────────────────────────────────────
def user_001_martingale():
    """Martingale + position_doubling: double stake after each loss."""
    trades = []
    trade_num = 1
    ts = BASE_DATE + timedelta(hours=8)
    session = "s_4401"
    stake = 5
    for i in range(TRADES_PER_USER):
        if i > 0 and i % 20 == 0:
            ts += timedelta(hours=random.randint(1, 3))
            session = f"s_{4401 + i // 20}"
            stake = 5  # reset
        result = random.choice(["win", "loss"])
        direction = random.choice(DIRECTION)
        inst = random.choice(INSTRUMENTS)
        open_ts = ts
        trades.append(make_trade("u_001", trade_num, open_ts, result, stake, inst, direction, session))
        # Martingale: double after loss, reset to base after win
        if result == "loss":
            stake = min(stake * 2, 500)
        else:
            stake = 5
        ts += timedelta(seconds=random.randint(30, 90))
        trade_num += 1
    return trades


def user_002_revenge():
    """Revenge trading: quick trades after losses."""
    trades = []
    trade_num = TRADES_PER_USER + 1
    ts = BASE_DATE + timedelta(hours=10)
    session = "s_5501"
    stake = random.randint(20, 50)
    for i in range(TRADES_PER_USER):
        if i > 0 and i % 25 == 0:
            ts += timedelta(hours=random.randint(2, 4))
            session = f"s_{5501 + i // 25}"
        result = random.choice(["win", "loss"])
        direction = random.choice(DIRECTION)
        inst = random.choice(INSTRUMENTS)
        open_ts = ts
        trades.append(make_trade("u_002", trade_num, open_ts, result, stake, inst, direction, session))
        # Revenge: if loss, next trade comes very fast
        if result == "loss":
            ts += timedelta(seconds=random.randint(30, 110))
        else:
            ts += timedelta(minutes=random.randint(5, 30))
        trade_num += 1
    return trades


def user_003_news_chasing():
    """News chasing: 40%+ trades within 5 min of high-impact news."""
    trades = []
    trade_num = TRADES_PER_USER * 2 + 1
    ts = BASE_DATE + timedelta(hours=12)
    session = "s_6601"
    stake = random.randint(30, 80)
    # High-impact news times
    news_times = [
        BASE_DATE + timedelta(days=d, hours=13, minutes=30)
        for d in range(0, 20, 3)
    ]
    news_times += [
        BASE_DATE + timedelta(days=d, hours=15, minutes=0)
        for d in range(1, 20, 4)
    ]
    ni = 0
    for i in range(TRADES_PER_USER):
        if i > 0 and i % 20 == 0:
            ts = BASE_DATE + timedelta(days=i // 20, hours=12 + random.randint(0, 6))
            session = f"s_{6601 + i // 20}"
        # 40% chance to place near a news event
        if ni < len(news_times) and random.random() < 0.45:
            ts = news_times[ni] + timedelta(seconds=random.randint(-280, 280))
            ni += 1
        result = random.choice(["win", "loss"])
        direction = random.choice(DIRECTION)
        inst = random.choice(INSTRUMENTS)
        open_ts = ts
        trades.append(make_trade("u_003", trade_num, open_ts, result, stake, inst, direction, session))
        ts += timedelta(minutes=random.randint(10, 60))
        trade_num += 1
    return trades


def user_004_scalping():
    """Scalping: high frequency, small stakes, short sessions."""
    trades = []
    trade_num = TRADES_PER_USER * 3 + 1
    ts = BASE_DATE + timedelta(hours=14)
    session = "s_7701"
    stake = random.randint(10, 20)
    for i in range(TRADES_PER_USER):
        if i > 0 and i % 30 == 0:
            ts += timedelta(hours=random.randint(1, 2))
            session = f"s_{7701 + i // 30}"
        result = random.choice(["win", "loss"])
        direction = random.choice(DIRECTION)
        inst = random.choice(INSTRUMENTS[:3])
        open_ts = ts
        trades.append(make_trade("u_004", trade_num, open_ts, result, stake, inst, direction, session))
        ts += timedelta(seconds=random.randint(3, 10))  # very fast trades
        trade_num += 1
    return trades


def user_005_anti_martingale():
    """Anti-martingale: increase stake after wins."""
    trades = []
    trade_num = TRADES_PER_USER * 4 + 1
    ts = BASE_DATE + timedelta(hours=16)
    session = "s_8801"
    stake = 10
    for i in range(TRADES_PER_USER):
        if i > 0 and i % 20 == 0:
            ts += timedelta(hours=random.randint(1, 3))
            session = f"s_{8801 + i // 20}"
            stake = 10
        result = random.choice(["win", "loss"])
        if result == "win":
            stake = min(stake * 1.5, 200)
        else:
            stake = max(10, int(stake * 0.7))
        direction = random.choice(DIRECTION)
        inst = random.choice(INSTRUMENTS)
        open_ts = ts
        trades.append(make_trade("u_005", trade_num, open_ts, result, stake, inst, direction, session))
        ts += timedelta(minutes=random.randint(2, 15))
        trade_num += 1
    return trades


def user_006_normal():
    """Normal: steady stakes, ~50% win rate."""
    trades = []
    trade_num = TRADES_PER_USER * 5 + 1
    ts = BASE_DATE + timedelta(hours=18)
    session = "s_9901"
    stake = 25
    for i in range(TRADES_PER_USER):
        if i > 0 and i % 20 == 0:
            ts += timedelta(hours=random.randint(1, 3))
            session = f"s_{9901 + i // 20}"
        result = "win" if random.random() < 0.5 else "loss"
        direction = random.choice(DIRECTION)
        inst = random.choice(INSTRUMENTS)
        open_ts = ts
        trades.append(make_trade("u_006", trade_num, open_ts, result, stake, inst, direction, session))
        ts += timedelta(minutes=random.randint(10, 40))
        trade_num += 1
    return trades


def user_007_insufficient_evidence():
    """Mixed/noisy behavior, no dominant pattern."""
    trades = []
    trade_num = TRADES_PER_USER * 6 + 1
    ts = BASE_DATE + timedelta(days=1, hours=8)
    session = "s_1101"
    stake = random.randint(10, 60)
    for i in range(TRADES_PER_USER):
        if i > 0 and i % 25 == 0:
            ts += timedelta(hours=random.randint(1, 4))
            session = f"s_{1101 + i // 25}"
        result = random.choice(["win", "loss"])
        stake = random.randint(10, 80)
        direction = random.choice(DIRECTION)
        inst = random.choice(INSTRUMENTS)
        open_ts = ts
        trades.append(make_trade("u_007", trade_num, open_ts, result, stake, inst, direction, session))
        ts += timedelta(minutes=random.randint(3, 45))
        trade_num += 1
    return trades


def user_008_mixed():
    """Mixed scalping + news chasing."""
    trades = []
    trade_num = TRADES_PER_USER * 7 + 1
    ts = BASE_DATE + timedelta(days=2, hours=9)
    session = "s_2201"
    stake = random.randint(10, 25)
    news_times = [
        BASE_DATE + timedelta(days=d, hours=13, minutes=30)
        for d in range(2, 20, 5)
    ]
    ni = 0
    for i in range(TRADES_PER_USER):
        if i > 0 and i % 25 == 0:
            ts += timedelta(hours=random.randint(1, 3))
            session = f"s_{2201 + i // 25}"
        # 30% near news
        if ni < len(news_times) and random.random() < 0.35:
            ts = news_times[ni] + timedelta(seconds=random.randint(-280, 280))
            ni += 1
        result = random.choice(["win", "loss"])
        direction = random.choice(DIRECTION)
        inst = random.choice(INSTRUMENTS[:3])
        open_ts = ts
        trades.append(make_trade("u_008", trade_num, open_ts, result, stake, inst, direction, session))
        ts += timedelta(seconds=random.randint(5, 15))  # fast
        trade_num += 1
    return trades


# ── Generate trades ───────────────────────────────────────────────────
all_trades = []
all_trades.extend(user_001_martingale())
all_trades.extend(user_002_revenge())
all_trades.extend(user_003_news_chasing())
all_trades.extend(user_004_scalping())
all_trades.extend(user_005_anti_martingale())
all_trades.extend(user_006_normal())
all_trades.extend(user_007_insufficient_evidence())
all_trades.extend(user_008_mixed())

# Sort all trades by open_ts
all_trades.sort(key=lambda t: t["open_ts"])

# Re-number trade IDs globally
for i, t in enumerate(all_trades, 1):
    t["trade_id"] = f"t_{i:05d}"

# ── Generate economic calendar ─────────────────────────────────────────
events = []
event_id = 1
for day in range(0, 30):
    date = BASE_DATE + timedelta(days=day)
    # High impact on weekdays at 13:30 and 15:00
    if date.weekday() < 5:
        events.append({
            "datetime_utc": iso(date.replace(hour=13, minute=30, second=0)),
            "event": "US NFP" if day % 7 == 0 else "CPI Release" if day % 5 == 0 else "Interest Rate Decision",
            "impact": "high",
        })
        events.append({
            "datetime_utc": iso(date.replace(hour=15, minute=0, second=0)),
            "event": "GDP Release" if day % 7 == 0 else "Retail Sales" if day % 5 == 0 else "PMI Manufacturing",
            "impact": "high",
        })
        event_id += 2
    # Medium impact events
    if random.random() < 0.7:
        events.append({
            "datetime_utc": iso(date.replace(hour=random.randint(9, 16), minute=random.randint(0, 59), second=0)),
            "event": random.choice(["Unemployment Claims", "Building Permits", "Industrial Production"]),
            "impact": "medium",
        })
        event_id += 1
    # Low impact events
    if random.random() < 0.5:
        events.append({
            "datetime_utc": iso(date.replace(hour=random.randint(8, 17), minute=random.randint(0, 59), second=0)),
            "event": random.choice(["Export Prices", "Import Prices", "Consumer Sentiment"]),
            "impact": "low",
        })
        event_id += 1

# Cap events to a reasonable number
events = events[:50]

# ── Save ──────────────────────────────────────────────────────────────
TRADES_FILE.parent.mkdir(exist_ok=True)
CALENDAR_FILE.parent.mkdir(exist_ok=True)

with open(TRADES_FILE, "w") as f:
    json.dump({"trades": all_trades}, f, indent=2)

with open(CALENDAR_FILE, "w") as f:
    json.dump(events, f, indent=2)

print(f"Generated {len(all_trades)} trades across {NUM_USERS} users")
print(f"Generated {len(events)} economic calendar events")
print(f"Saved trades to {TRADES_FILE}")
print(f"Saved calendar to {CALENDAR_FILE}")
