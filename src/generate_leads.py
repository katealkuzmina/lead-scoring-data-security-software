"""Synthetic data security software lead-scoring dataset generator.

See docs/superpowers/specs/2026-08-28-lead-scoring-design.md for the full
design rationale. Every function here is pure given an `rng`
(numpy.random.Generator), so the whole dataset is reproducible from a seed.
"""

import numpy as np

from src import lead_constants as c


def sample_geography(rng: np.random.Generator) -> dict:
    region = rng.choice(c.REGIONS, p=[0.50, 0.35, 0.15])
    country = rng.choice(c.COUNTRIES_BY_REGION[region])
    return {"region": region, "country": country}


def sample_company(rng: np.random.Generator) -> dict:
    industry = rng.choice(
        c.INDUSTRIES, p=[0.15, 0.12, 0.10, 0.10, 0.20, 0.13, 0.10, 0.10]
    )
    size = rng.choice(c.COMPANY_SIZE_BUCKETS, p=[0.35, 0.35, 0.20, 0.10])
    company_domain = f"company{rng.integers(100000, 999999)}.com"
    return {
        "industry": industry,
        "company_size_bucket": size,
        "company_domain": company_domain,
    }


def sample_pii(rng: np.random.Generator, domain: str) -> dict:
    first = rng.choice(c.FIRST_NAMES)
    last = rng.choice(c.LAST_NAMES)
    email = f"{first.lower()}.{last.lower()}@{domain}"
    return {"first_name": first, "last_name": last, "email": email}


def sample_job_title_seniority(rng: np.random.Generator) -> str:
    return rng.choice(c.JOB_LEVELS, p=[0.45, 0.30, 0.18, 0.07])


def sample_lead_source_channel(rng: np.random.Generator) -> str:
    return rng.choice(c.LEAD_SOURCE_CHANNELS, p=[0.35, 0.25, 0.15, 0.15, 0.10])


def sample_engagement(rng: np.random.Generator) -> dict:
    site_visits = int(rng.poisson(3)) + 1
    pages_viewed = int(site_visits * rng.uniform(1.5, 4))
    days_since_first_touch = int(rng.exponential(5))
    return {
        "site_visits_before_action": site_visits,
        "pages_viewed": pages_viewed,
        "days_since_first_touch": days_since_first_touch,
    }


def full_product_name(
    product_family: str, module: str | None = None, variant: str | None = None
) -> str:
    if product_family == "Auditor":
        if variant == "CE":
            if module:
                return f"DataSec Auditor for {module}: Free Community Edition"
            return "DataSec Auditor: Free Community Edition"
        if module:
            return f"DataSec Auditor for {module}"
        return "DataSec Auditor"
    if product_family == "Data Classification":
        if module:
            return f"DataSec Classification for {module}"
        return "DataSec Classification"
    if product_family == "Freeware Utility":
        assert module is not None
        return module
    raise ValueError(f"Unknown product_family: {product_family}")


def sample_module(rng: np.random.Generator, family: str) -> str:
    if family == "Auditor":
        return rng.choice(c.AUDITOR_POPULAR) if rng.random() < 0.5 else rng.choice(c.AUDITOR_OTHER)
    if family == "Data Classification":
        return rng.choice(c.DC_POPULAR) if rng.random() < 0.5 else rng.choice(c.DC_OTHER)
    raise ValueError(f"Unknown family: {family}")


def _build_activity(activity_value: str, product_family: str, product: str) -> dict:
    return {
        "activity_value": activity_value,
        "tier": c.classify_activity_tier(activity_value),
        "points": c.classify_activity_points(activity_value),
        "product_family": product_family,
        "product": product,
    }


def sample_activity(rng: np.random.Generator) -> dict:
    tier = rng.choice(["hot", "warm", "cool", "cold"], p=[0.18, 0.22, 0.30, 0.30])

    if tier == "hot":
        action = rng.choice(["Get a Demo", "Free Trial", "Request a Quote"])
        family = rng.choice(["Auditor", "Data Classification"], p=[0.7, 0.3])
        product = full_product_name(family, sample_module(rng, family))
        return _build_activity(f"{action}: {product}", family, product)

    if tier == "warm":
        family = rng.choice(["Auditor", "Data Classification"], p=[0.7, 0.3])
        module = sample_module(rng, family)
        if family == "Auditor" and rng.random() < 0.5:
            ce_module = module if module in c.CE_MODULES else rng.choice(c.CE_MODULES)
            product = full_product_name(family, ce_module, variant="CE")
            return _build_activity(f"Free Community Edition: {product}", family, product)
        product = full_product_name(family, module)
        return _build_activity(f"Launch In-Browser Demo: {product}", family, product)

    if tier == "cool":
        if rng.random() < 0.55:
            tool = rng.choice(c.FREEWARE_TOOLS)
            return _build_activity(tool, "Freeware Utility", tool)
        label = rng.choice(["Webinar Registration", "Webinar Attendance"], p=[0.6, 0.4])
        topic = rng.choice(c.WEBINAR_TOPICS)
        family = rng.choice(["Auditor", "Data Classification"], p=[0.8, 0.2])
        product = full_product_name(family)
        return _build_activity(f"{label}: {topic}", family, product)

    # cold
    topic = rng.choice(c.WHITEPAPER_TOPICS)
    family = rng.choice(["Auditor", "Data Classification"], p=[0.8, 0.2])
    product = full_product_name(family)
    return _build_activity(topic, family, product)


def generate_activity_sequence(
    rng: np.random.Generator, max_activities: int = c.MAX_ACTIVITIES
) -> tuple:
    """Sample activities for one contact until cumulative lead_score crosses
    VISIBILITY_THRESHOLD (materialized=True — the contact becomes a CRM Lead
    record), or the contact stops engaging first (materialized=False — never
    becomes a Lead record, per spec §3a).
    """
    activities = []
    score = 0
    while True:
        activity = sample_activity(rng)
        activities.append(activity)
        score += activity["points"]
        if score >= c.VISIBILITY_THRESHOLD:
            return activities, True
        if len(activities) >= max_activities:
            return activities, False
        if rng.random() >= c.CONTINUE_PROBABILITY:
            return activities, False


def sample_post_creation_activities(rng: np.random.Generator, funnel_stage: str) -> list:
    """Extra marketing engagement after the Lead record already exists — this
    is what makes lead_score_current (the live CRM field) diverge from
    lead_score_at_creation (the leakage-safe snapshot). Only stages where the
    lead is still actively being nurtured or worked get any."""
    active_stages = {"Nurturing", "Open (Opportunity)", "Working - In Progress (Contacted)"}
    if funnel_stage not in active_stages:
        return []
    n_extra = int(rng.poisson(0.6))
    return [sample_activity(rng) for _ in range(n_extra)]


def sample_lead_type(rng: np.random.Generator) -> tuple:
    """One real CRM field (end_user / msp / reseller). The SDR fills it from
    desk research before any call (~80% correct, ~20% missing/ambiguous),
    then corrects it during the qualification call if wrong. CRM only ever
    stores the current value — the two-value return here is a deliberate
    synthetic before/after snapshot for the leakage teaching point (spec §4),
    not two real CRM fields."""
    current = rng.choice(["end_user", "msp", "reseller"], p=[0.70, 0.15, 0.15])
    if rng.random() < 0.8:
        at_creation = current
    else:
        at_creation = np.nan
    return at_creation, current


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


def sample_country_modifiers(rng: np.random.Generator) -> dict:
    modifiers = dict(c.COUNTRY_CONVERSION_ANCHORS)
    for countries in c.COUNTRIES_BY_REGION.values():
        for country in countries:
            modifiers.setdefault(country, float(rng.normal(0, 0.15)))
    return modifiers


_SOURCE_LOGIT = {"organic": 0.1, "paid": 0.0, "referral": 0.5, "event": 0.3, "direct": 0.2}
_SIZE_LOGIT = {"1-50": -0.3, "51-200": 0.0, "201-1000": 0.3, "1000+": 0.5}
_SENIORITY_LOGIT = {
    "individual_contributor": -0.2, "manager": 0.1, "director": 0.3, "c_level": 0.4,
}
_LEAD_TYPE_LOGIT = {"end_user": 0.3, "msp": -0.1, "reseller": -0.2}


def compute_qualification_logit(row: dict, country_modifier: float) -> float:
    """Probability a lead survives qualification into an opportunity
    (target ~15-20% average — spec §4a)."""
    logit = -2.9
    logit += 0.03 * min(row["lead_score_at_creation"], 60)
    logit += 0.5 if row["industry"] in c.REGULATED_INDUSTRIES else 0.0
    logit += _SOURCE_LOGIT[row["lead_source_channel"]]
    logit += _SIZE_LOGIT[row["company_size_bucket"]]
    logit += _SENIORITY_LOGIT[row["job_title_seniority"]]
    logit += 0.1 * min(row["site_visits_before_action"], 10)
    logit += country_modifier
    return logit


def compute_win_logit(row: dict, country_modifier: float) -> float:
    """Probability a qualified opportunity closes won (target ~8-12%
    average, conditional on qualification — spec §4a)."""
    logit = -3.2
    logit += 0.02 * min(row["lead_score_at_creation"], 60)
    logit += _LEAD_TYPE_LOGIT[row["lead_type_current"]]
    logit += 0.5 if row["industry"] in c.REGULATED_INDUSTRIES else 0.0
    logit += country_modifier
    return logit


def sample_pre_opportunity_stage(rng: np.random.Generator) -> str:
    stages = [
        "New (Untouched)", "Working - No Contact",
        "Working - In Progress (Contacted)", "Nurturing", "Disqualified",
    ]
    weights = [0.20, 0.25, 0.25, 0.15, 0.15]
    return rng.choice(stages, p=weights)


def sample_post_qualification_non_won_stage(rng: np.random.Generator) -> str:
    stages = ["Open (Opportunity)", "Closed Lost"]
    weights = [0.45, 0.55]
    return rng.choice(stages, p=weights)


def sample_sdr_quality_offsets(rng: np.random.Generator) -> dict:
    return {sdr_id: float(rng.normal(0, 0.2)) for sdr_id in c.SDR_IDS}


def sample_license_count(rng: np.random.Generator, company_size_bucket: str) -> int:
    if rng.random() < 0.35:
        return c.MIN_LICENSES
    size_multiplier = {"1-50": 1.0, "51-200": 1.6, "201-1000": 3.0, "1000+": 6.0}[
        company_size_bucket
    ]
    extra_licenses = rng.lognormal(mean=1.0, sigma=1.0) * size_multiplier * 10
    return int(c.MIN_LICENSES + extra_licenses)


def sample_modules_in_deal(rng: np.random.Generator) -> int:
    return int(rng.choice([1, 2, 3], p=[0.70, 0.22, 0.08]))


def assign_owner(
    rng: np.random.Generator,
    lead_type_current: str,
    license_count: int,
    preferred_sdr_id: str | None = None,
) -> tuple:
    """§4b: MSP/reseller always goes to a regional manager; so does any
    end-user deal above the 150-license floor. RMs never qualify incoming
    leads — they only ever receive an opportunity that already exists, which
    is why this function is only called once a lead has converted."""
    if lead_type_current in ("msp", "reseller") or license_count > c.MIN_LICENSES:
        return rng.choice(c.RM_IDS), "regional_manager"
    if preferred_sdr_id is not None:
        return preferred_sdr_id, "sdr"
    return rng.choice(c.SDR_IDS), "sdr"


def resolve_module_from_product(product_family: str, product: str):
    if product_family == "Freeware Utility":
        return None
    for module in c.AUDITOR_MODULES:
        if f"for {module}" in product:
            return module
    return None


def price_per_license(product_family: str, module: str | None) -> float:
    base = c.PRICE_PER_LICENSE_AUDITOR.get(module, c.DEFAULT_PRICE_PER_LICENSE)
    if product_family == "Data Classification":
        return round(base * c.DATA_CLASSIFICATION_MULTIPLIER, 2)
    return base


def round_to_nearest(value: float, nearest: int = c.DEAL_ROUNDING) -> float:
    return round(value / nearest) * nearest


def _sample_extra_module(rng: np.random.Generator, family: str) -> str:
    return rng.choice(c.AUDITOR_MODULES) if family == "Auditor" else rng.choice(c.DC_MODULES)


def compute_deal_amount(
    rng: np.random.Generator,
    product_family: str,
    product: str,
    license_count: int,
    modules_in_deal: int,
) -> float:
    """deal_amount = round_to_nearest_50(0.85 × Σ license_count × price_per_license)
    — the 15% (RESELLER_MARGIN) is the channel/reseller cut the vendor's own
    recognized revenue never included, applied to every deal (spec §4c)."""
    module = resolve_module_from_product(product_family, product)
    total = price_per_license(product_family, module) * license_count
    for _ in range(modules_in_deal - 1):
        extra_family = rng.choice(["Auditor", "Data Classification"], p=[0.8, 0.2])
        extra_module = _sample_extra_module(rng, extra_family)
        total += price_per_license(extra_family, extra_module) * license_count
    net = total * (1 - c.RESELLER_MARGIN)
    return round_to_nearest(net, c.DEAL_ROUNDING)


def resolve_lead_type_at_close(rng: np.random.Generator, lead_type_current: str, is_won: bool) -> str:
    """MSP/reseller deals were almost never registered under the reseller's
    own name — payment usually came from the reseller's end client, and the
    deal was registered under that end client's name instead (spec §4b).
    Only applies at the point of winning; routing (assign_owner) already used
    the un-relabeled value, since ownership is decided before the outcome is
    known."""
    if is_won and lead_type_current == "reseller" and rng.random() < 0.90:
        return "end_user"
    return lead_type_current


def sample_payment_doc_attached(rng: np.random.Generator, owner_role: str) -> bool:
    threshold = 0.95 if owner_role == "regional_manager" else 0.5
    return bool(rng.random() < threshold)


def sample_call_attempts(rng: np.random.Generator, owner_role: str, converted_to_opportunity: bool) -> int:
    if owner_role == "regional_manager":
        return int(rng.random() < 0.1) * (int(rng.poisson(2)) + 1)
    base = int(rng.poisson(4)) + 1
    if converted_to_opportunity:
        base += int(rng.poisson(6))
    return base


from datetime import date, timedelta

import pandas as pd


def _sample_created_at(rng: np.random.Generator, start_date: date, n_days: int) -> date:
    # Lighter volume in the last two weeks of December (holiday lull) — resample
    # (with a hard cap so a pathological seed can't recurse forever).
    for _ in range(10):
        day_offset = int(rng.integers(0, n_days))
        candidate = start_date + timedelta(days=day_offset)
        if candidate.month == 12 and candidate.day > 18 and rng.random() < 0.6:
            continue
        return candidate
    return candidate


def _assign_activity_timestamps(
    rng: np.random.Generator, created_at: date, n_pre: int, n_post: int
) -> tuple:
    """Pre-creation activities land on or before `created_at` (the last one —
    whichever crossed the visibility threshold — lands exactly on it).
    Post-creation activities land on strictly increasing dates after it."""
    pre_offsets = sorted(int(rng.integers(1, 14)) for _ in range(max(n_pre - 1, 0)))
    pre_timestamps = [created_at - timedelta(days=d) for d in reversed(pre_offsets)]
    if n_pre > 0:
        pre_timestamps.append(created_at)

    post_timestamps = []
    running_offset = 0
    for _ in range(n_post):
        running_offset += int(rng.integers(3, 20))
        post_timestamps.append(created_at + timedelta(days=running_offset))

    return pre_timestamps, post_timestamps


def apply_field_completeness(rng: np.random.Generator, leads_df: pd.DataFrame) -> pd.DataFrame:
    """Real CRM leads were never fully filled in. Only registration-mandatory
    fields (first_name/last_name/email) and auto-populated ones (product/
    product_family/originating_activity) are guaranteed present — everything
    else has a chance of being blank, worse before an SDR has actually
    engaged the lead (spec §4). `lead_type_current` is a special case: it's
    only known once an SDR has actually spoken to the lead, so it's
    structurally missing (not a random data-entry gap) whenever that hasn't
    happened yet."""
    leads_df = leads_df.copy()
    untouched = leads_df["funnel_stage"].isin(c.UNTOUCHED_FUNNEL_STAGES)

    for column, base_rate in c.OPTIONAL_FIELD_MISSING_RATES.items():
        boosted_rate = min(base_rate * c.UNTOUCHED_MISSING_RATE_MULTIPLIER, c.UNTOUCHED_MISSING_RATE_CAP)
        rate = np.where(untouched, boosted_rate, base_rate)
        missing = rng.random(len(leads_df)) < rate
        leads_df.loc[missing, column] = np.nan

    leads_df.loc[untouched, "lead_type_current"] = np.nan

    return leads_df


def generate_leads(n: int = 15000, seed: int = 42, max_draws: int = 200000) -> tuple:
    rng = np.random.default_rng(seed)
    start_date = date(2020, 1, 1)
    n_days = 548  # ~18 months, inside Kate's 2019-2022 tenure

    sdr_quality = sample_sdr_quality_offsets(rng)
    country_modifiers = sample_country_modifiers(rng)

    lead_rows = []
    activity_rows = []
    lead_id = 0
    draws = 0

    while len(lead_rows) < n:
        draws += 1
        if draws > max_draws:
            raise RuntimeError(
                f"Gave up after {max_draws} draws with only {len(lead_rows)}/{n} "
                "leads materialized — CONTINUE_PROBABILITY or VISIBILITY_THRESHOLD "
                "likely need retuning."
            )

        activities, materialized = generate_activity_sequence(rng)
        if not materialized:
            continue

        lead_id += 1
        geography = sample_geography(rng)
        company = sample_company(rng)
        pii = sample_pii(rng, company["company_domain"])
        job = sample_job_title_seniority(rng)
        channel = sample_lead_source_channel(rng)
        engagement = sample_engagement(rng)
        created_at = _sample_created_at(rng, start_date, n_days)
        qualifying_sdr = rng.choice(c.SDR_IDS)

        lead_score_at_creation = sum(a["points"] for a in activities)
        originating = activities[-1]

        lead_type_at_creation, lead_type_current = sample_lead_type(rng)

        row = {
            "lead_id": lead_id,
            "created_at": created_at,
            **pii,
            **geography,
            "industry": company["industry"],
            "company_size_bucket": company["company_size_bucket"],
            "job_title_seniority": job,
            "lead_source_channel": channel,
            "originating_activity": originating["activity_value"],
            "product_family": originating["product_family"],
            "product": originating["product"],
            "lead_score_at_creation": lead_score_at_creation,
            "lead_type_at_creation": lead_type_at_creation,
            "lead_type_current": lead_type_current,
            **engagement,
        }

        country_modifier = country_modifiers[geography["country"]]
        qual_logit = (
            compute_qualification_logit(row, country_modifier)
            + sdr_quality[qualifying_sdr]
            + rng.normal(0, 0.3)
        )
        converted = bool(rng.random() < sigmoid(qual_logit))

        if not converted:
            funnel_stage = sample_pre_opportunity_stage(rng)
            is_won = False
        else:
            win_logit = compute_win_logit(row, country_modifier) + rng.normal(0, 0.3)
            is_won = bool(rng.random() < sigmoid(win_logit))
            funnel_stage = "Closed Won" if is_won else sample_post_qualification_non_won_stage(rng)

        row["converted_to_opportunity"] = int(converted)
        row["funnel_stage"] = funnel_stage
        row["closed_won"] = int(is_won)
        row["disqualified_reason"] = (
            rng.choice(c.DISQUALIFIED_REASONS) if funnel_stage == "Disqualified" else np.nan
        )

        post_activities = sample_post_creation_activities(rng, funnel_stage)
        row["lead_score_current"] = lead_score_at_creation + sum(a["points"] for a in post_activities)

        if converted:
            license_count = sample_license_count(rng, row["company_size_bucket"])
            modules_in_deal = sample_modules_in_deal(rng)
            owner_id, owner_role = assign_owner(
                rng, lead_type_current, license_count, preferred_sdr_id=qualifying_sdr
            )
        else:
            license_count = np.nan
            modules_in_deal = np.nan
            owner_id, owner_role = qualifying_sdr, "sdr"

        row["license_count"] = license_count
        row["modules_in_deal"] = modules_in_deal
        row["owner_id"] = owner_id
        row["owner_role"] = owner_role
        # Only relabel the exported column — assign_owner above already used
        # the un-relabeled lead_type_current, since routing happens before
        # the win/loss outcome is known.
        row["lead_type_current"] = resolve_lead_type_at_close(rng, lead_type_current, is_won)

        if is_won:
            row["deal_amount"] = compute_deal_amount(
                rng, row["product_family"], row["product"], license_count, modules_in_deal
            )
            row["payment_doc_attached"] = sample_payment_doc_attached(rng, owner_role)
        else:
            row["deal_amount"] = np.nan
            row["payment_doc_attached"] = np.nan

        row["sdr_call_attempts"] = sample_call_attempts(rng, owner_role, converted)

        lead_rows.append(row)

        all_activities = activities + post_activities
        pre_timestamps, post_timestamps = _assign_activity_timestamps(
            rng, created_at, len(activities), len(post_activities)
        )
        for activity, timestamp in zip(all_activities, pre_timestamps + post_timestamps):
            activity_rows.append({
                "lead_id": lead_id,
                "activity_timestamp": timestamp,
                "activity_value": activity["activity_value"],
                "points": activity["points"],
            })

    leads_df = pd.DataFrame(lead_rows)
    leads_df = apply_field_completeness(rng, leads_df)
    activities_df = pd.DataFrame(activity_rows)
    return leads_df, activities_df


if __name__ == "__main__":
    leads_df, activities_df = generate_leads(n=15000, seed=42)
    leads_df.to_csv("data/leads.csv", index=False)
    activities_df.to_csv("data/lead_activities.csv", index=False)
    print(f"Generated {len(leads_df)} leads -> data/leads.csv")
    print(f"Generated {len(activities_df)} activities -> data/lead_activities.csv")
    print(f"Qualification rate (lead -> opportunity): {leads_df['converted_to_opportunity'].mean():.2%}")
    print(f"Closed Won rate (of all leads): {leads_df['closed_won'].mean():.2%}")
