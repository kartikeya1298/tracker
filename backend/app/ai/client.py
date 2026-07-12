import json
import logging

from anthropic import AsyncAnthropic

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncAnthropic | None = None


def get_client() -> AsyncAnthropic | None:
    global _client
    settings = get_settings()
    if not settings.anthropic_api_key:
        return None
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


async def ask_json(prompt: str, max_tokens: int = 1024) -> dict | None:
    """Send a prompt to Claude and parse a JSON object from the response.
    Returns None if AI is disabled (no API key) or the call/parse fails, so
    callers can fall back to non-AI defaults rather than breaking the pipeline."""
    settings = get_settings()
    if not settings.ai_features_enabled:
        return None
    client = get_client()
    if client is None:
        logger.info("Anthropic API key not configured; skipping AI enrichment")
        return None

    try:
        response = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            logger.warning("No JSON object found in AI response")
            return None
        return json.loads(text[start : end + 1])
    except Exception:
        logger.exception("AI request failed")
        return None
