"""Seed registry: the original 50 user-specified companies (51 rows — Adobe has a
second early-careers Workday site) plus 12 user-approved additions (pure-play
analytics/decision-science consulting firms and India-based product companies/GCCs
with large data science hiring) — 63 rows total.

`verified=True` entries use a documented public JSON API (Greenhouse, Lever, or Workday's
CxS API) with a tenant/dc/site confirmed against real, currently-live job-posting URLs
(via web search on 2026-07-12) — these work out of the box, though Workday dc subdomains
do occasionally migrate so it's worth a periodic spot-check. Everything else is a
best-effort starting point: large enterprises overwhelmingly run custom-branded career
sites (often layered on SAP SuccessFactors or Oracle Recruiting Cloud under the hood,
but with bespoke frontends), and their exact DOM structure can't be reliably guessed
without inspecting the live page — this sandbox's network policy blocks raw HTML fetches
against these domains, so that step has to happen in a real browser. For `verified=False`
rows, `identifier` is a template GenericPlaywrightScraper config — before that company
will actually produce results, open `careers_url`, inspect the listing markup, and fill
in real CSS selectors (see app/scrapers/generic.py for the config schema).
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


# Fallback selector lists for sites whose search results only render after a real
# keystroke+submit against the search box (the URL's query string alone isn't enough) -
# see GenericPlaywrightScraper.search_input_selector in app/scrapers/generic.py.
_SEARCH_INPUT_FALLBACK = (
    "input[type='search'], input[placeholder*='search' i], input[aria-label*='search' i], "
    "input[name*='keyword' i], input[name='q']"
)
_SEARCH_SUBMIT_FALLBACK = "button[type='submit'], button[aria-label*='search' i], button:has-text('Search')"


# name, slug, platform, identifier, careers_url, verified
COMPANIES: list[dict] = [
    # --- Verified: public Greenhouse API ---
    {"name": "Databricks", "slug": "databricks", "platform": ATSPlatform.GREENHOUSE,
     "identifier": "databricks", "careers_url": "https://boards.greenhouse.io/databricks", "verified": True},

    # --- Verified: public Greenhouse API (confirmed live postings at boards.greenhouse.io/airbnb;
    #     Airbnb is NOT on Lever despite the platform name suggesting otherwise historically) ---
    {"name": "Airbnb", "slug": "airbnb", "platform": ATSPlatform.GREENHOUSE,
     "identifier": "airbnb", "careers_url": "https://boards.greenhouse.io/airbnb", "verified": True},

    # --- Workday: tenant/dc/site confirmed via live job-posting URLs (web search, 2026-07-12).
    #     Still worth spot-checking periodically since Workday dc subdomains do migrate. ---
    {"name": "Walmart Global Tech", "slug": "walmart", "platform": ATSPlatform.WORKDAY,
     "identifier": "walmart|wd5|WalmartExternal", "careers_url": "https://walmart.wd5.myworkdayjobs.com/WalmartExternal", "verified": True},
    {"name": "Visa", "slug": "visa", "platform": ATSPlatform.WORKDAY,
     "identifier": "visa|wd5|Visa", "careers_url": "https://visa.wd5.myworkdayjobs.com/Visa", "verified": True},
    {"name": "Mastercard", "slug": "mastercard", "platform": ATSPlatform.WORKDAY,
     "identifier": "mastercard|wd1|CorporateCareers", "careers_url": "https://mastercard.wd1.myworkdayjobs.com/CorporateCareers", "verified": True},
    {"name": "Philips", "slug": "philips", "platform": ATSPlatform.WORKDAY,
     "identifier": "philips|wd3|jobs-and-careers", "careers_url": "https://philips.wd3.myworkdayjobs.com/en-US/jobs-and-careers", "verified": True},

    # --- Nokia: NOT Workday. Runs on Oracle Fusion Cloud Recruiting (candidate experience UI
    #     at fa-evmr-saasfaprod1.fa.ocs.oraclecloud.com, fronted by jobs.nokia.com). Still needs
    #     real selectors (see Oracle Careers note below), but the platform/URL are now correct. ---
    {"name": "Nokia", "slug": "nokia", "platform": ATSPlatform.ORACLE_CAREERS,
     "identifier": _custom("https://jobs.nokia.com/en/sites/CX_1/jobs"), "careers_url": "https://jobs.nokia.com/en/sites/CX_1/jobs", "verified": False},

    # --- SAP SuccessFactors (SAP dogfoods its own product; many enterprises use it too).
    #     Selectors confirmed against live rendered HTML via tools/inspect_career_sites.py
    #     (GitHub Actions run, 2026-07-12) - real job titles/locations extracted successfully. ---
    {"name": "SAP", "slug": "sap", "platform": ATSPlatform.SAP_CAREERS,
     "identifier": json.dumps({
         "url": "https://jobs.sap.com/search/?q=data%20scientist",
         "item_selector": "tr.data-row",
         "title_selector": "a.jobTitle-link",
         "location_selector": "td.colLocation span.jobLocation",
         "link_selector": "a.jobTitle-link",
         "link_attr": "href",
     }), "careers_url": "https://jobs.sap.com/search/", "verified": True},
    # Siemens: same "results list" template family as SAP/EY/LTIMindtree below but with
    # different classnames. Location is split into city/state/country spans; only city is
    # captured here (state/country siblings weren't confirmed nested under the same item).
    {"name": "Siemens", "slug": "siemens", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://jobs.siemens.com/en_US/externaljobs/SearchJobs",
         "item_selector": "article.article--result",
         "title_selector": "h3.article__header__text__title",
         "location_selector": ".list-item-jobCity",
         "link_selector": "h3.article__header__text__title a",
         "link_attr": "href",
     }), "careers_url": "https://jobs.siemens.com/en_US/externaljobs/SearchJobs", "verified": True},
    {"name": "Bosch", "slug": "bosch", "platform": ATSPlatform.SUCCESSFACTORS,
     "identifier": _custom("https://jobs.bosch.com/en/"), "careers_url": "https://jobs.bosch.com/en/", "verified": False},
    # Ericsson: the career2.successfactors.eu URL from an earlier round turned out to
    # be a login-gated internal portal (redirects to a Microsoft/Azure AD sign-in
    # screen), not the public site - jobs.ericsson.com/careers is the real one, and
    # (despite the SUCCESSFACTORS platform label) runs the exact same card-grid
    # template as Microsoft's career site (data-test-id="job-listing", hashed
    # "title-XXXXX" classnames) - likely a shared white-label HR-tech vendor, not
    # actually SuccessFactors-branded on the frontend.
    {"name": "Ericsson", "slug": "ericsson", "platform": ATSPlatform.SUCCESSFACTORS,
     "identifier": json.dumps({
         "url": "https://jobs.ericsson.com/careers?query=data+scientist",
         "item_selector": "[data-test-id='job-listing']",
         "title_selector": "div[class*='title-']",
         "location_selector": "div[class*='fieldValue-']",
         "link_selector": "a.r-link",
         "link_attr": "href",
     }), "careers_url": "https://jobs.ericsson.com/careers", "verified": True},

    # --- Oracle Careers (Oracle Recruiting Cloud, ORC) ---
    {"name": "Oracle", "slug": "oracle", "platform": ATSPlatform.ORACLE_CAREERS,
     "identifier": _custom("https://careers.oracle.com/en/sites/jobsearch/jobs"), "careers_url": "https://careers.oracle.com", "verified": False},

    # --- Custom-built career sites (big tech) ---
    {"name": "Amazon", "slug": "amazon", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://www.amazon.jobs/en/search?base_query=data+scientist",
         "item_selector": "div.job-tile",
         "title_selector": "h3.job-title",
         "location_selector": ".location-and-id li.text-nowrap",
         "link_selector": "a.job-link",
         "link_attr": "href",
     }), "careers_url": "https://www.amazon.jobs", "verified": True},
    # Microsoft: item container uses a stable data-test-id attribute, but title/location
    # selectors rely on CSS-module hash-suffixed classnames (e.g. title-1aNJK) matched via
    # substring - these hashes can rotate on Microsoft's redeploys and may need re-checking.
    {"name": "Microsoft", "slug": "microsoft", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://jobs.careers.microsoft.com/global/en/search?q=data%20scientist",
         "item_selector": "[data-test-id='job-listing']",
         "title_selector": "div[class*='title-']",
         "location_selector": "div[class*='fieldValue-']",
         "link_selector": "a.r-link",
         "link_attr": "href",
     }), "careers_url": "https://careers.microsoft.com", "verified": True},
    # Confirmed correct search results URL from a real user search (needs the trailing
    # slash before the query string - .../jobs/results/?q=... not .../jobs/results?q=...).
    {"name": "Google", "slug": "google", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.google.com/about/careers/applications/jobs/results/?q=Data+Scientist&hl=en-GB"), "careers_url": "https://careers.google.com", "verified": False},
    {"name": "NVIDIA", "slug": "nvidia", "platform": ATSPlatform.WORKDAY,
     "identifier": "nvidia|wd5|NVIDIAExternalCareerSite", "careers_url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite", "verified": True},
    # jobs.cisco.com was the wrong domain (legacy portal, no real listings found).
    # careers.cisco.com is the real one - user-confirmed via a live job posting URL -
    # and matches the same Oracle Fusion Cloud Recruiting URL shape as JPMorgan
    # Chase/Nokia/Oracle.
    {"name": "Cisco", "slug": "cisco", "platform": ATSPlatform.ORACLE_CAREERS,
     "identifier": _custom("https://careers.cisco.com/global/en/search-results?keywords=Data+Scientist&location=India&locationLevel=country&mode=location"), "careers_url": "https://careers.cisco.com", "verified": False},
    # IBM: the category-filter URL alone doesn't render results on load - confirmed the
    # search box needs a real keystroke+submit. Uses IBM's Carbon Design System card grid.
    {"name": "IBM", "slug": "ibm", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://www.ibm.com/careers/search?field_keyword_18[0]=Data%20and%20AI",
         "item_selector": "div.bx--card-group__cards__col",
         "title_selector": "div.bx--card__heading",
         "location_selector": "div.ibm--card__copy__inner",
         "link_selector": "a.bx--card-group__card",
         "link_attr": "href",
         "search_input_selector": _SEARCH_INPUT_FALLBACK,
         "search_submit_selector": _SEARCH_SUBMIT_FALLBACK,
     }), "careers_url": "https://www.ibm.com/careers", "verified": True},
    {"name": "Salesforce", "slug": "salesforce", "platform": ATSPlatform.WORKDAY,
     "identifier": "salesforce|wd12|External_Career_Site", "careers_url": "https://salesforce.wd12.myworkdayjobs.com/External_Career_Site", "verified": True},
    {"name": "Adobe", "slug": "adobe", "platform": ATSPlatform.WORKDAY,
     "identifier": "adobe|wd5|external_experienced", "careers_url": "https://adobe.wd5.myworkdayjobs.com/external_experienced", "verified": True},
    # Adobe also runs a separate Workday site for university/new-grad hiring, which is
    # arguably more relevant to a fresher tracker than the experienced-hire site above.
    {"name": "Adobe Early Careers", "slug": "adobe-early-careers", "platform": ATSPlatform.WORKDAY,
     "identifier": "adobe|wd5|external_university", "careers_url": "https://adobe.wd5.myworkdayjobs.com/external_university", "verified": True},
    {"name": "Intel", "slug": "intel", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://jobs.intel.com/en/search-jobs?k=data%20scientist"), "careers_url": "https://jobs.intel.com", "verified": False},
    # Qualcomm: confirmed by hitting Workday's CxS API directly for both candidate dc
    # subdomains - wd12 returns 200 with a valid jobPostings payload, wd5 returns 422.
    {"name": "Qualcomm", "slug": "qualcomm", "platform": ATSPlatform.WORKDAY,
     "identifier": "qualcomm|wd12|External", "careers_url": "https://qualcomm.wd12.myworkdayjobs.com/External", "verified": True},
    # Apple: same story as IBM - the ?search= query param doesn't populate results
    # without an actual search-box interaction.
    {"name": "Apple", "slug": "apple", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://jobs.apple.com/en-us/search?search=data%20scientist",
         "item_selector": "div.job-title.job-list-item",
         "title_selector": "a.link-inline",
         "location_selector": "div.job-title-location span:not(.a11y)",
         "link_selector": "a.link-inline",
         "link_attr": "href",
         "search_input_selector": _SEARCH_INPUT_FALLBACK,
         "search_submit_selector": _SEARCH_SUBMIT_FALLBACK,
     }), "careers_url": "https://jobs.apple.com", "verified": True},
    {"name": "Uber", "slug": "uber", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.uber.com/us/en/careers/list/?query=data%20scientist"), "careers_url": "https://www.uber.com/us/en/careers/", "verified": False},
    # careers.linkedin.com/jobs/search is a dead Apache Sling path (plain 404) - the
    # real public job-search surface is linkedin.com/jobs. Confirmed via live
    # inspection (2026-07-12): 60/60 matched title/location/link across every card,
    # no search-interaction needed since ?location= already filters server-side.
    {"name": "LinkedIn", "slug": "linkedin", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://www.linkedin.com/jobs/data-scientist-jobs?location=India",
         "item_selector": "div.job-search-card",
         "title_selector": "h3.base-search-card__title",
         "location_selector": "span.job-search-card__location",
         "link_selector": "a.base-card__full-link",
         "link_attr": "href",
     }), "careers_url": "https://www.linkedin.com/jobs/data-scientist-jobs", "verified": True},
    {"name": "PayPal", "slug": "paypal", "platform": ATSPlatform.WORKDAY,
     "identifier": "paypal|wd1|jobs", "careers_url": "https://paypal.wd1.myworkdayjobs.com/jobs", "verified": True},
    {"name": "ServiceNow", "slug": "servicenow", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.servicenow.com/jobs/?search=data+scientist"), "careers_url": "https://careers.servicenow.com", "verified": False},
    # Snowflake: same "URL param alone doesn't search" pattern as IBM/Apple. Runs on a
    # Phenom People career site. location_selector is approximate - the confirmed DOM
    # only isolated a wrapping "information" block whose text is "Location <city> ...
    # Category <dept>", not a dedicated location-only element - noisier than ideal but
    # still usable free text.
    {"name": "Snowflake", "slug": "snowflake", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://careers.snowflake.com/us/en/search-results?keywords=data%20scientist",
         "item_selector": "li.jobs-list-item",
         "title_selector": "a[data-ph-at-id='job-link']",
         "location_selector": "div.information",
         "link_selector": "a[data-ph-at-id='job-link']",
         "link_attr": "href",
         "search_input_selector": _SEARCH_INPUT_FALLBACK,
         "search_submit_selector": _SEARCH_SUBMIT_FALLBACK,
     }), "careers_url": "https://careers.snowflake.com", "verified": True},

    # --- Banking / finance ---
    # careers.jpmorgan.com redirected to a marketing homepage with no search box in
    # the DOM. User-supplied the real underlying Oracle Fusion Cloud Recruiting deep
    # link (same platform as Nokia/Oracle), which carries search state directly in
    # the URL and works without any client-side interaction.
    {"name": "JPMorgan Chase", "slug": "jpmorgan-chase", "platform": ATSPlatform.ORACLE_CAREERS,
     "identifier": _custom("https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?keyword=Data+scientist&location=India&locationId=300000000289360&locationLevel=country&mode=location"), "careers_url": "https://careers.jpmorgan.com", "verified": False},
    {"name": "Goldman Sachs", "slug": "goldman-sachs", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://higher.gs.com/roles?query=data%20scientist",
         "item_selector": "div.d-flex.justify-content-between.border-bottom",
         "title_selector": "a.text-decoration-none > span.gs-text",
         "location_selector": "[data-testid='location']",
         "link_selector": "a.text-decoration-none",
         "link_attr": "href",
     }), "careers_url": "https://higher.gs.com", "verified": True},

    # --- IT services / consulting (mostly custom career portals; several on SuccessFactors/Taleo) ---
    # Deloitte: same "results list" template family as Siemens (likely a shared career-site
    # vendor). Location is the last of several pipe-separated spans (company | practice |
    # location) - :last-child is the most reliable way to grab it without a dedicated class.
    {"name": "Deloitte", "slug": "deloitte", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://apply.deloitte.com/careers/SearchJobs/data-scientist",
         "item_selector": "article.article--result",
         "title_selector": "h3.article__header__text__title a",
         "location_selector": ".article__header__text__subtitle span:last-child",
         "link_selector": "h3.article__header__text__title a",
         "link_attr": "href",
     }), "careers_url": "https://apply.deloitte.com", "verified": True},
    # Accenture: title/location confirmed working. The job card is an expand-in-place
    # accordion rather than a direct link to a job detail page, so no real apply href was
    # found - apply_url falls back to the search page (still enough to detect new matches).
    {"name": "Accenture", "slug": "accenture", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://www.accenture.com/in-en/careers/jobsearch?jk=data%20scientist",
         "item_selector": "div.rad-filters-vertical__job-card",
         "title_selector": "h3.rad-filters-vertical__job-card-title",
         "location_selector": "span.rad-filters-vertical__job-card-details-location",
         "link_selector": "a",
         "link_attr": "href",
     }), "careers_url": "https://www.accenture.com/in-en/careers", "verified": True},
    {"name": "Capgemini", "slug": "capgemini", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.capgemini.com/careers/join-capgemini/?search=data+scientist"), "careers_url": "https://www.capgemini.com/careers/", "verified": False},
    # /global/en/search-results was the wrong path - user-confirmed real URL is
    # /global-en/jobs/ with a singular "keyword" param.
    {"name": "Cognizant", "slug": "cognizant", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.cognizant.com/global-en/jobs/?keyword=Data+Scientist&location=&radius=100&lat=&lng=&cname=&ccode=&pagesize=10#results"), "careers_url": "https://careers.cognizant.com", "verified": False},
    # Infosys: title/location confirmed working (Angular Material cards). The card is
    # click-routed via the Angular app's JS router with no static href - apply_url falls
    # back to the search page.
    {"name": "Infosys", "slug": "infosys", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://career.infosys.com/jobs?searchText=data%20scientist",
         "item_selector": "mat-card.DSA_wb_card-widget",
         "title_selector": "div.job-titleTxt",
         "location_selector": "div.job-locationTxt",
         "link_selector": "mat-card",
         "link_attr": "href",
     }), "careers_url": "https://career.infosys.com", "verified": True},
    # TCS runs its own custom candidate platform ("iBegin"), not Oracle Taleo.
    {"name": "TCS", "slug": "tcs", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://ibegin.tcs.com/iBegin/jobs/search?searchText=data+scientist"), "careers_url": "https://ibegin.tcs.com", "verified": False},
    # www.hcltech.com was the wrong domain (explains the earlier HTTP2 protocol
    # error) - user-confirmed real domain is careers.hcltech.com. Real selectors
    # confirmed via inspection - location is approximate (footer concatenates job
    # ID + country + city with no distinguishing class per field).
    {"name": "HCLTech", "slug": "hcltech", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://careers.hcltech.com/search/?q=Data+Scientist&locationsearch=&searchResultView=LIST&pageNumber=0&facetFilters=%7B%7D&sortBy=&markerViewed=&carouselIndex=",
         "item_selector": "li[data-testid='jobCard']",
         "title_selector": "a.jobCardTitle",
         "location_selector": "[data-testid='jobCardFooter']",
         "link_selector": "a.jobCardTitle",
         "link_attr": "href",
     }), "careers_url": "https://careers.hcltech.com", "verified": True},
    {"name": "Wipro", "slug": "wipro", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.wipro.com/careers-home/jobs?keywords=data+scientist"), "careers_url": "https://careers.wipro.com", "verified": False},
    {"name": "Tech Mahindra", "slug": "tech-mahindra", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.techmahindra.com/find-a-job?keywords=data+scientist"), "careers_url": "https://careers.techmahindra.com", "verified": False},
    # LTIMindtree and EY share the exact same "data-row" table template as SAP above
    # (likely the same underlying career-site vendor/template).
    {"name": "LTIMindtree", "slug": "ltimindtree", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://careers.ltimindtree.com/search?searchText=data+scientist",
         "item_selector": "tr.data-row",
         "title_selector": "a.jobTitle-link",
         "location_selector": "td.colLocation span.jobLocation",
         "link_selector": "a.jobTitle-link",
         "link_attr": "href",
     }), "careers_url": "https://careers.ltimindtree.com", "verified": True},
    {"name": "EY", "slug": "ey", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://careers.ey.com/ey/search/?q=data+scientist",
         "item_selector": "tr.data-row",
         "title_selector": "a.jobTitle-link",
         "location_selector": "td.colLocation span.jobLocation",
         "link_selector": "a.jobTitle-link",
         "link_attr": "href",
     }), "careers_url": "https://careers.ey.com", "verified": True},
    {"name": "PwC", "slug": "pwc", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://jobs.us.pwc.com/search-jobs/data%20scientist",
         "item_selector": "li.search-results-list__item",
         "title_selector": "a.search-results-list__job-link",
         "location_selector": ".search-results-list__job-info.job-location",
         "link_selector": "a.search-results-list__job-link",
         "link_attr": "href",
     }), "careers_url": "https://jobs.us.pwc.com", "verified": True},
    {"name": "KPMG", "slug": "kpmg", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://kpmg.com/us/en/careers/search-openings.html?q=data+scientist"), "careers_url": "https://kpmg.com/careers", "verified": False},
    {"name": "Genpact", "slug": "genpact", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://genpact.taleo.net/careersection/genpact_ext/jobsearch.ftl?searchText=data+scientist"), "careers_url": "https://www.genpact.com/careers", "verified": False},
    {"name": "DXC Technology", "slug": "dxc-technology", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://jobs.dxc.com/global/en/search-results?keywords=data%20scientist"), "careers_url": "https://jobs.dxc.com", "verified": False},
    {"name": "Mphasis", "slug": "mphasis", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.mphasis.com/search?searchText=data+scientist"), "careers_url": "https://careers.mphasis.com", "verified": False},

    # --- India-based product companies ---
    # openpositions.html 404s now; /careers/ shows current openings directly with no
    # search interaction needed.
    {"name": "Zoho", "slug": "zoho", "platform": ATSPlatform.CUSTOM,
     "identifier": json.dumps({
         "url": "https://www.zoho.com/careers/",
         "item_selector": "div.cw-filter-joblist",
         "title_selector": "a.cw-3-title",
         "location_selector": "p.filter-subhead",
         "link_selector": "a.cw-3-title",
         "link_attr": "href",
     }), "careers_url": "https://www.zoho.com/careers/", "verified": True},
    {"name": "Freshworks", "slug": "freshworks", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.freshworks.com/company/careers/"), "careers_url": "https://www.freshworks.com/company/careers/", "verified": False},
    {"name": "GoComet", "slug": "gocomet", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://gocomet.com/careers/"), "careers_url": "https://gocomet.com/careers/", "verified": False},

    # --- Samsung R&D ---
    {"name": "Samsung R&D", "slug": "samsung-rd", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.samsung.com/in/careers/job-search/"), "careers_url": "https://www.samsung.com/in/careers/", "verified": False},

    # --- User-requested additions: pure-play analytics/decision-science consulting
    # firms and India-based product companies/GCCs with large data science hiring,
    # often more fresher-friendly for DS specifically than several companies above. ---
    {"name": "Mu Sigma", "slug": "mu-sigma", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.mu-sigma.com/career/"), "careers_url": "https://www.mu-sigma.com/career/", "verified": False},
    # Confirmed on Workday via multiple live job-posting URLs
    # (fractal.wd1.myworkdayjobs.com/en-US/Careers/job/...).
    {"name": "Fractal Analytics", "slug": "fractal-analytics", "platform": ATSPlatform.WORKDAY,
     "identifier": "fractal|wd1|Careers", "careers_url": "https://fractal.wd1.myworkdayjobs.com/en-US/Careers", "verified": True},
    # Real job data confirmed (title "p.job-title" / "a.job-title-link" and location
    # value "span.label-value.location" both found via inspection), but the shared
    # item wrapper containing both wasn't identified - title and location appeared as
    # same-count (10) sibling elements, not one obviously-common parent. Needs a
    # closer look at the live page's DOM tree to find the real item_selector before
    # this can be marked verified.
    {"name": "ZS Associates", "slug": "zs-associates", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://jobs.zs.com/jobs", item_sel=".job-result, .job-card"), "careers_url": "https://jobs.zs.com/jobs", "verified": False},
    # Runs on the SenseHQ ATS platform.
    {"name": "Tiger Analytics", "slug": "tiger-analytics", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://tiger-analytics.sensehq.com/careers"), "careers_url": "https://tiger-analytics.sensehq.com/careers", "verified": False},
    {"name": "LatentView Analytics", "slug": "latentview-analytics", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.latentview.com/career/"), "careers_url": "https://www.latentview.com/career/", "verified": False},
    {"name": "Flipkart", "slug": "flipkart", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.flipkartcareers.com/data-science"), "careers_url": "https://www.flipkartcareers.com/data-science", "verified": False},
    {"name": "Swiggy", "slug": "swiggy", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://careers.swiggy.com/"), "careers_url": "https://careers.swiggy.com/", "verified": False},
    {"name": "Target India", "slug": "target-india", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://indiajobs.target.com/search-jobs?k=Data%20Scientist"), "careers_url": "https://indiajobs.target.com", "verified": False},
    # Runs on Oracle Fusion Cloud Recruiting (careers.americanexpress.com/en/sites/
    # CX_1/job/... confirmed via a live job posting URL) - same platform as JPMorgan
    # Chase/Cisco/Nokia/Oracle above.
    {"name": "American Express", "slug": "american-express", "platform": ATSPlatform.ORACLE_CAREERS,
     "identifier": _custom("https://careers.americanexpress.com/en/sites/CX_1/jobs?keyword=Data+Scientist&location=India&locationLevel=country&mode=location"),
     "careers_url": "https://careers.americanexpress.com", "verified": False},
    {"name": "Optum", "slug": "optum", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom("https://www.optum.in/about/careers.html"), "careers_url": "https://www.optum.in/about/careers.html", "verified": False},
    # Runs on Oracle Fusion Cloud Recruiting with a confirmed India locationId found
    # directly via search (fa-ewjt-saasfaprod1.fa.ocs.oraclecloud.com), unlike most
    # other Oracle-Cloud rows here where the locationId is unknown.
    {"name": "EXL Service", "slug": "exl-service", "platform": ATSPlatform.ORACLE_CAREERS,
     "identifier": _custom(
         "https://fa-ewjt-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_2/jobs"
         "?keyword=Data+Scientist&location=India&locationId=300000000467203&locationLevel=country&mode=location"
     ), "careers_url": "https://www.exlservice.com/careers", "verified": False},
    # Confirmed real title/link data ("li.opening-job" / "h4.details-title" /
    # "a.link--block.details.js-job-ad-link"), but this page groups jobs under a
    # location heading rather than repeating the location inside each job's own
    # element (confirmed via "section.openings-section.opening--grouped" wrapping
    # multiple "li.opening-job" per location) - GenericPlaywrightScraper can only
    # extract fields from within each item's own subtree, not an ancestor heading, so
    # location would come back empty here. Runs on SmartRecruiters, which (like
    # Greenhouse/Lever) has a public postings JSON API -
    # api.smartrecruiters.com/v1/companies/{company}/postings - that returns location
    # as a real structured field and is the proper fix; worth a dedicated adapter
    # (see app/scrapers/greenhouse.py for the pattern to follow) rather than solving
    # this via the generic HTML scraper.
    {"name": "WNS Global Services", "slug": "wns-global-services", "platform": ATSPlatform.CUSTOM,
     "identifier": _custom(
         "https://careers.smartrecruiters.com/WNSGlobalServices144/wns-india-career-page",
         item_sel="li.opening-job",
     ),
     "careers_url": "https://careers.smartrecruiters.com/WNSGlobalServices144/wns-india-career-page", "verified": False},
]


def get_company_by_slug(slug: str) -> dict | None:
    return next((c for c in COMPANIES if c["slug"] == slug), None)
