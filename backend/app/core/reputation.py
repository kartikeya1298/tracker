"""Static company reputation tiers used as one input to job ranking.
Tiering is a coarse, opinionated heuristic (brand recognition + comp/benefits reputation
for DS/ML roles) — adjust freely to match your own priorities."""

TIER_1 = {  # score 100
    "google", "microsoft", "amazon", "apple", "nvidia", "databricks", "snowflake",
    "linkedin", "salesforce", "goldman-sachs", "jpmorgan-chase",
}
TIER_2 = {  # score 80
    "adobe", "oracle", "sap", "cisco", "ibm", "intel", "qualcomm", "uber", "airbnb",
    "paypal", "visa", "mastercard", "servicenow", "walmart", "samsung-rd",
}
TIER_3 = {  # score 60
    "siemens", "bosch", "philips", "nokia", "ericsson", "deloitte", "accenture",
    "ey", "pwc", "kpmg", "zoho", "freshworks",
}
# everything else (IT services majors, mid-size) defaults to 45


def reputation_score(company_slug: str) -> float:
    if company_slug in TIER_1:
        return 100.0
    if company_slug in TIER_2:
        return 80.0
    if company_slug in TIER_3:
        return 60.0
    return 45.0
