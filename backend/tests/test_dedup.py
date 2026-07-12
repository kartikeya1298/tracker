from app.core.dedup import compute_dedup_hash


def test_same_external_id_same_hash():
    h1 = compute_dedup_hash("amazon", "12345", "Data Scientist", "Bangalore")
    h2 = compute_dedup_hash("amazon", "12345", "Data Scientist II", "Different City")
    assert h1 == h2  # external id is authoritative when present


def test_different_external_id_different_hash():
    h1 = compute_dedup_hash("amazon", "111", "Data Scientist", "Bangalore")
    h2 = compute_dedup_hash("amazon", "222", "Data Scientist", "Bangalore")
    assert h1 != h2


def test_fallback_hash_uses_title_and_location():
    h1 = compute_dedup_hash("acme", "", "Data Analyst", "Pune")
    h2 = compute_dedup_hash("acme", "", "data analyst", "pune")
    assert h1 == h2  # case-insensitive normalization


def test_fallback_hash_differs_by_location():
    h1 = compute_dedup_hash("acme", "", "Data Analyst", "Pune")
    h2 = compute_dedup_hash("acme", "", "Data Analyst", "Mumbai")
    assert h1 != h2
