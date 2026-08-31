"""Reference data for the synthetic data security software lead-scoring
dataset.

All names/topics are period-styled after real vendor offerings; "Microsoft
Entra ID" and any AI/Copilot topic are deliberately excluded — they postdate
Kate's 2019-2022 tenure. See docs/ (kept local-only, not part of the
published repo) for every anchor point's real-world grounding.
"""

AUDITOR_MODULES = [
    "Active Directory", "Microsoft 365", "Exchange", "SharePoint",
    "Nutanix Files", "Windows File Servers", "NetApp", "Dell Data Storage",
    "Oracle Database", "SQL Server", "Windows Server", "Network Devices",
    "VMware", "Azure Files", "Qumulo", "Synology",
]

AUDITOR_POPULAR = ["Active Directory", "Windows Server", "Windows File Servers"]
AUDITOR_OTHER = [m for m in AUDITOR_MODULES if m not in AUDITOR_POPULAR]

DC_MODULES = [
    "SharePoint", "Windows File Servers", "NetApp", "Dell Data Storage",
    "Nutanix Files", "Azure Files", "Qumulo", "Synology",
]
DC_POPULAR = ["Windows File Servers", "SharePoint", "Azure Files"]
DC_OTHER = [m for m in DC_MODULES if m not in DC_POPULAR]

# Free Community Edition — Auditor only, module-specific variants (no Entra ID)
CE_MODULES = [
    "Active Directory", "Dell Data Storage", "Exchange", "NetApp",
    "Network Devices", "Oracle Database", "SharePoint", "SQL Server",
    "VMware", "Windows File Servers", "Windows Server",
]

FREEWARE_TOOLS = [
    "DataSec Account Lockout Examiner",
    "DataSec Bulk Password Reset",
    "DataSec Effective Permissions Reporting Tool",
    "DataSec Event Log Manager",
    "DataSec Disk Space Monitor",
    "DataSec Flashlight for NetSuite",
    "DataSec Inactive User Tracker",
    "DataSec Password Expiration Notifier",
    "DataSec Service Monitor",
]

WEBINAR_TOPICS = [
    "Get on Top of Active Directory Certificate Services and Stay There",
    "World Password Day: You Still Have Passwords. Now What?",
    "Ransomware Unmasked: Tactics, Entry Points, and Real-World Lessons",
    "Ransomware Unmasked: Detection, Response, and Resilience",
    "Active Directory Recommended Practices: Avoiding and Detecting Unintended Permission Changes",
    "Active Directory Recommended Practices: Detecting and Remediating Unwanted Persistence",
    "Windows Server Security Masterclass: Proactively Clearing Attack Surfaces",
    "Mastering Endpoint Management with DataSec",
    "Discover and Secure Sensitive Data with DataSec Classification",
    "Group and Identity Management Mastery: Techniques and Best Practices",
    "Ease the Burden of IT Auditing with DataSec Auditor",
    "Block Insider Threats Where They Start: At the Endpoint",
    "Identity Security Roadmap: Reduce Risk and Stop Identity-Based Attacks",
    "PAM Roadmap: Key Strategies for Effective Deployment and Team Engagement",
    "Identify and Reduce Risks Around Sensitive Data with DataSec Access Analyzer",
    "Enhance Your Data Loss Prevention Strategy with DataSec Endpoint Protector",
]

WHITEPAPER_TOPICS = [
    "Ebook: Defending Against Crypto-Ransomware",
    "White Paper: A Practical Guide to GDPR Compliance",
    "White Paper: Active Directory Security Best Practices",
    "Ebook: Privileged Access Management Fundamentals",
    "White Paper: Preventing Data Loss - A DLP Primer",
    "Ebook: Password Policy Best Practices",
    "White Paper: PCI DSS Compliance Checklist for IT Teams",
    "White Paper: Insider Threat Detection Fundamentals",
    "Ebook: Windows Server Hardening Guide",
    "White Paper: HIPAA Compliance for IT Auditors",
]

INDUSTRIES = [
    "Finance", "Healthcare", "Government", "Education",
    "Technology", "Retail", "Manufacturing", "Other",
]
REGULATED_INDUSTRIES = {"Finance", "Healthcare", "Government"}

COMPANY_SIZE_BUCKETS = ["1-50", "51-200", "201-1000", "1000+"]

REGIONS = ["APAC", "EMEA", "LATAM"]

# Country-level conversion varies a lot more than region-level (Kate's real
# experience) — see COUNTRY_CONVERSION_ANCHORS below.
COUNTRIES_BY_REGION = {
    "APAC": ["India", "Australia", "Japan", "Singapore", "Philippines", "Indonesia", "New Zealand"],
    "EMEA": [
        "United Kingdom", "Germany", "France", "Sweden", "Norway", "Denmark",
        "Finland", "United Arab Emirates", "South Africa",
    ],
    "LATAM": ["Brazil", "Mexico", "Argentina", "Colombia", "Chile"],
}

# Logit-scale conversion modifiers. India: Kate personally closed ~0 deals
# there in 4 years. Australia: consistently strong-converting market. Nordics
# (Sweden/Norway/Denmark/Finland): private-by-culture buyers, and technical
# staff are specifically trained not to disclose budget/authority info to
# salespeople, to avoid giving them price leverage. Every other country in
# COUNTRIES_BY_REGION gets a small random modifier instead (generated once
# per dataset — see generate_leads.sample_country_modifiers).
COUNTRY_CONVERSION_ANCHORS = {
    "India": -0.9,
    "Australia": 0.6,
    "Sweden": -0.4,
    "Norway": -0.4,
    "Denmark": -0.4,
    "Finland": -0.4,
}

JOB_LEVELS = ["individual_contributor", "manager", "director", "c_level"]

LEAD_SOURCE_CHANNELS = ["organic", "paid", "referral", "event", "direct"]

DISQUALIFIED_REASONS = [
    "No Budget", "No Interest", "Not a Fit", "Too Small", "Competitor", "Duplicate",
]

MIN_LICENSES = 150
RESELLER_MARGIN = 0.15  # channel/reseller cut netted out of recognized deal value
DEAL_ROUNDING = 50      # deal_amount is always rounded to the nearest $50

# Confirmed 2026-08-29: Active Directory (top of range) and Windows File
# Servers/SQL Server/Exchange anchors are real; the rest are plausible
# interpolations in the same [$4, $7] range.
PRICE_PER_LICENSE_AUDITOR = {
    "Active Directory": 7.00,
    "Microsoft 365": 5.20,
    "Exchange": 4.00,
    "SharePoint": 5.00,
    "Nutanix Files": 5.50,
    "Windows File Servers": 5.60,
    "NetApp": 5.60,
    "Dell Data Storage": 5.60,
    "Oracle Database": 6.50,
    "SQL Server": 4.00,
    "Windows Server": 4.80,
    "Network Devices": 5.30,
    "VMware": 5.80,
    "Azure Files": 5.10,
    "Qumulo": 5.70,
    "Synology": 4.60,
}
DATA_CLASSIFICATION_MULTIPLIER = 1.5
DEFAULT_PRICE_PER_LICENSE = 5.00

# Points per activity — Kate's best recollection of the real CRM lead-score
# field's shape (a lot for a demo request, very little for a collateral),
# exact numbers invented for this project. VISIBILITY_THRESHOLD is the
# cumulative-score point at which a contact's activities materialize into a
# CRM Lead record (data/leads.csv) — below it, nothing gets exported there.
ACTION_POINTS = {
    "hot": 40,
    "warm": 15,
    "webinar_attendance": 10,
    "freeware": 8,
    "webinar_registration": 5,
    "cold": 2,
}
VISIBILITY_THRESHOLD = 10
CONTINUE_PROBABILITY = 0.35  # chance a contact takes another action after one that didn't cross the threshold
MAX_ACTIVITIES = 15          # hard cap so a pathological rng draw can't loop forever

SDR_IDS = [f"SDR_{i:02d}" for i in range(1, 11)]
RM_IDS = [f"RM_{i:02d}" for i in range(1, 26)]

FIRST_NAMES = [
    "Liam", "Noah", "Olivia", "Emma", "Ava", "Sophia", "Mia", "Amelia",
    "Aiden", "Ethan", "James", "Lucas", "Mason", "Harper", "Ella", "Grace",
    "Zoe", "Ryan", "Nathan", "Priya", "Wei", "Hiroshi", "Yuki", "Arjun",
    "Chloe", "Daniel", "Isabella", "Jack", "Lily", "Sam",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Wilson", "Anderson", "Taylor",
    "Thomas", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen",
]

# Real CRM leads were never fully filled in. Mandatory-at-registration
# (first_name/last_name/email) and auto-populated-from-the-triggering-
# activity (product_family/product/originating_activity) fields are always
# present; everything else has a chance of being blank. Rates are Kate's
# plausible estimate, not real vendor numbers.
OPTIONAL_FIELD_MISSING_RATES = {
    "region": 0.04,
    "country": 0.06,
    "industry": 0.18,
    "company_size_bucket": 0.15,
    "job_title_seniority": 0.22,
    "lead_source_channel": 0.06,
}
# Before an SDR has actually engaged a lead, nobody has corrected/enriched
# these fields yet — gaps are worse.
UNTOUCHED_MISSING_RATE_MULTIPLIER = 1.8
UNTOUCHED_MISSING_RATE_CAP = 0.9
UNTOUCHED_FUNNEL_STAGES = {"New (Untouched)", "Working - No Contact"}


def classify_activity_tier(activity_value: str) -> str:
    """Static hot/warm/cool/cold mapping over the CRM's one real activity
    field — this is what an SDR did by eye in real life, never a CRM column.
    """
    if activity_value.startswith(("Get a Demo:", "Free Trial:", "Request a Quote:")):
        return "hot"
    if activity_value.startswith(("Launch In-Browser Demo:", "Free Community Edition:")):
        return "warm"
    if activity_value.startswith(("Webinar Attendance:", "Webinar Registration:")):
        return "cool"
    if activity_value in FREEWARE_TOOLS:
        return "cool"
    if activity_value in WHITEPAPER_TOPICS:
        return "cold"
    raise ValueError(f"Unrecognized activity_value: {activity_value!r}")


def classify_activity_points(activity_value: str) -> int:
    """The real CRM `lead_score` field's points, reconstructed from the same
    activity string (see classify_activity_tier)."""
    if activity_value.startswith(("Get a Demo:", "Free Trial:", "Request a Quote:")):
        return ACTION_POINTS["hot"]
    if activity_value.startswith(("Launch In-Browser Demo:", "Free Community Edition:")):
        return ACTION_POINTS["warm"]
    if activity_value.startswith("Webinar Attendance:"):
        return ACTION_POINTS["webinar_attendance"]
    if activity_value.startswith("Webinar Registration:"):
        return ACTION_POINTS["webinar_registration"]
    if activity_value in FREEWARE_TOOLS:
        return ACTION_POINTS["freeware"]
    if activity_value in WHITEPAPER_TOPICS:
        return ACTION_POINTS["cold"]
    raise ValueError(f"Unrecognized activity_value: {activity_value!r}")
