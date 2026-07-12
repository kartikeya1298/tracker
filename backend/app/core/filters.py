"""Experience, location, and internship filtering for scraped job postings."""
import re
from dataclasses import dataclass

ENTRY_LEVEL_SIGNALS = re.compile(
    r"\b(entry[- ]level|graduate|new grad|campus|early career|fresher|associate|"
    r"junior|jr\.?|intern(ship)?|trainee|0-2 years?|0-1 years?|1-2 years?)\b",
    re.IGNORECASE,
)

INTERNSHIP_SIGNALS = re.compile(r"\b(intern(ship)?|co-?op|trainee)\b", re.IGNORECASE)

INDIA_LOCATION_SIGNALS = re.compile(
    r"\b(india|bengaluru|bangalore|hyderabad|pune|chennai|mumbai|noida|gurugram|gurgaon|"
    r"delhi|ncr|kolkata|ahmedabad|kochi|coimbatore|indore|jaipur|trivandrum|thiruvananthapuram)\b",
    re.IGNORECASE,
)

REMOTE_SIGNALS = re.compile(r"\b(remote|work from home|wfh|anywhere)\b", re.IGNORECASE)

# Matches patterns like "0-2 years", "1 to 3 years", "2+ years", "minimum 1 year"
EXPERIENCE_RANGE_PATTERNS = [
    re.compile(r"(\d+(?:\.\d+)?)\s*[-–to]+\s*(\d+(?:\.\d+)?)\s*years?", re.IGNORECASE),
    re.compile(r"(\d+(?:\.\d+)?)\s*\+\s*years?", re.IGNORECASE),
    re.compile(r"(?:minimum|min\.?)\s*(\d+(?:\.\d+)?)\s*years?", re.IGNORECASE),
    re.compile(r"(\d+(?:\.\d+)?)\s*years?\s*(?:of)?\s*experience", re.IGNORECASE),
]


@dataclass
class ExperienceRange:
    min_years: float | None = None
    max_years: float | None = None
    raw_text: str = ""


def parse_experience(text: str) -> ExperienceRange:
    """Best-effort extraction of a min/max years-of-experience range from free text."""
    if not text:
        return ExperienceRange()

    m = EXPERIENCE_RANGE_PATTERNS[0].search(text)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        return ExperienceRange(min(lo, hi), max(lo, hi), m.group(0))

    m = EXPERIENCE_RANGE_PATTERNS[1].search(text)
    if m:
        lo = float(m.group(1))
        return ExperienceRange(lo, None, m.group(0))

    m = EXPERIENCE_RANGE_PATTERNS[2].search(text)
    if m:
        lo = float(m.group(1))
        return ExperienceRange(lo, None, m.group(0))

    m = EXPERIENCE_RANGE_PATTERNS[3].search(text)
    if m:
        val = float(m.group(1))
        return ExperienceRange(val, val, m.group(0))

    if ENTRY_LEVEL_SIGNALS.search(text):
        return ExperienceRange(0, 2, "entry-level (inferred)")

    return ExperienceRange()


def is_entry_level(title: str, description: str, exp_range: ExperienceRange, max_years: float = 2.0) -> bool:
    combined = f"{title} {description}"
    if exp_range.min_years is not None:
        # Accept if the role's minimum requirement is within our threshold.
        return exp_range.min_years <= max_years
    return bool(ENTRY_LEVEL_SIGNALS.search(combined))


def is_internship(title: str, description: str) -> bool:
    return bool(INTERNSHIP_SIGNALS.search(title)) or bool(INTERNSHIP_SIGNALS.search(description[:200]))


def is_india_location(location: str) -> bool:
    return bool(INDIA_LOCATION_SIGNALS.search(location or ""))


def is_remote_location(location: str) -> bool:
    return bool(REMOTE_SIGNALS.search(location or ""))


def location_passes_filter(
    location: str,
    include_remote: bool,
    include_global: bool,
) -> bool:
    if is_india_location(location):
        return True
    if include_remote and is_remote_location(location):
        return True
    if include_global:
        return True
    return False
