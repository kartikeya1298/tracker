import hashlib


def compute_dedup_hash(company_slug: str, external_id: str, title: str, location: str) -> str:
    """Stable hash for deduplication. Prefers the ATS's own external job id when available,
    falling back to a normalized title+location composite for platforms without stable ids."""
    if external_id:
        basis = f"{company_slug}:{external_id}"
    else:
        basis = f"{company_slug}:{title.strip().lower()}:{location.strip().lower()}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()
