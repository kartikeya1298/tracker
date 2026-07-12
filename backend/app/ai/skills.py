import re

# Deterministic fallback skill extraction (used when AI is disabled, and as a safety net
# to merge with AI-extracted skills so we never under-report obvious keyword matches).
KNOWN_SKILLS = [
    "Python", "R", "SQL", "NoSQL", "Excel", "Power BI", "Tableau", "Looker",
    "Spark", "PySpark", "Hadoop", "Kafka", "Airflow", "dbt", "Snowflake", "BigQuery",
    "Redshift", "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas", "NumPy",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Generative AI",
    "LLM", "MLOps", "Statistics", "A/B Testing", "Data Visualization", "ETL",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "Java", "Scala",
    "Data Warehousing", "Data Modeling", "Hypothesis Testing", "Regression",
    "Time Series", "Clustering", "Deep Learning", "Reinforcement Learning",
]

_PATTERNS = [(skill, re.compile(rf"\b{re.escape(skill)}\b", re.IGNORECASE)) for skill in KNOWN_SKILLS]


def extract_skills_keyword(text: str) -> list[str]:
    if not text:
        return []
    found = []
    for skill, pattern in _PATTERNS:
        if pattern.search(text):
            found.append(skill)
    return found
