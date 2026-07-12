from app.core.ranking import compute_rank_score


def test_higher_reputation_scores_higher_all_else_equal():
    tier1 = compute_rank_score("Data Scientist", "google", resume_match_score=70)
    tier3 = compute_rank_score("Data Scientist", "genpact", resume_match_score=70)
    assert tier1 > tier3


def test_resume_match_influences_score():
    high_match = compute_rank_score("Data Scientist", "google", resume_match_score=95)
    low_match = compute_rank_score("Data Scientist", "google", resume_match_score=20)
    assert high_match > low_match


def test_missing_resume_match_still_produces_score():
    score = compute_rank_score("Data Scientist", "google", resume_match_score=None)
    assert 0 <= score <= 100
