"""Loads settings from backend/.env. This is the ONLY place the API key is read.

The key is never logged or returned in any response."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Resolve .env relative to this file so it works no matter where uvicorn is started from.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
# `or` (not a getenv default) so an empty "CLAUDE_MODEL=" line in .env still falls back.
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "").strip() or "claude-sonnet-5-5"
