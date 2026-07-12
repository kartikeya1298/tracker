from app.core.filters import (
    is_entry_level,
    is_india_location,
    is_internship,
    is_visa_friendly_location,
    location_passes_filter,
    parse_experience,
)


def test_parse_experience_range():
    exp = parse_experience("0-2 years of experience required")
    assert exp.min_years == 0
    assert exp.max_years == 2


def test_parse_experience_plus():
    exp = parse_experience("3+ years experience")
    assert exp.min_years == 3
    assert exp.max_years is None


def test_parse_experience_entry_level_inferred():
    exp = parse_experience("This is a great fresher / entry-level opportunity")
    assert exp.min_years == 0
    assert exp.max_years == 2


def test_is_entry_level_within_threshold():
    exp = parse_experience("1-2 years")
    assert is_entry_level("Data Analyst", "", exp, max_years=2.0)


def test_is_entry_level_rejects_senior_requirement():
    exp = parse_experience("5-8 years")
    assert not is_entry_level("Data Scientist", "", exp, max_years=2.0)


def test_is_internship_detects_title():
    assert is_internship("Data Science Intern", "")


def test_india_location_detection():
    assert is_india_location("Bengaluru, Karnataka, India")
    assert is_india_location("Hyderabad")
    assert not is_india_location("San Francisco, CA")


def test_location_passes_filter_india_always_passes():
    assert location_passes_filter("Pune, India", include_remote=False, include_global=False)


def test_location_passes_filter_remote_gated():
    assert location_passes_filter("Remote", include_remote=True, include_global=False)
    assert not location_passes_filter("Remote", include_remote=False, include_global=False)


def test_location_passes_filter_global_gated():
    assert location_passes_filter("London, UK", include_remote=False, include_global=True)
    assert not location_passes_filter("London, UK", include_remote=False, include_global=False)


def test_visa_friendly_location_detection():
    assert is_visa_friendly_location("Dubai, UAE")
    assert is_visa_friendly_location("Toronto, Canada")
    assert is_visa_friendly_location("London, United Kingdom")
    assert is_visa_friendly_location("Singapore")
    assert is_visa_friendly_location("Berlin, Germany")
    assert is_visa_friendly_location("Dublin, Ireland")
    assert is_visa_friendly_location("Sydney, Australia")


def test_visa_friendly_location_excludes_us():
    # H1B is lottery-based, not a realistic route to plan around for a fresher -
    # the US is deliberately not on the visa-friendly list.
    assert not is_visa_friendly_location("San Francisco, CA, USA")
    assert not is_visa_friendly_location("New York, United States")
    assert not is_visa_friendly_location("Seattle, WA")


def test_location_passes_filter_global_excludes_non_visa_friendly():
    # include_global=True should NOT let every country through - only the
    # visa-friendly list. A non-visa-friendly country should still be rejected.
    assert not location_passes_filter("San Francisco, CA, USA", include_remote=False, include_global=True)
    assert not location_passes_filter("Tokyo, Japan", include_remote=False, include_global=True)


def test_location_passes_filter_global_includes_visa_friendly():
    assert location_passes_filter("Dubai, UAE", include_remote=False, include_global=True)
    assert location_passes_filter("Amsterdam, Netherlands", include_remote=False, include_global=True)
