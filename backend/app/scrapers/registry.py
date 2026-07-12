"""Seed registry of the 50 tracked companies.

`verified=True` entries use a documented public JSON API (Greenhouse, Lever) and work
out of the box. Everything else is a best-effort starting point: large enterprises
overwhelmingly run custom-branded career sites (often layered on Workday,
SAP SuccessFactors, or Oracle Taleo under the hood, but with bespoke frontends), and
their exact DOM structure changes over time and can't be reliably guessed without
inspecting the live page. For `verified=False` rows, `identifier` is a template
GenericPlaywrightScraper config — before that company will actually produce results,
open `careers_url`, inspect the listing markup, and fill in real CSS selectors
(see app/scrapers/generic.py for the config schema). This mirrors how a real
production deployment is bootstrapped: platform + URL is known immediately,
selectors are filled in per-target during onboarding.
"""
import json

from app.models import ATSPlatform


def _custom(url: str, item_sel: str = ".job, .job-listing, .job-card, li[class*=job]") -> str:
    return json.dumps(
        {
            "url": url,
            "item_selector": item_sel,
            "title_selector": "a, .job-title, h3, h2",
            "location_selector": ".location, .job-location, [class*=location]",
            "link_selector": "a",
            "link_attr": "href",
        }
    )


# name, slug, platform, identifier, careers_url, verified
COMPANIES: list[dict] = [
    # --- Verified: public Greenhouse API ---
    {"name": "Databricks", "slug": "databricks", "platform": ATSPlatform.GREENHOUSE,
     "identifier": "databricks", "careers_url": "https://boards.greenhouse.io/databricks", "verified": True},

    # --- Verified: public Lever API (well-known long-standing Lever tenants) ---
    {"name": "Airbnb", "slug": "airbnb", "platform": ATSPlatform.LEVER,
     "identifier": "airbnb", "careers_url": "https://careers.airbnb.com", "verified": False},

    # --- Best-effort Workday tenants (common for large enterprises); VERIFY tenant/dc/site ---
    {"name": "Walmart Global Tech", "slug": "walmart", "platform": ATSPlatform.WORKDAY,
     "identifier": "walmart|walmart|WalmartExternal", "careers_url": "https://careers.walmart.com", "verified": False},
    {"name": "Visa", "slug": "visa", "platform": ATSPlatform.WORKDAY,
     "identifier": "visa|visa|Visa_Careers", "careers_url": "https://careers.visa.com", "verified": False},
    {"name": "Mastercard", "slug": "mastercard", "platform": ATSPlatform.WORKDAY,
     "identifier": "mastercard|mastercard|CorporateCareers", "careers_url": "https://careers.mastercard.com", "verified": False},
    {"name": "Nokia", "slug": "nokia", "platform": ATSPlatform.WORKDAY,
     "identifier": "nokia|nokia|Careers", "careers_url": "https://www.nokia.com/careers/", "verified": False},
    {"name": "Philips", "slug": "philips", "platform": ATSPlatform.WORKDAY,
     "identifier": "philips|philips|External_Careers", "careers_url": "https://www.careers.philips.com", "verified": False},

    # --- SAP SuccessFactors (SAP dogfoods its own product; many enterprises use it too) ---
    {"name": "SAP", "slug": "sap", "platform": ATSPlatform.SAP_CAREERS,
     "identifier": _custom("https://jobs.sap.com/search/"), "careers_url": "https://jobs.sap.com", "verified": False},
    {"name": "Siemens", "slug": "siemens", "platform": ATSPlatform.SUCCESSFACTORS,
     "identifier": _custom("https://jobs.siemens.com/careers"), "careers_url": "https://jobs.siemens.com", "verified": False},
    {"name": "Bosch", "slug": "bosch", "platform": ATSPlatform.SUCCESSFACTORS,
     "identifier": _custom("https://www.bosch.com/careers/jobs/"), "careers_url": "https://www.bosch.com/careers/", "verified": False},
    {"name": "Ericsson", "slug": "ericsson", "platform": ATSPlatform.SUCCESSFACTORS,
     "identifier": _custom("https://jobs.ericsson.com/careers"), "careers_url": "https://www.ericsson.com/en/careers", "verified": False},

    # --- Oracle Careers (Oracle Recruiting Cloud, ORC) ---
    {"name": "Oracle", "slug": "oracle", "platform": ATSPlatform.ORACLE_CAREERS,
     "identifier": _custom("https://careers.oracle.com/en/sites/jobsearch/jobs"), "careers_url": "https://careers.oracle.com", "verified": False},

    # --- Custom-built career sites (big tech) ---
    {"name": "Amazon", "slug": "amazon", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.amazon.jobs/en/search?base_query=data+scientist"), "careers_url": "https://www.amazon.jobs", "verified": False},
    {"name": "Microsoft", "slug": "microsoft", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://jobs.careers.microsoft.com/global/en/search?q=data%20scientist"), "careers_url": "https://careers.microsoft.com", "verified": False},
    {"name": "Google", "slug": "google", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.google.com/about/careers/applications/jobs/results?q=data%20scientist"), "careers_url": "https://careers.google.com", "verified": False},
    {"name": "NVIDIA", "slug": "nvidia", "platform": ATSPlatform.WORKDAY,
     "identifier": "nvidia|nvidia|NVIDIAExternalCareerSite", "careers_url": "https://www.nvidia.com/en-us/about-nvidia/careers/", "verified": False},
    {"name": "Cisco", "slug": "cisco", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://jobs.cisco.com/jobs/SearchJobs/data%2520scientist"), "careers_url": "https://jobs.cisco.com", "verified": False},
    {"name": "IBM", "slug": "ibm", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.ibm.com/careers/search?field_keyword_18[0]=Data%20and%20AI"), "careers_url": "https://www.ibm.com/careers", "verified": False},
    {"name": "Salesforce", "slug": "salesforce", "platform": ATSPlatform.WORKDAY,
     "identifier": "salesforce|salesforce|External_Career_Site", "careers_url": "https://careers.salesforce.com", "verified": False},
    {"name": "Adobe", "slug": "adobe", "platform": ATSPlatform.WORKDAY,
     "identifier": "adobe|adobe|external_experienced", "careers_url": "https://careers.adobe.com", "verified": False},
    {"name": "Intel", "slug": "intel", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://jobs.intel.com/en/search-jobs?k=data%20scientist"), "careers_url": "https://jobs.intel.com", "verified": False},
    {"name": "Qualcomm", "slug": "qualcomm", "platform": ATSPlatform.WORKDAY,
     "identifier": "qualcomm|qualcomm|External", "careers_url": "https://www.qualcomm.com/company/careers", "verified": False},
    {"name": "Apple", "slug": "apple", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://jobs.apple.com/en-us/search?search=data%20scientist"), "careers_url": "https://jobs.apple.com", "verified": False},
    {"name": "Uber", "slug": "uber", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.uber.com/us/en/careers/list/?query=data%20scientist"), "careers_url": "https://www.uber.com/us/en/careers/", "verified": False},
    {"name": "LinkedIn", "slug": "linkedin", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.linkedin.com/jobs/search?keywords=data%20scientist"), "careers_url": "https://careers.linkedin.com", "verified": False},
    {"name": "PayPal", "slug": "paypal", "platform": ATSPlatform.WORKDAY,
     "identifier": "paypal|paypal|JobSearch", "careers_url": "https://careers.pypl.com", "verified": False},
    {"name": "ServiceNow", "slug": "servicenow", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.servicenow.com/jobs/?search=data+scientist"), "careers_url": "https://careers.servicenow.com", "verified": False},
    {"name": "Snowflake", "slug": "snowflake", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.snowflake.com/us/en/search-results?keywords=data%20scientist"), "careers_url": "https://careers.snowflake.com", "verified": False},

    # --- Banking / finance ---
    {"name": "JPMorgan Chase", "slug": "jpmorgan-chase", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.jpmorgan.com/us/en/search-results?keywords=data%20scientist"), "careers_url": "https://careers.jpmorgan.com", "verified": False},
    {"name": "Goldman Sachs", "slug": "goldman-sachs", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://higher.gs.com/roles?query=data%20scientist"), "careers_url": "https://higher.gs.com", "verified": False},

    # --- IT services / consulting (mostly custom career portals; several on SuccessFactors/Taleo) ---
    {"name": "Deloitte", "slug": "deloitte", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://apply.deloitte.com/careers/SearchJobs/data-scientist"), "careers_url": "https://apply.deloitte.com", "verified": False},
    {"name": "Accenture", "slug": "accenture", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.accenture.com/in-en/careers/jobsearch?jk=data%20scientist"), "careers_url": "https://www.accenture.com/in-en/careers", "verified": False},
    {"name": "Capgemini", "slug": "capgemini", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.capgemini.com/careers/join-capgemini/?search=data+scientist"), "careers_url": "https://www.capgemini.com/careers/", "verified": False},
    {"name": "Cognizant", "slug": "cognizant", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.cognizant.com/global/en/search-results?keywords=data%20scientist"), "careers_url": "https://careers.cognizant.com", "verified": False},
    {"name": "Infosys", "slug": "infosys", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://career.infosys.com/jobs?searchText=data%20scientist"), "careers_url": "https://career.infosys.com", "verified": False},
    {"name": "TCS", "slug": "tcs", "platform": ATSPlatform.ORACLE_CAREERS,
     "identifier": _custom("https://ibegin.tcs.com/iBegin/jobs/search?searchText=data+scientist"), "careers_url": "https://ibegin.tcs.com", "verified": False},
    {"name": "HCLTech", "slug": "hcltech", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.hcltech.com/careers/job-search?keywords=data+scientist"), "careers_url": "https://www.hcltech.com/careers", "verified": False},
    {"name": "Wipro", "slug": "wipro", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.wipro.com/careers-home/jobs?keywords=data+scientist"), "careers_url": "https://careers.wipro.com", "verified": False},
    {"name": "Tech Mahindra", "slug": "tech-mahindra", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.techmahindra.com/find-a-job?keywords=data+scientist"), "careers_url": "https://careers.techmahindra.com", "verified": False},
    {"name": "LTIMindtree", "slug": "ltimindtree", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.ltimindtree.com/search?searchText=data+scientist"), "careers_url": "https://careers.ltimindtree.com", "verified": False},
    {"name": "EY", "slug": "ey", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.ey.com/ey/search/?q=data+scientist"), "careers_url": "https://careers.ey.com", "verified": False},
    {"name": "PwC", "slug": "pwc", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://jobs.us.pwc.com/search-jobs/data%20scientist"), "careers_url": "https://www.pwc.com/careers", "verified": False},
    {"name": "KPMG", "slug": "kpmg", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://kpmg.com/us/en/careers/search-openings.html?q=data+scientist"), "careers_url": "https://kpmg.com/careers", "verified": False},
    {"name": "Genpact", "slug": "genpact", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://genpact.taleo.net/careersection/genpact_ext/jobsearch.ftl?searchText=data+scientist"), "careers_url": "https://www.genpact.com/careers", "verified": False},
    {"name": "DXC Technology", "slug": "dxc-technology", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://jobs.dxc.com/global/en/search-results?keywords=data%20scientist"), "careers_url": "https://jobs.dxc.com", "verified": False},
    {"name": "Mphasis", "slug": "mphasis", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.mphasis.com/search?searchText=data+scientist"), "careers_url": "https://careers.mphasis.com", "verified": False},

    # --- India-based product companies ---
    {"name": "Zoho", "slug": "zoho", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.zoho.com/careers/openpositions.html"), "careers_url": "https://www.zoho.com/careers/", "verified": False},
    {"name": "Freshworks", "slug": "freshworks", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.freshworks.com/company/careers/"), "careers_url": "https://www.freshworks.com/company/careers/", "verified": False},
    {"name": "GoComet", "slug": "gocomet", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://gocomet.com/careers/"), "careers_url": "https://gocomet.com/careers/", "verified": False},

    # --- Samsung R&D ---
    {"name": "Samsung R&D", "slug": "samsung-rd", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.samsung.com/in/careers/job-search/"), "careers_url": "https://www.samsung.com/in/careers/", "verified": False},
]


def get_company_by_slug(slug: str) -> dict | None:
    return next((c for c in COMPANIES if c["slug"] == slug), None)
