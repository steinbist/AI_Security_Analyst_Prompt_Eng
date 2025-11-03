"""
app/services/analyze_service.py

Purpose
-------
Extracts all non-endpoint logic from the analyze route so the router only
does HTTP I/O and response shaping.

This module provides:
- load_system_prompt()         -> reads system prompt from app/prompts/system_prompt.txt
- build_user_instruction(req)  -> creates minimal user instruction wrapper
- call_openai(messages)        -> invokes OpenAI chat completion
- audit_save(...)              -> writes best-effort audit row to SQLite
- run_analysis(req)            -> orchestrates prompt build + OpenAI call (+ auditing)
- try_parse_json(text)         -> small helper to safely parse assistant JSON

Dependencies
------------
- Database helpers: app/data/db_config.py  (init_db, get_connection)
- Request models:   app/schemas/analyze_schema.py (AnalyzeRequest)
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.data.db_config import init_db, get_connection
from app.schemas.analyze_schema import AnalyzeRequest

# -------------------------------------------------------------------
# Paths and configuration
# -------------------------------------------------------------------
APP_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = APP_ROOT / "prompts" / "system_prompt.txt"

# Models available in your environment (as provided)
ALLOWED_MODELS = ['gpt-3.5-turbo', 'gpt-5-search-api-2025-10-14', 'gpt-audio-mini-2025-10-06']
DEFAULT_MODEL = 'gpt-3.5-turbo'
OPENAI_MODEL = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
if OPENAI_MODEL not in ALLOWED_MODELS:
    OPENAI_MODEL = DEFAULT_MODEL

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI client (adjust import if your SDK differs)
try:
    from openai import OpenAI  # type: ignore
    _openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    _openai_client = None


# -------------------------------------------------------------------
# Core helpers
# -------------------------------------------------------------------
def load_system_prompt() -> str:
    """
    Load the system prompt spec from disk.
    Raises FileNotFoundError if the prompt is missing.
    """
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"System prompt not found at {PROMPT_PATH}. "
            "Create app/prompts/system_prompt.txt and paste your spec."
        )
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_user_instruction(req: AnalyzeRequest) -> str:
    """
    Minimal wrapper to steer format/schema selection.
    Heavier structure lives inside the system prompt spec.
    """
    inputs = req.inputs or ["logs", "access_records", "policy_text"]
    time_window = req.time_window or "Not specified"

    if req.output_format == "json":
        return (
            f"Produce a {req.schema} JSON object strictly following the system JSON schema. "
            f"Context time_window: {time_window}. Inputs: {inputs}. "
            f"Analyze the following content:\n\n{req.input_text}"
        )
    else:
        return (
            "Produce a Markdown report using the system Markdown template. "
            f"Context time_window: {time_window}. Inputs: {inputs}. "
            f"Analyze the following content:\n\n{req.input_text}"
        )


def call_openai(messages: list[dict]) -> str:
    """
    Invokes OpenAI chat completions and returns assistant text.
    Raises RuntimeError with a helpful message if the client/key is unavailable.
    """
    if _openai_client is None or not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not configured or OpenAI client unavailable.")
    try:
        completion = _openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.2,
        )
        return completion.choices[0].message.content or ""
    except Exception as ex:
        raise RuntimeError(f"OpenAI call failed: {type(ex).__name__}: {ex}") from ex


def audit_save(
    model: str,
    output_format: str,
    schema: Optional[str],
    prompt_chars: int,
    input_text: str,
    response_text: str
) -> None:
    """
    Best-effort audit row into SQLite. Never raises outwardly.
    Matches the 'analyses' table defined in app/data/db_config.py.
    """
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO analyses
                    (created_at, model, output_format, schema, prompt_chars, input_preview, response_preview)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(timespec="seconds") + "Z",
                    model,
                    output_format,
                    schema,
                    prompt_chars,
                    input_text[:500],      # preview only
                    response_text[:1000],  # preview only
                ),
            )
            conn.commit()
    except Exception:
        # Swallow logging errors to avoid breaking main flow
        pass


def try_parse_json(text: str) -> tuple[bool, Optional[dict], Optional[str]]:
    """
    Safely attempt to parse assistant output as JSON.

    Returns:
        (True, parsed_dict, None) on success
        (False, None, error_message) on failure
    """
    try:
        parsed = json.loads(text)
        return True, parsed, None
    except json.JSONDecodeError as je:
        return False, None, f"Invalid JSON: {je}. Raw: {text[:500]}"


# -------------------------------------------------------------------
# Orchestration
# -------------------------------------------------------------------
def run_analysis(req: AnalyzeRequest) -> str:
    """
    High-level orchestrator used by the route layer.

    Flow:
        - Ensure DB exists
        - Load system prompt
        - Build user instruction
        - Call OpenAI
        - Audit (best-effort)
        - Return assistant_text (router decides how to shape response)

    Returns:
        assistant_text (str): caller may parse JSON if req.output_format == 'json'
    """
    # Ensure DB and prompt readiness
    init_db()
    system_prompt = load_system_prompt()
    user_instruction = build_user_instruction(req)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_instruction},
    ]

    assistant_text = call_openai(messages)

    # Audit best-effort
    audit_save(
        model=OPENAI_MODEL,
        output_format=req.output_format,
        schema=req.schema if req.output_format == "json" else None,
        prompt_chars=len(system_prompt) + len(user_instruction),
        input_text=req.input_text,
        response_text=assistant_text,
    )

    return assistant_text
