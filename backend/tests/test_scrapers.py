import json
import urllib.parse

import httpx
import pytest
import respx

from app.scrapers.generic import GenericPlaywrightScraper
from app.scrapers.greenhouse import GreenhouseScraper
from app.scrapers.lever import LeverScraper


@pytest.mark.asyncio
@respx.mock
async def test_greenhouse_parses_jobs():
    respx.get("https://boards-api.greenhouse.io/v1/boards/acme/jobs?content=true").mock(
        return_value=httpx.Response(
            200,
            json={
                "jobs": [
                    {
                        "id": 111,
                        "title": "Junior Data Scientist",
                        "location": {"name": "Bengaluru, India"},
                        "absolute_url": "https://boards.greenhouse.io/acme/jobs/111",
                        "content": "<p>0-2 years experience. Python, SQL required.</p>",
                        "updated_at": "2026-07-10T12:00:00-00:00",
                    }
                ]
            },
        )
    )
    scraper = GreenhouseScraper("acme")
    jobs = await scraper.fetch_jobs()
    assert len(jobs) == 1
    assert jobs[0].title == "Junior Data Scientist"
    assert jobs[0].location == "Bengaluru, India"
    assert jobs[0].external_id == "111"
    assert jobs[0].apply_url == "https://boards.greenhouse.io/acme/jobs/111"
    assert jobs[0].posted_date is not None


@pytest.mark.asyncio
@respx.mock
async def test_lever_parses_jobs():
    respx.get("https://api.lever.co/v0/postings/acme?mode=json").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "abc-123",
                    "text": "Data Analyst",
                    "categories": {"location": "Mumbai, India"},
                    "hostedUrl": "https://jobs.lever.co/acme/abc-123",
                    "descriptionPlain": "Great entry level role.",
                    "lists": [],
                    "createdAt": 1752192000000,
                }
            ],
        )
    )
    scraper = LeverScraper("acme")
    jobs = await scraper.fetch_jobs()
    assert len(jobs) == 1
    assert jobs[0].title == "Data Analyst"
    assert jobs[0].location == "Mumbai, India"
    assert jobs[0].external_id == "abc-123"


# A page whose job listing only appears after a real search-box interaction - mirrors
# what IBM/Apple/Snowflake turned out to need (a URL query param alone isn't enough).
_SEARCH_GATED_HTML = """
<!DOCTYPE html>
<html><body>
<input type="search" id="q" />
<button id="submit-btn">Search</button>
<div id="results"></div>
<script>
document.getElementById('submit-btn').addEventListener('click', function () {
  if (document.getElementById('q').value === 'data scientist') {
    document.getElementById('results').innerHTML =
      '<div class="job-card">' +
      '<a class="job-title" href="/jobs/1">Data Scientist</a>' +
      '<span class="job-location">Bengaluru, India</span>' +
      '</div>';
  }
});
</script>
</body></html>
"""


@pytest.mark.asyncio
async def test_generic_scraper_performs_search_interaction_when_configured():
    data_url = "data:text/html;charset=utf-8," + urllib.parse.quote(_SEARCH_GATED_HTML)
    config = json.dumps(
        {
            "url": data_url,
            "item_selector": ".job-card",
            "title_selector": ".job-title",
            "location_selector": ".job-location",
            "link_selector": ".job-title",
            "link_attr": "href",
            "search_input_selector": "input[type='search']",
            "search_submit_selector": "#submit-btn",
        }
    )
    scraper = GenericPlaywrightScraper(config, timeout=15)
    jobs = await scraper.fetch_jobs()
    assert len(jobs) == 1
    assert jobs[0].title == "Data Scientist"
    assert jobs[0].location == "Bengaluru, India"
    assert jobs[0].apply_url.endswith("/jobs/1")


@pytest.mark.asyncio
async def test_generic_scraper_finds_nothing_without_search_interaction():
    """Same page, but the config omits search_input_selector - the results div never
    gets populated, so the scraper should come back empty rather than erroring."""
    data_url = "data:text/html;charset=utf-8," + urllib.parse.quote(_SEARCH_GATED_HTML)
    config = json.dumps(
        {
            "url": data_url,
            "wait_selector": "#results",
            "item_selector": ".job-card",
            "title_selector": ".job-title",
            "location_selector": ".job-location",
            "link_selector": ".job-title",
            "link_attr": "href",
        }
    )
    scraper = GenericPlaywrightScraper(config, timeout=15)
    jobs = await scraper.fetch_jobs()
    assert jobs == []
