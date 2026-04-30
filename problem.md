## BUILD

Build a replayable pipeline that ingests anonymised trading-session data, computes deterministic behavioural features, uses staged LLM calls to classify trading behaviour from a controlled vocabulary, calculates auditable risk scores in code, and produces a responsible-trading intervention plan ranked by risk.

This is not a one-shot profiling report. The evaluator will run the pipeline from a clean checkout, may replace the input data with equivalent fixtures, and will verify that features and risk scores are computed deterministically rather than delegated to the LLM.

The pipeline must preserve intermediate artifacts, enforce stage separation, log LLM calls, and ensure that intervention recommendations are grounded in computed evidence.

---

## INPUT FILES

Your pipeline must read the following files from disk:

- `trades.json`
- `economic_calendar.json`

The sample data below is provided as a seed fixture. Your pipeline must extend or generate synthetic anonymised data to at least:

- 8 anonymised users
- 800 total trades

The evaluator may replace the input files with equivalent data using the same schema. Your implementation must not depend on exact user ordering, trade ordering, or hardcoded final outputs.

---

## SAMPLE `trades.json`

```json
{
  "trades": [
    {
      "user_id": "u_001",
      "trade_id": "t_00001",
      "open_ts": "2025-08-01T08:14:22Z",
      "close_ts": "2025-08-01T08:14:55Z",
      "instrument": "Volatility 75 Index",
      "direction": "rise",
      "stake_usd": 5,
      "payout_usd": 0,
      "result": "loss",
      "session_id": "s_4412"
    },
    {
      "user_id": "u_001",
      "trade_id": "t_00002",
      "open_ts": "2025-08-01T08:15:01Z",
      "close_ts": "2025-08-01T08:15:34Z",
      "instrument": "Volatility 75 Index",
      "direction": "rise",
      "stake_usd": 10,
      "payout_usd": 0,
      "result": "loss",
      "session_id": "s_4412"
    },
    {
      "user_id": "u_001",
      "trade_id": "t_00003",
      "open_ts": "2025-08-01T08:15:40Z",
      "close_ts": "2025-08-01T08:16:13Z",
      "instrument": "Volatility 75 Index",
      "direction": "rise",
      "stake_usd": 20,
      "payout_usd": 0,
      "result": "loss",
      "session_id": "s_4412"
    },
    {
      "user_id": "u_001",
      "trade_id": "t_00004",
      "open_ts": "2025-08-01T08:16:20Z",
      "close_ts": "2025-08-01T08:16:53Z",
      "instrument": "Volatility 75 Index",
      "direction": "rise",
      "stake_usd": 40,
      "payout_usd": 76,
      "result": "win",
      "session_id": "s_4412"
    },
    {
      "user_id": "u_002",
      "trade_id": "t_00005",
      "open_ts": "2025-08-01T13:29:55Z",
      "close_ts": "2025-08-01T13:30:25Z",
      "instrument": "EURUSD",
      "direction": "rise",
      "stake_usd": 50,
      "payout_usd": 0,
      "result": "loss",
      "session_id": "s_5511"
    }
  ]
}
```

---

## SAMPLE `economic_calendar.json`

```json
[
  {
    "datetime_utc": "2025-08-01T13:30:00Z",
    "event": "US NFP",
    "impact": "high"
  }
]
```

---

## PIPELINE STAGES

Your implementation must enforce these stages in code:

```text
INIT
 -> INPUTS_LOADED
 -> DATASET_EXTENDED_OR_VALIDATED
 -> FEATURES_COMPUTED
 -> PATTERNS_CLASSIFIED
 -> RISK_SCORES_COMPUTED
 -> INTERVENTIONS_GENERATED
 -> VALIDATION_COMPLETE
 -> RESULTS_FINALISED
```

Final intervention rankings must not be produced before deterministic feature computation and deterministic risk scoring have completed.

---

## MUST COMPLETE

### 1. Behavioural Feature Engineering

Compute behavioural features using deterministic code only.

Do not ask an LLM to compute these values.

For each user, compute:

- average stake
- stake escalation ratio after losses
- trades per minute
- percentage of trades within 5 minutes of high-impact news
- win rate
- revenge interval, defined as time between a losing trade and the next trade
- longest losing streak
- total trades
- total net profit or loss
- average session duration

Save one file per user:

```text
features/{user_id}.json
```

Each feature file must include enough source counts or supporting values to make the calculation auditable.

---

### 2. Pattern Detection

For each user, make one Stage 1 LLM call.

Each call must include:

- the user's computed feature vector
- the user's last 30 trades in compact format
- the controlled pattern vocabulary
- clear definitions for each pattern

Allowed pattern vocabulary:

```text
martingale
anti_martingale
revenge_trading
news_chasing
scalping
position_doubling
normal
insufficient_evidence
```

The LLM must classify the user using one or more labels from the vocabulary.

The output must include:

```json
{
  "user_id": "string",
  "patterns": ["martingale"],
  "evidence": [
    {
      "pattern": "martingale",
      "triggering_features": ["stake_escalation_ratio_after_losses", "longest_losing_streak"],
      "trade_ids": ["t_00001", "t_00002"],
      "explanation": "string"
    }
  ],
  "confidence": "low | medium | high"
}
```

Pattern outputs must be saved to `patterns.json`.

---

### 3. Deterministic Risk Scoring

Compute a risk score from 0 to 100 per user using deterministic code.

Do not ask an LLM to assign risk scores.

Risk weights must be explicitly defined in code and documented in `risk_model.md`.

The score should consider:

- detected patterns
- feature severity
- frequency of rapid repeat trading
- stake escalation after losses
- news-event trading concentration
- longest losing streak
- recent net loss

Save output to `risk_scores.json`.

Each record must include:

- `user_id`
- `risk_score`
- risk tier
- contributing factors
- formula version

Risk tiers:

```text
low
medium
high
critical
```

---

### 4. Intervention Plan

Make one Stage 2 LLM call using all user profiles, detected patterns, feature summaries, and deterministic risk scores.

The LLM must produce a tiered responsible-trading intervention plan.

Allowed intervention types:

```text
soft_nudge
deposit_limit_prompt
cooling_off_period
human_outreach
```

Each intervention must include:

```json
{
  "user_id": "string",
  "risk_tier": "low | medium | high | critical",
  "intervention_type": "string",
  "triggering_patterns": ["string"],
  "evidence_summary": "string",
  "recommended_action": "string"
}
```

Interventions must reference the specific user ID and the specific behavioural evidence that triggered the recommendation.

Save output to `interventions.json`.

---

## SHOULD ATTEMPT

### 5. False-Positive Audit

Select at least one user classified as `martingale`.

Verify in deterministic code that stake escalation follows losses in the underlying trade ledger.

Output:

```json
{
  "user_id": "string",
  "pattern": "martingale",
  "verified": true,
  "supporting_trade_sequence": ["trade_id"],
  "calculation": "string"
}
```

Save results to `false_positive_audit.json`.

If no user is classified as `martingale`, the audit must state that no eligible user was available.

For the public sample fixture, `u_001` should be detected and verified as a martingale-like stake escalation case.

---

### 6. Cohort-Level Insights

Generate cohort insights using computed data only.

Each insight must include:

- metric name
- cohort definition
- comparison group
- computed values
- conclusion

Examples:

```text
Users trading within 5 minutes of high-impact news had a higher loss rate than users who did not.
Users with high stake escalation after losses had shorter revenge intervals.
```

Do not allow the LLM to invent cohort statistics.

Save output to `cohort_insights.json`.

---

## STRETCH

### 7. Responsible-Trading Copy Generation

Generate user-facing message copy for each intervention type.

The copy must be:

- empathetic
- non-judgmental
- non-blaming
- concise
- free of financial promises
- free of shame-based language

Save messages under:

```text
messages/
```

---

### 8. Regulatory Mapping

Map each intervention type to relevant responsible-trading or customer-protection obligations.

For each mapping, include:

- regulator or framework
- obligation name
- short explanation
- intervention type supported
- citation or reference label

Save output to `regulatory_mapping.json`.

---

## REQUIRED ARTIFACTS

Your repository must produce:

- `trades.json`
- `economic_calendar.json`
- `features/`
- `patterns.json`
- `risk_scores.json`
- `risk_model.md`
- `interventions.json`
- `false_positive_audit.json`, if attempted
- `cohort_insights.json`, if attempted
- `messages/`, if attempted
- `regulatory_mapping.json`, if attempted
- `llm_calls.jsonl`

---

## `llm_calls.jsonl` REQUIREMENTS

Log one JSON object per LLM call.

Each record must include:

```json
{
  "stage": "string",
  "user_id": "string | null",
  "timestamp": "ISO-8601 timestamp",
  "provider": "string",
  "model": "string",
  "prompt_hash": "string",
  "input_artifacts": ["path"],
  "output_artifact": "path"
}
```

There must be separate records for:

- each per-user pattern classification call
- combined intervention planning call
- responsible-trading copy generation, if attempted
- regulatory mapping, if attempted

---

## VALIDATION REQUIREMENTS

The repository must include a validation command, for example:

```bash
make validate
```

or:

```bash
python validate.py
```

The validation command must check that:

- required artifacts exist
- JSON files are valid
- feature files exist for every user
- feature values are computed before pattern classification
- risk scores are computed deterministically and not produced by an LLM
- risk scores are reproducible across repeated runs
- interventions reference valid user IDs
- interventions reference triggering patterns and evidence
- LLM call logs contain one pattern-classification record per user
- final intervention ranking is not produced before risk scoring
- public sample `u_001`, when present, is flagged as martingale or position_doubling with evidence

---

## EXECUTION REQUIREMENTS

The evaluator will run the pipeline from a clean checkout.

Generated artifacts may be deleted before evaluation.

The evaluator may replace `trades.json` and `economic_calendar.json` with equivalent files using the same schema.

Static precomputed outputs are not sufficient.

The solution must actually run the staged pipeline and regenerate the required artifacts.

---

## TOOLS

Any programming language may be used.

Any LLM provider or AI tooling may be used.

---

## TECHNICAL CONSTRAINTS

- Feature engineering must be deterministic code.
- Risk scoring must be deterministic code.
- Pattern classification must use the controlled vocabulary.
- LLM pattern classifications must cite computed features and supporting trade IDs.
- Intervention copy must not shame, blame, or pressure users.
- Do not use real personal data.
- Do not infer protected characteristics or demographic attributes.
- Do not produce medical, legal, or financial advice for individual users.
- The public sample pattern for `u_001` must be detected when that fixture is present.