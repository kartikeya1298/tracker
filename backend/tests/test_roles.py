from app.core.roles import match_role


def test_matches_core_data_scientist():
    assert match_role("Data Scientist") == "Data Scientist"


def test_matches_junior_variant():
    assert match_role("Junior Data Scientist") == "Junior Data Scientist"


def test_matches_ai_ml_engineer_slash_form():
    assert match_role("AI/ML Engineer") == "AI/ML Engineer"


def test_excludes_senior_without_entry_signal():
    assert match_role("Senior Data Scientist") is None


def test_allows_senior_titled_but_entry_level_signal():
    # "Associate" entry-level signal should override the senior/lead exclusion heuristic
    assert match_role("Associate Data Scientist") == "Associate Data Scientist"


def test_ignores_unrelated_software_engineer():
    assert match_role("Senior Software Engineer, Backend") is None


def test_ignores_devops():
    assert match_role("DevOps Engineer") is None


def test_matches_business_intelligence_engineer():
    assert match_role("Business Intelligence Engineer") == "Business Intelligence Engineer"


def test_matches_generative_ai_engineer():
    assert match_role("Generative AI Engineer - Early Career") == "Generative AI Engineer"
