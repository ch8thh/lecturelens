"""The ONE place the backend talks to Claude.

call_claude_json(...) sends text and/or images, asks for JSON only, validates the reply
against a Pydantic model, and retries once (telling Claude what was wrong) if the JSON
is invalid. Every failure is raised as AppError, which main.py turns into the
{"error": {"code", "message"}} response shape (ErrorResponse).
"""
import base64
import json
import logging
import re
from typing import TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from . import config

logger = logging.getLogger("lecturelens.claude")  # never log the key or full prompts

T = TypeVar("T", bound=BaseModel)


class AppError(Exception):
    """An error we want to send to the client as an ErrorResponse."""

    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    """Create the SDK client lazily so the server can start (and /api/health work)
    even before a key is configured."""
    global _client
    if not config.ANTHROPIC_API_KEY:
        raise AppError(
            500, "missing_api_key",
            "ANTHROPIC_API_KEY is not set. Add it to backend/.env and restart the server.",
        )
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def _extract_json(text: str) -> str:
    """Models sometimes wrap JSON in ```json fences or add a sentence. Grab the outermost {...}."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = text.find("{"), text.rfind("}")
    return text[start : end + 1] if start != -1 and end > start else text


def _json_instruction(result_model: type[BaseModel]) -> str:
    schema = json.dumps(result_model.model_json_schema())
    return (
        "\n\nRespond with ONLY a single valid JSON object - no markdown fences, no commentary "
        f"before or after it. It must conform exactly to this JSON Schema:\n{schema}"
    )


def call_claude_json(
    *,
    system: str,
    user_text: str,
    result_model: type[T],
    images: list[tuple[str, bytes]] | None = None,  # [(media_type, raw_bytes), ...]
    history: list[dict] | None = None,  # prior [{"role", "content": str}] turns
    max_tokens: int = 16000,
) -> T:
    client = _get_client()

    # The final user turn: images first, then the text (+ JSON instructions).
    content: list[dict] = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64.standard_b64encode(data).decode("ascii"),
            },
        }
        for media_type, data in (images or [])
    ]
    content.append({"type": "text", "text": user_text + _json_instruction(result_model)})
    messages: list[dict] = [*(history or []), {"role": "user", "content": content}]

    last_problem = ""
    for attempt in (1, 2):  # first try + one retry
        try:
            response = client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
        except anthropic.APIStatusError as e:
            logger.warning("Claude API status error %s", e.status_code)
            raise AppError(502, "claude_api_error",
                           f"The AI service returned an error (HTTP {e.status_code}).") from e
        except anthropic.APIConnectionError as e:  # includes timeouts
            logger.warning("Claude API connection error: %s", type(e).__name__)
            raise AppError(502, "claude_api_error", "Could not reach the AI service.") from e

        if response.stop_reason == "refusal":
            raise AppError(502, "claude_refused", "The AI declined to process this content.")

        text = "".join(b.text for b in response.content if b.type == "text")
        try:
            return result_model.model_validate_json(_extract_json(text))
        except ValidationError as e:  # also covers malformed JSON (json_invalid)
            last_problem = str(e)[:1500]
            logger.warning("Invalid AI response on attempt %d: %s", attempt, last_problem[:300])
            if response.stop_reason == "max_tokens":
                last_problem = "Your reply was cut off. Be more concise. " + last_problem
            # Retry: show Claude its bad answer and what was wrong with it.
            messages = [
                *messages,
                {"role": "assistant", "content": text or "{}"},
                {"role": "user", "content": (
                    "That was not valid. Problem:\n" + last_problem +
                    "\nReply again with ONLY the corrected JSON object.")},
            ]

    raise AppError(502, "invalid_ai_response",
                   "The AI returned a response in an unexpected format. Please try again.")
