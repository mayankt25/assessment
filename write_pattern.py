import json

code = r"""\"\"\"Per-user LLM pattern classification (Stage1). Uses OpenRouter API.\"\"\"

import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone

from openai import OpenAI
from dotenv import load_dotenv

from config import (
    MODEL, BASE_URL, KEY, PATTERNS_FILE, FEATURES_DIR, LOGS_DIR,
    CONTROLLED_PATTERNS, PATTERN_DEFINITIONS, LLM_CALLS_FILE,
)

load_dotenv()

client = OpenAI(api_key=KEY, base_url=BASE_URL)


def prompt_hash(prompt):
    return hashlib.sha256(prompt.encode()).hexdigest()


def log_llm_call(stage, user_id, timestamp, model, prompt, input_artifacts, output_artifact):
    LOGS_DIR.mkdir(exist_ok=True)
    entry = {
        "stage": stage,
        "user_id": user_id,
        "timestamp": timestamp,
        "provider": "openrouter",
        "model": model,
        "prompt_hash": prompt_hash(prompt),
        "input_artifacts": input_artifacts,
        "output_artifact": output_artifact,
    }
    with open(LLM_CALLS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def build_prompt(user_id, features, last_30_trades):
    compact = []
    for t in last_30_trades:
        compact.append({
            "tid": t["trade_id"],
            "ts": t["open_ts"],
            "dir": t["direction"],
            "stake": t["stake_usd"],
            "res": t["result"],
            "inst": t["instrument"],
        })

    vocab_defs = "\n".join(
        "- {0}: {1}".format(p, PATTERN_DEFINITIONS[p])
        for p in CONTROLLED_PATTERNS
    )

    parts = []
    parts.append("You are a trading behaviour analyst. Classify the user using ONLY the controlled vocabulary below.")
    parts.append("## Controlled Vocabulary & Definitions")
    parts.append(vocab_defs)
    parts.append("## Rules")
    parts.append("- You MAY assign one or more labels from the vocabulary.")
    parts.append("- If the data clearly shows a pattern, use that specific label.")
    parts.append("- If multiple patterns apply, list all that apply.")
    parts.append("- If data is inconclusive, use 'insufficient_evidence'.")
    parts.append("- If behaviour is normal with no concerns, use 'normal'.")
    parts.append("## User ID")
    parts.append(user_id)
    parts.append("## Computed Feature Vector")
    parts.append(json.dumps(features, indent=2))
    parts.append("## Last " + str(len(last_30_trades)) + " Trades (compact format)")
    parts.append(json.dumps(compact, indent=2))
    parts.append("## Output Format")
    parts.append('Return valid JSON only (no markdown fences, no explanations outside JSON):')
    parts.append('{"user_id": "' + user_id + '", "patterns": ["pattern1"], "evidence": [{"pattern": "pattern_name", "triggering_features": ["feature_name"], "trade_ids": ["t_xxxxx"], "explanation": "Why detected."}], "confidence": "low"}')
    return "\n".join(parts)


def call_llm(prompt, retries=3):
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=1024,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print("LLM call failed (attempt {}/{}): {}".format(attempt + 1, retries, e))
            if attempt < retries - 1:
                time.sleep(5)
    return None


def parse_response(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(l for l in lines if not l.strip().startswith("```"))
    return json.loads(text)


def main():
    with open("data/trades.json") as f:
        all_trades = json.load(f)["trades"]

    user_trades = {}
    for t in all_trades:
        user_trades.setdefault(t["user_id"], []).append(t)
    for uid in user_trades:
        user_trades[uid].sort(key=lambda t: t["open_ts"])

    features_by_user = {}
    for uid in user_trades:
        fpath = FEATURES_DIR / "{}.json".format(uid)
        with open(fpath) as f:
            features_by_user[uid] = json.load(f)

    results = []
    for uid in sorted(user_trades.keys()):
        features = features_by_user[uid]
        trades = user_trades[uid]
        last_30 = trades[-30:]

        print("Classifying {}...".format(uid))

        prompt = build_prompt(uid, features, last_30)
        input_artifacts = [str(FEATURES_DIR / "{}.json".format(uid))]

        parsed = None
        for attempt in range(2):
            raw = call_llm(prompt)
            if raw is None:
                time.sleep(4)
                continue
            try:
                parsed = parse_response(raw)
                assert parsed["user_id"] == uid, "user_id mismatch"
                for p in parsed["patterns"]:
                    assert p in CONTROLLED_PATTERNS, "Invalid pattern: {}".format(p)
                break
            except Exception as e:
                print("  Parse failed (attempt {}): {}".format(attempt + 1, e))
                time.sleep(2)

        if parsed is None:
            print("  Using fallback for {}".format(uid))
            parsed = {
                "user_id": uid,
                "patterns": ["insufficient_evidence"],
                "evidence": [],
                "confidence": "low",
            }
        else:
            results.append(parsed)
            print("  Patterns: {} (confidence: {})".format(
                parsed["patterns"], parsed.get("confidence", "N/A")))

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        log_llm_call(
            stage="pattern_classification",
            user_id=uid,
            timestamp=ts,
            model=MODEL,
            prompt=prompt,
            input_artifacts=input_artifacts,
            output_artifact=str(PATTERNS_FILE),
        )
        time.sleep(4)

    PATTERNS_FILE.parent.mkdir(exist_ok=True)
    with open(PATTERNS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print("\nSaved patterns for {} users to {}".format(len(results), PATTERNS_FILE))


if __name__ == "__main__":
    main()
"""
with open('pattern_detection.py', 'w') as f:
    f.write(code)
print('pattern_detection.py written successfully')
