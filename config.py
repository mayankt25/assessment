import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
FEATURES_DIR = BASE_DIR / "features"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
MESSAGES_DIR = BASE_DIR / "messages"

for d in (DATA_DIR, FEATURES_DIR, OUTPUT_DIR, LOGS_DIR, MESSAGES_DIR):
    d.mkdir(exist_ok=True)

TRADES_FILE = DATA_DIR / "trades.json"
CALENDAR_FILE = DATA_DIR / "economic_calendar.json"
PATTERNS_FILE = OUTPUT_DIR / "patterns.json"
RISK_SCORES_FILE = OUTPUT_DIR / "risk_scores.json"
INTERVENTIONS_FILE = OUTPUT_DIR / "interventions.json"
LLM_CALLS_FILE = LOGS_DIR / "llm_calls.jsonl"
RISK_MODEL_FILE = BASE_DIR / "risk_model.md"
FALSE_POSITIVE_FILE = OUTPUT_DIR / "false_positive_audit.json"
COHORT_INSIGHTS_FILE = OUTPUT_DIR / "cohort_insights.json"
REGULATORY_FILE = OUTPUT_DIR / "regulatory_mapping.json"

# ── LLM ───────────────────────────────────────────────────────────────
KEY = os.getenv("KEY")
BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "google/gemma-3-27b-it:free"

# ── Controlled Vocabularies ───────────────────────────────────────────
CONTROLLED_PATTERNS = [
    "martingale",
    "anti_martingale",
    "revenge_trading",
    "news_chasing",
    "scalping",
    "position_doubling",
    "normal",
    "insufficient_evidence",
]

INTERVENTION_TYPES = [
    "soft_nudge",
    "deposit_limit_prompt",
    "cooling_off_period",
    "human_outreach",
]

RISK_TIERS = ["low", "medium", "high", "critical"]

# ── Replayability ──────────────────────────────────────────────────────
RANDOM_SEED = 42

# ── Pattern Definitions (for LLM prompts) ────────────────────────────
PATTERN_DEFINITIONS = {
    "martingale": "Increasing stake after losses systematically (e.g., doubling stake after each loss)",
    "anti_martingale": "Increasing stake after wins systematically (e.g., increasing stake after each win)",
    "revenge_trading": "Quickly placing a trade after a loss in an attempt to recover losses, typically within a very short time window",
    "news_chasing": "Placing trades within 5 minutes of high-impact economic news events",
    "scalping": "High-frequency trading with many rapid trades, small stakes, and short holding times (typically under 1 minute)",
    "position_doubling": "Suddenly increasing stake by 2x or more between two consecutive trades",
    "normal": "No concerning trading patterns detected; trading behavior appears balanced and within reasonable limits",
    "insufficient_evidence": "The available data is inconclusive for any specific pattern classification",
}

INTERVENTION_DEFINITIONS = {
    "soft_nudge": "Gentle in-app reminder about trading behavior, encouraging the user to review their activity",
    "deposit_limit_prompt": "Prompt the user to consider setting or lowering a deposit limit to manage their spending",
    "cooling_off_period": "Recommend that the user takes a short break from trading to reset their decision-making",
    "human_outreach": "Assign a human customer-service representative to reach out directly to the user for a wellness check and support",
}

# ── Risk Scoring Weights ─────────────────────────────────────────────
RISK_FORMULA_VERSION = "1.0"

PATTERN_SCORES = {
    "martingale": 20,
    "position_doubling": 15,
    "revenge_trading": 12,
    "news_chasing": 10,
    "scalping": 5,
    "anti_martingale": 2,
    "normal": 0,
    "insufficient_evidence": 0,
}

# Stake escalation ratio buckets: (min_ratio_exclusive, score)
STAKE_ESCALATION_BUCKETS = [(2.0, 15), (1.5, 5)]

# Losing streak buckets: (min_streak_exclusive, score)
LOSING_STREAK_BUCKETS = [(5, 10), (3, 5)]

# Recent net loss (last 10 trades): (min_loss_exclusive, score)
RECENT_LOSS_BUCKETS = [(-100, 10), (0, 5)]

# Trades per minute buckets: (min_tpm_exclusive, score)
TPM_BUCKETS = [(5, 10), (2, 5)]

# News concentration buckets: (min_pct_exclusive, score)
NEWS_CONC_BUCKETS = [(50, 15), (30, 10)]

RISK_TIER_THRESHOLDS = {"low": (0, 29), "medium": (30, 59), "high": (60, 79), "critical": (80, 100)}
