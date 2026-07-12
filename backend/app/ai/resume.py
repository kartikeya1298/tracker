import logging
import os

from app.config import get_settings

logger = logging.getLogger(__name__)


def load_resume_text() -> str:
    """Loads the candidate's resume as plain text from RESUME_TEXT_PATH.
    Supports .txt/.md directly; for .pdf/.docx, pre-convert to text and point
    resume_text_path at the .txt output (keeps this module dependency-free)."""
    settings = get_settings()
    path = settings.resume_text_path
    if not path or not os.path.exists(path):
        logger.info("No resume found at %s; resume matching will be skipped", path)
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        logger.exception("Failed to read resume at %s", path)
        return ""
