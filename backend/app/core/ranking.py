from app.core.reputation import reputation_score
from app.core.roles import TARGET_ROLES, match_role

# Roles closest to "Data Scientist" core get a small relevance boost over adjacent roles.
_ROLE_RELEVANCE_WEIGHT = {role: 100 for role in TARGET_ROLES}
_ROLE_RELEVANCE_WEIGHT.update(
    {
        "Data Scientist": 100,
        "Associate Data Scientist": 95,
        "Junior Data Scientist": 95,
        "Applied Scientist": 92,
        "Machine Learning Engineer": 90,
        "AI Engineer": 88,
        "AI/ML Engineer": 88,
        "Generative AI Engineer": 85,
        "Decision Scientist": 85,
        "Research Scientist (AI/ML)": 85,
        "Data Analyst": 80,
        "Analytics Engineer": 80,
        "Data Engineer": 78,
        "Business Intelligence Engineer": 75,
        "BI Analyst": 72,
        "Business Analyst": 68,
        "Statistical Analyst": 70,
        "Quantitative Analyst (Entry Level)": 82,
        "Junior Machine Learning Engineer": 90,
        "Junior Data Analyst": 78,
    }
)


def compute_rank_score(title: str, company_slug: str, resume_match_score: float | None) -> float:
    """Weighted composite: 40% role relevance, 25% company reputation, 35% resume match.
    When resume match is unavailable (AI disabled), its weight is redistributed to role
    relevance and reputation so the score still reflects something meaningful."""
    role = match_role(title)
    role_score = _ROLE_RELEVANCE_WEIGHT.get(role, 50) if role else 50
    company_score = reputation_score(company_slug)

    if resume_match_score is None:
        return round(role_score * 0.55 + company_score * 0.45, 2)

    return round(role_score * 0.40 + company_score * 0.25 + resume_match_score * 0.35, 2)
