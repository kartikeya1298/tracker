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

# Countries/cities where an Indian fresher has a realistic shot at employer-sponsored
# work authorization - i.e. skilled-worker visa routes that aren't a lottery and don't
# require years of prior experience to qualify. Deliberately excludes the US: H1B is
# lottery-based and effectively impossible for a fresh graduate with no existing
# US employer/OPT status to plan around. Edit this list directly to change what
# "global" means for INCLUDE_GLOBAL - there's no env-var override for it, matching
# how INDIA_LOCATION_SIGNALS/REMOTE_SIGNALS above are also hardcoded, not configurable.
VISA_FRIENDLY_LOCATION_SIGNALS = re.compile(
    r"\b("
    r"uae|dubai|abu dhabi|sharjah|united arab emirates|"
    r"qatar|doha|"
    r"singapore|"
    r"canada|toronto|vancouver|montreal|ottawa|calgary|"
    r"united kingdom|\buk\b|london|manchester|birmingham|edinburgh|"
    r"germany|berlin|munich|frankfurt|hamburg|"
    r"netherlands|amsterdam|rotterdam|"
    r"ireland|dublin|"
    r"australia|sydney|melbourne|brisbane|perth|"
    r"new zealand|auckland|wellington"
    r")\b",
    re.IGNORECASE,
)

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


def is_visa_friendly_location(location: str) -> bool:
    return bool(VISA_FRIENDLY_LOCATION_SIGNALS.search(location or ""))


def location_passes_filter(
    location: str,
    include_remote: bool,
    include_global: bool,
) -> bool:
    """India always passes. Remote passes if INCLUDE_REMOTE is on. Everything else
    (a specific non-India country) only passes if INCLUDE_GLOBAL is on AND that
    location is on the visa-friendly list - "global" does not mean "everywhere,"
    it means "countries where a fresher visa route realistically exists."""
    if is_india_location(location):
        return True
    if include_remote and is_remote_location(location):
        return True
    if include_global and is_visa_friendly_location(location):
        return True
    return False
