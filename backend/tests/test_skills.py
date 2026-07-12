from app.ai.skills import extract_skills_keyword


def test_extracts_known_skills():
    text = "We use Python, SQL, and Power BI heavily along with Spark for ETL."
    skills = extract_skills_keyword(text)
    assert "Python" in skills
    assert "SQL" in skills
    assert "Power BI" in skills
    assert "Spark" in skills


def test_no_skills_in_empty_text():
    assert extract_skills_keyword("") == []
