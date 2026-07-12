import json

from app.scrapers.factory import get_scraper
from app.scrapers.registry import COMPANIES


def test_no_duplicate_slugs():
    slugs = [c["slug"] for c in COMPANIES]
    assert len(slugs) == len(set(slugs))


def test_every_company_constructs_a_scraper():
    for c in COMPANIES:
        get_scraper(c["platform"], c["identifier"])


def test_generic_scraper_configs_have_required_keys():
    required = {"url", "item_selector", "title_selector", "location_selector", "link_selector", "link_attr"}
    for c in COMPANIES:
        ident = c["identifier"]
        if ident.strip().startswith("{"):
            cfg = json.loads(ident)
            missing = required - cfg.keys()
            assert not missing, f"{c['slug']} missing config keys: {missing}"


def test_workday_identifiers_have_three_parts():
    for c in COMPANIES:
        if c["platform"].value == "workday":
            parts = c["identifier"].split("|")
            assert len(parts) == 3, f"{c['slug']} workday identifier malformed: {c['identifier']!r}"
