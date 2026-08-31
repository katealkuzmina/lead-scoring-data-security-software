# Lead Scoring — Data Security Software (synthetic data)

Predicting which inbound leads convert to **Closed Won**, using a synthetic
dataset built to resemble a real data security software vendor's auditing
and data classification product lead funnel. Grounded in 4 years (2019-2022)
of my SDR experience in a data security software vendor's APAC region — the
funnel logic, module popularity, pricing anchors, and CRM field names in the
generator are based on that real experience.

## Problem

The SDR team receives inbound leads from six kinds of site actions
(demo requests, free trials, quote requests, in-browser demos, Free Community
Edition/freeware downloads, webinar/white paper engagement). Not all leads
are worth equal SDR attention. This project scores a lead **the moment it
enters an SDR's visibility zone** — i.e. the moment its accumulated
`lead_score` first crosses the CRM's visibility threshold, before any SDR has
touched it — with the probability it eventually closes as a paid deal, so
SDRs can prioritize their queue.

## Data

Two tables, included in `data/`:

- `data/leads.csv` — 15,000 synthetic **materialized leads** — a contact
  only shows up here once its accumulated `lead_score` (a real CRM field:
  points per activity) crosses a visibility threshold, mirroring how a single
  freeware download alone never surfaced to an SDR in practice.
- `data/lead_activities.csv` — 22,818 individual activities behind those
  leads (demo requests, downloads, webinar touches), many-to-one with
  `leads.csv`.

## Methodology

1. **EDA** — first step: drop the (synthetic) PII columns, since real CRM
   exports always need that. Base rates: lead-level `closed_won` is 2.37%,
   lead→opportunity qualification rate is 20.8%, and win rate *among*
   opportunities is 11.4% — three very different numbers for a reason (see
   notebook Step 2). Funnel shape, score distribution, and the
   country-conversion pattern (Australia up, India/Nordics down) are checked
   against real SDR experience here, before any modeling decision is made.
2. **Missing values** — real CRM exports are never fully filled in, and this
   dataset reproduces that. Rather than blanket-imputing everything, each
   gap column is tested for whether the *fact* of being missing correlates
   with `closed_won` (a chi-square test per column, with a Bonferroni check
   for multiple comparisons). Two columns (`job_title_seniority`,
   `company_size_bucket`) come back statistically significant and get an
   explicit `_is_missing` flag feature in addition to being imputed; the
   rest are imputed straight to `"Unknown"`.
3. **Feature engineering** — every column in both tables is sorted into one
   of four buckets: feature (known the moment the lead enters the SDR's
   visibility zone), leakage (only known after the lead is already being
   worked — `lead_type_current`, `lead_score_current`, `funnel_stage`,
   `deal_amount`, etc.), fairness/attribution problem (`owner_id`/
   `owner_role` — would reward rep assignment, not lead quality), or PII.
   Engineered activity-tier counts (`num_hot_actions`, etc.) are filtered to
   `activity_timestamp <= created_at` for the same reason — and that cutoff
   is **verified empirically in the notebook**, not just assumed: summing
   the points of every activity at or before that boundary reconstructs
   `lead_score_at_creation` exactly, for all 15,000 leads. See the notebook
   for the full bucket list and reasoning.
4. **Modeling** — Logistic Regression (`class_weight="balanced"`) vs
   XGBoost (`scale_pos_weight`), compared on Precision/Recall and PR-AUC
   (chosen over ROC-AUC because Closed Won is a small minority class — the
   lead-level base rate is only ~2.4%). A naive 0.5 threshold is shown to be
   unusable for either model at this base rate; each model's own F1-optimal
   threshold is used instead.
5. **Feature importance** — LR coefficients and XGBoost's
   `feature_importances_`, read against real SDR intuition about which leads
   were actually worth chasing.
6. **Business economics** — deal value comes from the dataset's own
   `deal_amount` field (derived from real license-count pricing, not a flat
   assumption); the cost side has three separate lines instead of one blended
   number — a marketing-only Cost Per Lead, a separate SDR qualification
   cost, and RM overhead attributed only to RM-owned opportunities — since
   SDRs, marketing, and RMs don't do the same job. Salaries are labeled
   *averages*, not real figures (compensation wasn't shared between
   colleagues at the company).

## Results

- **PR-AUC:** Logistic Regression 0.066±0.010 (range 0.059–0.083), XGBoost
  0.055±0.010 (range 0.048–0.072) — both averaged across 5 different
  train/test splits, not a single split (a single-split reading, e.g. the
  original `random_state=42`, can show LR as high as 0.083 — the best of 5,
  not typical). Both are well above the ~0.024 base-rate floor, on a
  genuinely hard, noisy target. **Logistic Regression outperforms XGBoost
  on PR-AUC in 4 of 5 splits** — not "every metric," a claim an earlier
  version of this README made from a single split; on `seed=2024` XGBoost
  actually wins (0.072 vs. 0.063). Most likely cause either way: only
  ~356 `closed_won` leads in the whole dataset, too few positives for 200
  boosted trees to learn a stable pattern from without overfitting. LR is
  carried forward as the primary model (Step 5 onward); XGBoost is kept as
  the comparison.
- **Thresholds:** the F1-optimal threshold is selected honestly — on a
  held-out 25% slice of the *training* set, never on `y_test` — then scored
  once on the untouched test set; a 5-split robustness check (different
  train-internal splits, same fixed test set) shows how much that headline
  number actually moves. LR: precision 10.0%±2.3% / recall 24.5%±9.2%
  averaged over 5 splits; XGBoost: precision 8.0%±2.6% / recall 14.9%±7.9%.
  LR's precision is a **~4.2x lift** over the 2.37% base rate. (An earlier
  version of this notebook selected the threshold directly on the test set
  it then reported metrics on — a leakage bug that inflated recall
  specifically, from the true ~24.5% up to a reported 32.4%; see the
  notebook's Step 4 for the full before/after.) A naive 0.5 threshold is
  shown to be unusable for either model at this base rate (LR floods the
  queue at 5% precision; XGBoost misses most of the real wins).
- **Top features:** `lead_score_at_creation` (the real CRM rating field) is
  LR's single strongest coefficient (1.27), matching how SDRs actually
  triaged their queue day to day. Country/industry effects come through
  cleanly and in the expected direction — `country=Australia`/`Chile`
  positive, `country=Finland`/`Sweden`/`India` negative,
  `industry=Healthcare`/`Finance` positive — recovering the real
  India/Nordics-down, Australia-up pattern from my SDR experience
  without being told about it directly. XGBoost tells a different story:
  its top feature is `region=EMEA`, with `lead_score_at_creation` only 4th
  and importance spread thin across many region/industry dummies — trees
  are far more robust to the multicollinearity between `lead_score_at_creation`
  and the engineered activity-tier counts than the linear model is. See the
  notebook's "Reading the importances" section for the full discussion,
  including why `num_hot_actions`/`total_actions` carry *negative* LR
  coefficients despite more engagement being a good sign (multicollinearity
  with `lead_score_at_creation`, not a real inverse relationship).
- **Business impact:** working just the **top 20%** of leads by LR score
  captures **49.3%±4.2%** of total Closed Won deal value on average across
  5 splits (range 45.4–56.1% — the 56.1% figure, on ~33.3% of the working
  cost, USD 189,777 vs. USD 569,941, is the single-split reading and the
  best of 5, not typical). The honest headline is "roughly half the deal
  value from a fifth of the effort," not "over half."

## How to run

`data/leads.csv` and `data/lead_activities.csv` are included in the repo, so
no data generation step is needed to open and run the notebook. The full
project — generator, tests, notebook — is included, managed with
[uv](https://docs.astral.sh/uv/).

```bash
uv sync                                    # installs everything from pyproject.toml/uv.lock
uv run pytest                              # 85 tests for the data generator
uv run python -m src.generate_leads        # optional: regenerate data/*.csv from scratch (same seed=42)
uv run jupyter notebook lead_scoring_model.ipynb
```

## Limitations

- All data is synthetic; conversion probabilities and pricing are calibrated
  to be *plausible*, not fit to any real historical rate. The
  qualification-rate and win-rate intercepts in `src/generate_leads.py` are
  hand-tuned to land in a plausible range, not derived from real vendor
  numbers.
- The funnel-stage progression is generated independently per lead (with a
  time-ordered activity sequence feeding it), not simulated as a fully
  time-ordered CRM event stream.
- Business-economics cost assumptions are explicitly fictional, and salaries
  are labeled averages rather than real per-role figures (see Methodology).
- Real BANT (Budget/Authority/Need/Timeline) qualification notes existed in
  the real CRM as SDR free text, not structured fields — not modeled here.
- `num_hot_actions`/`total_actions` are mechanically derived from the same
  activities that build `lead_score_at_creation`, so their standalone
  coefficients in the linear model are not reliably interpretable on their
  own (see Results above).
- The positive class is thin — only 71 `closed_won` leads land in the test
  set — so every metric above (PR-AUC, the F1-optimal thresholds, the gains
  table) rests on a small sample and would sharpen with more history.
- Recall stays modest and noisy even at the best threshold (24.5%±9.2% for
  LR across 5 train-internal splits) — this model is a triage/prioritization
  tool, not a filter that reliably catches every eventual winner.
