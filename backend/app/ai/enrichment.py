import logging

from app.ai.client import ask_json
from app.ai.skills import extract_skills_keyword

logger = logging.getLogger(__name__)

ENRICHMENT_PROMPT = """You are helping a job seeker evaluate a Data Science-related job posting.

JOB TITLE: {title}
COMPANY: {company}
LOCATION: {location}
JOB DESCRIPTION:
{description}

CANDIDATE RESUME:
{resume}

Respond with ONLY a JSON object (no markdown fences, no commentary) with these exact keys:
{{
  "summary": "2-3 sentence plain-English summary of the role and what the candidate would do day to day",
  "skills": ["list", "of", "required or preferred technical skills mentioned or implied, e.g. Python, SQL, Power BI"],
  "resume_match_score": <integer 0-100, how well the candidate's resume matches this job's requirements>,
  "resume_match_notes": "1-2 sentences explaining the score: key overlaps and key gaps",
  "learning_recommendations": "1-3 sentences recommending specific resources/topics to close the biggest skill gaps for this role, or empty string if no material gaps"
}}
"""


class JobEnrichment:
    def __init__(self, summary: str, skills: list[str], resume_match_score: float | None,
                 resume_match_notes: str, learning_recommendations: str):
        self.summary = summary
        self.skills = skills
        self.resume_match_score = resume_match_score
        self.resume_match_notes = resume_match_notes
        self.learning_recommendations = learning_recommendations


async def enrich_job(title: str, company: str, location: str, description: str, resume_text: str) -> JobEnrichment:
    keyword_skills = extract_skills_keyword(f"{title}\n{description}")

    result = await ask_json(
        ENRICHMENT_PROMPT.format(
            title=title,
            company=company,
            location=location,
            description=(description or "")[:6000],
            resume=(resume_text or "No resume provided.")[:4000],
        ),
        max_tokens=1024,
    )

    if result is None:
        return JobEnrichment(
            summary="",
            skills=keyword_skills,
            resume_match_score=None,
            resume_match_notes="",
            learning_recommendations="",
        )

    ai_skills = result.get("skills") or []
    merged_skills = sorted(set(keyword_skills) | {s.strip() for s in ai_skills if s and s.strip()})
    score = result.get("resume_match_score")
    try:
        score = float(score) if score is not None else None
    except (TypeError, ValueError):
        score = None

    return JobEnrichment(
        summary=result.get("summary", ""),
        skills=merged_skills,
        resume_match_score=score,
        resume_match_notes=result.get("resume_match_notes", ""),
        learning_recommendations=result.get("learning_recommendations", ""),
    )
