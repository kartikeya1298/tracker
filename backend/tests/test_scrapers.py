import httpx
import pytest
import respx

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
