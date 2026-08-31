import pytest

from src import lead_constants as c


def test_no_entra_id_anywhere():
    haystacks = c.AUDITOR_MODULES + c.CE_MODULES + c.WEBINAR_TOPICS + c.WHITEPAPER_TOPICS
    assert not any("entra" in item.lower() for item in haystacks)


def test_no_ai_or_copilot_topics():
    banned = ("ai ", " ai", "copilot", "genai", "artificial intelligence")
    for topic in c.WEBINAR_TOPICS + c.WHITEPAPER_TOPICS:
        lowered = topic.lower()
        assert not any(b in lowered for b in banned), topic


def test_auditor_popular_modules_are_subset():
    assert set(c.AUDITOR_POPULAR) == {"Active Directory", "Windows Server", "Windows File Servers"}
    assert set(c.AUDITOR_POPULAR) <= set(c.AUDITOR_MODULES)
    assert set(c.AUDITOR_OTHER) == set(c.AUDITOR_MODULES) - set(c.AUDITOR_POPULAR)


def test_dc_modules_are_storage_subset_of_auditor():
    assert set(c.DC_MODULES) <= set(c.AUDITOR_MODULES)
    assert set(c.DC_POPULAR) == {"Windows File Servers", "SharePoint", "Azure Files"}
    assert set(c.DC_POPULAR) <= set(c.DC_MODULES)


def test_freeware_tools_count():
    assert len(c.FREEWARE_TOOLS) == 9
    assert len(set(c.FREEWARE_TOOLS)) == 9


def test_price_per_license_key_anchors():
    assert c.PRICE_PER_LICENSE_AUDITOR["Active Directory"] == 7.00
    assert c.PRICE_PER_LICENSE_AUDITOR["Windows File Servers"] == 5.60
    assert c.PRICE_PER_LICENSE_AUDITOR["SQL Server"] == 4.00
    assert c.PRICE_PER_LICENSE_AUDITOR["Exchange"] == 4.00
    assert all(4.00 <= v <= 7.00 for v in c.PRICE_PER_LICENSE_AUDITOR.values())
    assert set(c.PRICE_PER_LICENSE_AUDITOR.keys()) == set(c.AUDITOR_MODULES)


def test_data_classification_multiplier():
    assert c.DATA_CLASSIFICATION_MULTIPLIER == 1.5


def test_countries_by_region_covers_regions_no_us():
    assert set(c.COUNTRIES_BY_REGION.keys()) == set(c.REGIONS)
    for countries in c.COUNTRIES_BY_REGION.values():
        assert "United States" not in countries
        assert "US" not in countries


def test_country_conversion_anchors_match_kate_experience():
    assert c.COUNTRY_CONVERSION_ANCHORS["India"] < 0
    assert c.COUNTRY_CONVERSION_ANCHORS["Australia"] > 0
    for nordic in ("Sweden", "Norway", "Denmark", "Finland"):
        assert c.COUNTRY_CONVERSION_ANCHORS[nordic] < 0
    assert set(c.COUNTRY_CONVERSION_ANCHORS.keys()) <= {
        co for countries in c.COUNTRIES_BY_REGION.values() for co in countries
    }


def test_owner_id_pools():
    assert len(c.SDR_IDS) == 10
    assert len(c.RM_IDS) == 25
    assert len(set(c.SDR_IDS) & set(c.RM_IDS)) == 0


def test_classify_activity_tier_and_points():
    assert c.classify_activity_tier("Get a Demo: DataSec Auditor for Active Directory") == "hot"
    assert c.classify_activity_points("Get a Demo: DataSec Auditor for Active Directory") == c.ACTION_POINTS["hot"]

    ce_product = "DataSec Auditor for Active Directory: Free Community Edition"
    assert c.classify_activity_tier(f"Free Community Edition: {ce_product}") == "warm"
    assert c.classify_activity_points(f"Free Community Edition: {ce_product}") == c.ACTION_POINTS["warm"]

    assert c.classify_activity_tier(f"Webinar Attendance: {c.WEBINAR_TOPICS[0]}") == "cool"
    assert c.classify_activity_points(f"Webinar Attendance: {c.WEBINAR_TOPICS[0]}") == c.ACTION_POINTS["webinar_attendance"]

    assert c.classify_activity_tier(f"Webinar Registration: {c.WEBINAR_TOPICS[0]}") == "cool"
    assert c.classify_activity_points(f"Webinar Registration: {c.WEBINAR_TOPICS[0]}") == c.ACTION_POINTS["webinar_registration"]

    assert c.classify_activity_tier(c.FREEWARE_TOOLS[0]) == "cool"
    assert c.classify_activity_points(c.FREEWARE_TOOLS[0]) == c.ACTION_POINTS["freeware"]

    assert c.classify_activity_tier(c.WHITEPAPER_TOPICS[0]) == "cold"
    assert c.classify_activity_points(c.WHITEPAPER_TOPICS[0]) == c.ACTION_POINTS["cold"]


def test_classify_activity_rejects_unknown_string():
    with pytest.raises(ValueError):
        c.classify_activity_tier("Something Made Up")
    with pytest.raises(ValueError):
        c.classify_activity_points("Something Made Up")
