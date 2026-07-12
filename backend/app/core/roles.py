"""Target Data Science role catalog and fuzzy matching against job titles."""
import re

# Canonical role -> list of surface-form patterns (regex, case-insensitive, word-boundary aware)
TARGET_ROLES: dict[str, list[str]] = {
    "Data Analyst": [r"data anal(ys|yz)t"],
    "Business Analyst": [r"business anal(ys|yz)t"],
    "Junior Data Analyst": [r"junior data anal(ys|yz)t", r"jr\.? data anal(ys|yz)t"],
    "Data Scientist": [r"data scientist(?! ii| iii| iv| v)"],
    "Junior Data Scientist": [r"junior data scientist", r"jr\.? data scientist"],
    "Associate Data Scientist": [r"associate data scientist"],
    "Machine Learning Engineer": [r"machine learning engineer"],
    "Junior Machine Learning Engineer": [r"junior machine learning engineer", r"jr\.? machine learning engineer"],
    "AI Engineer": [r"\bai engineer\b", r"artificial intelligence engineer"],
    "Applied Scientist": [r"applied scientist"],
    "Research Scientist (AI/ML)": [r"research scientist.*(\bai\b|\bml\b|machine learning|artificial intelligence)",
                                     r"(\bai\b|\bml\b|machine learning).*research scientist"],
    "Data Engineer": [r"data engineer(?! ii| iii| iv| v)"],
    "Analytics Engineer": [r"analytics engineer"],
    "Business Intelligence Engineer": [r"business intelligence engineer", r"\bbi engineer\b"],
    "BI Analyst": [r"\bbi anal(ys|yz)t\b", r"business intelligence anal(ys|yz)t"],
    "Decision Scientist": [r"decision scientist"],
    "AI/ML Engineer": [r"ai\s*/\s*ml engineer", r"ai and ml engineer", r"\bml/ai engineer\b"],
    "Generative AI Engineer": [r"generative ai engineer", r"\bgenai engineer\b"],
    "Statistical Analyst": [r"statistical anal(ys|yz)t"],
    "Quantitative Analyst (Entry Level)": [r"quantitative anal(ys|yz)t"],
}

# Precompute a flat list of (canonical_role, compiled_pattern), most specific first (by
# word count of the canonical role name) so e.g. "Junior Data Scientist" is tried before
# the bare "Data Scientist" pattern it would otherwise also match as a substring.
_COMPILED: list[tuple[str, re.Pattern]] = sorted(
    (
        (role, re.compile(pattern, re.IGNORECASE))
        for role, patterns in TARGET_ROLES.items()
        for pattern in patterns
    ),
    key=lambda pair: len(pair[0].split()),
    reverse=True,
)

# Titles that look like a match on keywords but should be excluded (senior/lead/manager-only postings
# unless combined with entry-level signal handled separately in experience filtering).
EXCLUDE_TITLE_PATTERNS = [
    re.compile(r"\b(senior|sr\.?|staff|principal|lead|director|head of|vp|vice president|manager|architect)\b", re.IGNORECASE),
]

# Non-DS software roles to hard-exclude even if a keyword partially overlaps
IGNORE_PATTERNS = [
    re.compile(r"software (development )?engineer(?!.*(\bai\b|\bml\b|machine learning))", re.IGNORECASE),
    re.compile(r"\bdevops\b", re.IGNORECASE),
    re.compile(r"\bfront[- ]?end\b", re.IGNORECASE),
    re.compile(r"\bback[- ]?end\b", re.IGNORECASE),
    re.compile(r"\bfull[- ]?stack\b", re.IGNORECASE),
    re.compile(r"\bmobile (developer|engineer)\b", re.IGNORECASE),
    re.compile(r"\bqa\b|\bquality assurance\b|\bsdet\b", re.IGNORECASE),
]


def match_role(title: str) -> str | None:
    """Return the canonical target role name if the job title matches, else None."""
    if not title:
        return None
    for pattern in IGNORE_PATTERNS:
        if pattern.search(title):
            return None
    for role, pattern in _COMPILED:
        if pattern.search(title):
            if any(p.search(title) for p in EXCLUDE_TITLE_PATTERNS) and not re.search(
                r"\b(entry|junior|jr\.?|associate|graduate|campus|early career|fresher|new grad|i\b)\b",
                title,
                re.IGNORECASE,
            ):
                return None
            return role
    return None


def is_target_role(title: str) -> bool:
    return match_role(title) is not None
