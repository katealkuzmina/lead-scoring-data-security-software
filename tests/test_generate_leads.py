import numpy as np
import pytest

from src import lead_constants as c
from src.generate_leads import (
    sample_geography,
    sample_company,
    sample_pii,
    sample_job_title_seniority,
    sample_lead_source_channel,
    sample_engagement,
)


@pytest.fixture
def rng():
    return np.random.default_rng(0)


def test_sample_geography_region_and_country_consistent(rng):
    for _ in range(200):
        geo = sample_geography(rng)
        assert geo["region"] in c.REGIONS
        assert "US" not in geo["region"]
        assert geo["country"] in c.COUNTRIES_BY_REGION[geo["region"]]


def test_sample_company_fields(rng):
    company = sample_company(rng)
    assert company["industry"] in c.INDUSTRIES
    assert company["company_size_bucket"] in c.COMPANY_SIZE_BUCKETS
    assert company["company_domain"].endswith(".com")


def test_sample_pii_matches_domain(rng):
    pii = sample_pii(rng, "acme123.com")
    assert pii["first_name"] in c.FIRST_NAMES
    assert pii["last_name"] in c.LAST_NAMES
    assert pii["email"].endswith("@acme123.com")
    assert pii["first_name"].lower() in pii["email"]


def test_sample_job_title_seniority_valid(rng):
    for _ in range(50):
        assert sample_job_title_seniority(rng) in c.JOB_LEVELS


def test_sample_lead_source_channel_valid(rng):
    for _ in range(50):
        assert sample_lead_source_channel(rng) in c.LEAD_SOURCE_CHANNELS


def test_sample_engagement_non_negative(rng):
    for _ in range(50):
        eng = sample_engagement(rng)
        assert eng["site_visits_before_action"] >= 1
        assert eng["pages_viewed"] >= 1
        assert eng["days_since_first_touch"] >= 0


from src.generate_leads import (
    full_product_name,
    sample_module,
    sample_activity,
    generate_activity_sequence,
    sample_post_creation_activities,
)


def test_full_product_name_auditor_module():
    assert full_product_name("Auditor", "Active Directory") == "DataSec Auditor for Active Directory"


def test_full_product_name_auditor_ce():
    assert full_product_name("Auditor", "Active Directory", variant="CE") == (
        "DataSec Auditor for Active Directory: Free Community Edition"
    )
    assert full_product_name("Auditor", variant="CE") == "DataSec Auditor: Free Community Edition"


def test_full_product_name_data_classification():
    assert full_product_name("Data Classification", "SharePoint") == (
        "DataSec Classification for SharePoint"
    )
    assert full_product_name("Data Classification") == "DataSec Classification"


def test_full_product_name_freeware():
    assert full_product_name("Freeware Utility", "DataSec Event Log Manager") == "DataSec Event Log Manager"


def test_sample_module_auditor_only_returns_auditor_modules(rng):
    for _ in range(100):
        assert sample_module(rng, "Auditor") in c.AUDITOR_MODULES


def test_sample_module_dc_only_returns_dc_modules(rng):
    for _ in range(100):
        assert sample_module(rng, "Data Classification") in c.DC_MODULES


def test_sample_activity_valid_and_points_match_classifier(rng):
    valid_families = {"Auditor", "Data Classification", "Freeware Utility"}
    for _ in range(300):
        activity = sample_activity(rng)
        assert activity["tier"] in {"hot", "warm", "cool", "cold"}
        assert activity["product_family"] in valid_families
        assert activity["product"]
        assert activity["points"] == c.classify_activity_points(activity["activity_value"])
        assert activity["tier"] == c.classify_activity_tier(activity["activity_value"])


def test_sample_activity_freeware_is_always_cool_and_8_points(rng):
    seen = False
    for _ in range(300):
        activity = sample_activity(rng)
        if activity["product_family"] == "Freeware Utility":
            seen = True
            assert activity["tier"] == "cool"
            assert activity["points"] == c.ACTION_POINTS["freeware"]
            assert activity["product"] in c.FREEWARE_TOOLS
            assert activity["activity_value"] == activity["product"]
    assert seen


def test_sample_activity_no_entra_id(rng):
    for _ in range(500):
        activity = sample_activity(rng)
        assert "entra" not in activity["activity_value"].lower()


def test_generate_activity_sequence_score_matches_threshold_crossing():
    rng = np.random.default_rng(3)
    for _ in range(500):
        activities, materialized = generate_activity_sequence(rng)
        score = sum(a["points"] for a in activities)
        if materialized:
            assert score >= c.VISIBILITY_THRESHOLD
        else:
            assert score < c.VISIBILITY_THRESHOLD


def test_generate_activity_sequence_produces_both_outcomes():
    rng = np.random.default_rng(2)
    materialized_count, excluded_count = 0, 0
    for _ in range(2000):
        _, materialized = generate_activity_sequence(rng)
        if materialized:
            materialized_count += 1
        else:
            excluded_count += 1
    assert materialized_count > 0
    assert excluded_count > 0


def test_generate_activity_sequence_single_freeware_never_materializes():
    # Statistical check: every non-materialized single-activity sequence must
    # be below threshold — this is the "freeware alone is not a workable
    # lead" rule, now a special case of the general score mechanic.
    rng = np.random.default_rng(4)
    single_action_seen = False
    for _ in range(3000):
        activities, materialized = generate_activity_sequence(rng)
        if len(activities) == 1 and not materialized:
            single_action_seen = True
            assert sum(a["points"] for a in activities) < c.VISIBILITY_THRESHOLD
    assert single_action_seen


def test_sample_post_creation_activities_none_for_terminal_stages(rng):
    for stage in ("Closed Won", "Closed Lost", "Disqualified", "New (Untouched)", "Working - No Contact"):
        assert sample_post_creation_activities(rng, stage) == []


def test_sample_post_creation_activities_possible_for_nurturing():
    rng = np.random.default_rng(5)
    counts = [len(sample_post_creation_activities(rng, "Nurturing")) for _ in range(500)]
    assert any(n > 0 for n in counts)


from src.generate_leads import sample_lead_type


def test_sample_lead_type_current_valid(rng):
    for _ in range(200):
        _, current = sample_lead_type(rng)
        assert current in {"end_user", "msp", "reseller"}


def test_sample_lead_type_at_creation_mostly_matches_current():
    rng = np.random.default_rng(123)
    total, matches, missing = 0, 0, 0
    for _ in range(5000):
        at_creation, current = sample_lead_type(rng)
        total += 1
        if isinstance(at_creation, float) and np.isnan(at_creation):
            missing += 1
        elif at_creation == current:
            matches += 1
    assert 0.15 < missing / total < 0.25
    assert 0.75 < matches / total < 0.85


from src.generate_leads import (
    sigmoid,
    sample_country_modifiers,
    compute_qualification_logit,
    compute_win_logit,
    sample_pre_opportunity_stage,
    sample_post_qualification_non_won_stage,
)

BASE_ROW = {
    "lead_score_at_creation": 10,
    "industry": "Other",
    "lead_source_channel": "paid",
    "company_size_bucket": "1-50",
    "job_title_seniority": "individual_contributor",
    "site_visits_before_action": 1,
    "lead_type_current": "reseller",
}


def test_sigmoid_bounds():
    assert sigmoid(-100) == pytest.approx(0.0, abs=1e-6)
    assert sigmoid(100) == pytest.approx(1.0, abs=1e-6)
    assert sigmoid(0) == pytest.approx(0.5)


def test_sample_country_modifiers_covers_all_countries(rng):
    modifiers = sample_country_modifiers(rng)
    all_countries = {co for countries in c.COUNTRIES_BY_REGION.values() for co in countries}
    assert all_countries <= set(modifiers.keys())


def test_sample_country_modifiers_matches_anchors(rng):
    modifiers = sample_country_modifiers(rng)
    assert modifiers["India"] == c.COUNTRY_CONVERSION_ANCHORS["India"]
    assert modifiers["Australia"] == c.COUNTRY_CONVERSION_ANCHORS["Australia"]
    assert modifiers["India"] < modifiers["Australia"]


def test_higher_lead_score_scores_higher_qualification_logit():
    low = compute_qualification_logit(BASE_ROW, country_modifier=0.0)
    high_row = {**BASE_ROW, "lead_score_at_creation": 50}
    high = compute_qualification_logit(high_row, country_modifier=0.0)
    assert high > low


def test_regulated_industry_scores_higher_qualification_logit():
    base = compute_qualification_logit(BASE_ROW, country_modifier=0.0)
    regulated_row = {**BASE_ROW, "industry": "Finance"}
    assert compute_qualification_logit(regulated_row, country_modifier=0.0) > base


def test_country_modifier_shifts_qualification_logit():
    base = compute_qualification_logit(BASE_ROW, country_modifier=0.0)
    boosted = compute_qualification_logit(BASE_ROW, country_modifier=0.6)
    assert boosted > base


def test_end_user_scores_higher_win_logit_than_reseller():
    reseller = compute_win_logit(BASE_ROW, country_modifier=0.0)
    end_user_row = {**BASE_ROW, "lead_type_current": "end_user"}
    assert compute_win_logit(end_user_row, country_modifier=0.0) > reseller


def test_sample_pre_opportunity_stage_valid(rng):
    valid = {
        "New (Untouched)", "Working - No Contact",
        "Working - In Progress (Contacted)", "Nurturing", "Disqualified",
    }
    for _ in range(200):
        assert sample_pre_opportunity_stage(rng) in valid


def test_sample_post_qualification_non_won_stage_valid(rng):
    valid = {"Open (Opportunity)", "Closed Lost"}
    for _ in range(200):
        assert sample_post_qualification_non_won_stage(rng) in valid


from src.generate_leads import (
    sample_sdr_quality_offsets,
    sample_license_count,
    sample_modules_in_deal,
    assign_owner,
    resolve_module_from_product,
    price_per_license,
    round_to_nearest,
    compute_deal_amount,
    resolve_lead_type_at_close,
    sample_payment_doc_attached,
    sample_call_attempts,
)


def test_sample_sdr_quality_offsets_covers_all_sdrs(rng):
    offsets = sample_sdr_quality_offsets(rng)
    assert set(offsets.keys()) == set(c.SDR_IDS)
    assert all(isinstance(v, float) for v in offsets.values())


def test_sample_license_count_floor(rng):
    for size in c.COMPANY_SIZE_BUCKETS:
        for _ in range(100):
            assert sample_license_count(rng, size) >= c.MIN_LICENSES


def test_sample_license_count_some_at_floor():
    rng = np.random.default_rng(7)
    counts = [sample_license_count(rng, "1-50") for _ in range(2000)]
    at_floor = sum(1 for n in counts if n == c.MIN_LICENSES)
    assert at_floor / len(counts) > 0.2


def test_sample_modules_in_deal_valid(rng):
    for _ in range(200):
        assert sample_modules_in_deal(rng) in {1, 2, 3}


def test_assign_owner_msp_always_regional_manager(rng):
    for _ in range(100):
        owner_id, role = assign_owner(rng, "msp", c.MIN_LICENSES)
        assert role == "regional_manager"
        assert owner_id in c.RM_IDS


def test_assign_owner_end_user_at_floor_is_sdr(rng):
    for _ in range(100):
        owner_id, role = assign_owner(rng, "end_user", c.MIN_LICENSES)
        assert role == "sdr"
        assert owner_id in c.SDR_IDS


def test_assign_owner_reuses_preferred_sdr_when_staying_with_sdr(rng):
    for _ in range(20):
        owner_id, role = assign_owner(rng, "end_user", c.MIN_LICENSES, preferred_sdr_id="SDR_07")
        assert role == "sdr"
        assert owner_id == "SDR_07"


def test_assign_owner_ignores_preferred_sdr_when_escalated(rng):
    for _ in range(20):
        owner_id, role = assign_owner(rng, "msp", c.MIN_LICENSES, preferred_sdr_id="SDR_07")
        assert role == "regional_manager"
        assert owner_id in c.RM_IDS


def test_assign_owner_end_user_above_floor_is_regional_manager(rng):
    for _ in range(100):
        owner_id, role = assign_owner(rng, "end_user", c.MIN_LICENSES + 1)
        assert role == "regional_manager"
        assert owner_id in c.RM_IDS


def test_resolve_module_from_product():
    assert resolve_module_from_product("Auditor", "DataSec Auditor for Active Directory") == "Active Directory"
    assert resolve_module_from_product("Freeware Utility", "DataSec Event Log Manager") is None
    assert resolve_module_from_product("Auditor", "DataSec Auditor") is None


def test_price_per_license_auditor_uses_table_directly():
    assert price_per_license("Auditor", "Active Directory") == 7.00
    assert price_per_license("Auditor", "Windows File Servers") == 5.60


def test_price_per_license_data_classification_applies_multiplier():
    assert price_per_license("Data Classification", "SharePoint") == pytest.approx(
        c.PRICE_PER_LICENSE_AUDITOR["SharePoint"] * c.DATA_CLASSIFICATION_MULTIPLIER
    )


def test_price_per_license_unknown_module_falls_back_to_default():
    assert price_per_license("Auditor", None) == c.DEFAULT_PRICE_PER_LICENSE


def test_round_to_nearest():
    assert round_to_nearest(714, 50) == 700
    assert round_to_nearest(724, 50) == 700
    assert round_to_nearest(726, 50) == 750


def test_compute_deal_amount_matches_file_server_anchor(rng):
    amount = compute_deal_amount(
        rng, "Auditor", "DataSec Auditor for Windows File Servers", c.MIN_LICENSES, 1
    )
    assert amount == pytest.approx(700, abs=1)


def test_compute_deal_amount_scales_with_modules(rng):
    one_module = compute_deal_amount(
        rng, "Auditor", "DataSec Auditor for Active Directory", c.MIN_LICENSES, 1
    )
    two_modules = compute_deal_amount(
        rng, "Auditor", "DataSec Auditor for Active Directory", c.MIN_LICENSES, 2
    )
    assert two_modules > one_module


def test_resolve_lead_type_at_close_relabels_reseller_wins_mostly():
    rng = np.random.default_rng(11)
    outcomes = [resolve_lead_type_at_close(rng, "reseller", True) for _ in range(2000)]
    assert np.mean([o == "end_user" for o in outcomes]) > 0.8


def test_resolve_lead_type_at_close_leaves_non_wins_alone(rng):
    for _ in range(50):
        assert resolve_lead_type_at_close(rng, "reseller", False) == "reseller"


def test_resolve_lead_type_at_close_leaves_end_user_alone(rng):
    for _ in range(50):
        assert resolve_lead_type_at_close(rng, "end_user", True) == "end_user"


def test_sample_payment_doc_attached_more_likely_for_rm():
    rng = np.random.default_rng(3)
    rm_rate = np.mean([sample_payment_doc_attached(rng, "regional_manager") for _ in range(2000)])
    sdr_rate = np.mean([sample_payment_doc_attached(rng, "sdr") for _ in range(2000)])
    assert rm_rate > sdr_rate


def test_sample_call_attempts_rm_mostly_zero():
    rng = np.random.default_rng(5)
    attempts = [sample_call_attempts(rng, "regional_manager", True) for _ in range(500)]
    assert np.mean([a == 0 for a in attempts]) > 0.7


def test_sample_call_attempts_sdr_rises_after_conversion():
    rng = np.random.default_rng(9)
    pre = np.mean([sample_call_attempts(rng, "sdr", False) for _ in range(500)])
    post = np.mean([sample_call_attempts(rng, "sdr", True) for _ in range(500)])
    assert post > pre


import pandas as pd

from src.generate_leads import generate_leads


@pytest.fixture(scope="module")
def leads_and_activities():
    return generate_leads(n=1500, seed=42)


def test_generate_leads_shape_and_reproducibility():
    leads1, activities1 = generate_leads(n=300, seed=1)
    leads2, activities2 = generate_leads(n=300, seed=1)
    pd.testing.assert_frame_equal(leads1, leads2)
    pd.testing.assert_frame_equal(activities1, activities2)
    assert len(leads1) == 300


def test_generate_leads_no_entra_id(leads_and_activities):
    leads_df, activities_df = leads_and_activities
    assert not leads_df["product"].str.contains("Entra", case=False).any()
    assert not activities_df["activity_value"].str.contains("Entra", case=False).any()


def test_generate_leads_license_floor(leads_and_activities):
    leads_df, _ = leads_and_activities
    licensed = leads_df["license_count"].dropna()
    assert (licensed >= c.MIN_LICENSES).all()


def test_generate_leads_deal_amount_only_when_won(leads_and_activities):
    leads_df, _ = leads_and_activities
    won = leads_df["closed_won"] == 1
    assert leads_df.loc[won, "deal_amount"].notna().all()
    assert leads_df.loc[~won, "deal_amount"].isna().all()


def test_generate_leads_deal_amount_range(leads_and_activities):
    leads_df, _ = leads_and_activities
    amounts = leads_df["deal_amount"].dropna()
    if len(amounts) > 0:
        assert amounts.min() >= 300
        assert amounts.max() < 2_000_000  # generous ceiling, not a hard spec bound


def test_generate_leads_reseller_rarely_wins(leads_and_activities):
    leads_df, _ = leads_and_activities
    won = leads_df[leads_df["closed_won"] == 1]
    if len(won) > 0:
        reseller_share = (won["lead_type_current"] == "reseller").mean()
        assert reseller_share < 0.10


def test_generate_leads_msp_reseller_always_regional_manager(leads_and_activities):
    leads_df, _ = leads_and_activities
    converted = leads_df[leads_df["converted_to_opportunity"] == 1]
    # Restrict to non-won rows: owner_role was assigned from the pre-relabel
    # lead_type_current, and only WON reseller rows get relabeled to
    # end_user afterwards — checking non-won rows isolates the routing rule
    # cleanly from that later relabeling.
    not_won = converted[converted["closed_won"] == 0]
    partner_rows = not_won[not_won["lead_type_current"].isin(["msp", "reseller"])]
    assert (partner_rows["owner_role"] == "regional_manager").all()


def test_generate_leads_lead_level_closed_won_rate_reasonable(leads_and_activities):
    leads_df, _ = leads_and_activities
    rate = leads_df["closed_won"].mean()
    assert 0.005 < rate < 0.06


def test_generate_leads_qualification_rate_reasonable(leads_and_activities):
    leads_df, _ = leads_and_activities
    rate = leads_df["converted_to_opportunity"].mean()
    assert 0.08 < rate < 0.30


def test_generate_leads_pii_columns_present(leads_and_activities):
    leads_df, _ = leads_and_activities
    for col in ("first_name", "last_name", "email"):
        assert col in leads_df.columns
        assert leads_df[col].notna().all()


def test_generate_leads_no_us_region(leads_and_activities):
    leads_df, _ = leads_and_activities
    assert "US" not in leads_df["region"].unique()
    assert set(leads_df["region"].dropna().unique()) <= set(c.REGIONS)


def test_generate_leads_lead_score_at_creation_meets_threshold(leads_and_activities):
    leads_df, _ = leads_and_activities
    assert (leads_df["lead_score_at_creation"] >= c.VISIBILITY_THRESHOLD).all()


def test_generate_leads_lead_score_current_never_less_than_at_creation(leads_and_activities):
    leads_df, _ = leads_and_activities
    assert (leads_df["lead_score_current"] >= leads_df["lead_score_at_creation"]).all()


def test_generate_leads_activities_link_to_leads(leads_and_activities):
    leads_df, activities_df = leads_and_activities
    assert set(activities_df["lead_id"]) <= set(leads_df["lead_id"])


def test_generate_leads_activities_points_sum_to_lead_score_current(leads_and_activities):
    leads_df, activities_df = leads_and_activities
    totals = activities_df.groupby("lead_id")["points"].sum()
    expected = leads_df.set_index("lead_id")["lead_score_current"]
    pd.testing.assert_series_equal(
        totals.reindex(expected.index), expected, check_names=False, check_dtype=False,
    )


def test_generate_leads_mandatory_columns_never_missing(leads_and_activities):
    leads_df, _ = leads_and_activities
    for col in ("first_name", "last_name", "email", "product_family", "product", "originating_activity"):
        assert leads_df[col].notna().all()


def test_generate_leads_optional_columns_have_some_missing(leads_and_activities):
    leads_df, _ = leads_and_activities
    for col in c.OPTIONAL_FIELD_MISSING_RATES:
        assert leads_df[col].isna().mean() > 0.01


def test_generate_leads_untouched_leads_have_more_missing_optional_fields():
    leads_df, _ = generate_leads(n=6000, seed=7)
    untouched = leads_df["funnel_stage"].isin(c.UNTOUCHED_FUNNEL_STAGES)
    for col in c.OPTIONAL_FIELD_MISSING_RATES:
        untouched_rate = leads_df.loc[untouched, col].isna().mean()
        touched_rate = leads_df.loc[~untouched, col].isna().mean()
        assert untouched_rate > touched_rate


def test_generate_leads_lead_type_current_missing_only_for_untouched(leads_and_activities):
    leads_df, _ = leads_and_activities
    untouched = leads_df["funnel_stage"].isin(c.UNTOUCHED_FUNNEL_STAGES)
    assert leads_df.loc[untouched, "lead_type_current"].isna().all()
    assert leads_df.loc[~untouched, "lead_type_current"].notna().all()


def test_generate_leads_india_converts_no_better_than_australia():
    # Statistical property over a larger draw, since country is randomly
    # assigned per lead.
    leads_df, _ = generate_leads(n=6000, seed=99)
    india = leads_df[leads_df["country"] == "India"]
    australia = leads_df[leads_df["country"] == "Australia"]
    if len(india) > 20 and len(australia) > 20:
        assert india["closed_won"].mean() <= australia["closed_won"].mean()
