"""
app/route/analyze_route.py

APIRouter for the AI Security Analyst Assistant.

Endpoints:
- GET  /health      -> health check & model info
- POST /analyze     -> prompt-only security analysis (JSON or Markdown)

This revision:
- Delegates non-HTTP logic to app/services/analyze_service.py
- Imports Pydantic models from app/schemas/analyze_schema.py
- Uses centralized DB init from app/data/db_config.py
"""

from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException
import os

# DB bootstrap
from app.data.db_config import init_db

# Shared request/response models
from app.schemas.analyze_schema import (
    AnalyzeRequest,
    AnalyzeResponseJSON,
    AnalyzeResponseMarkdown,
)

# Service layer: orchestration + helpers + model constants
from app.services.analyze_service import (
    run_analysis,
    try_parse_json,
    OPENAI_MODEL,
    ALLOWED_MODELS,
    PROMPT_PATH,
)

router = APIRouter(tags=["analysis"])


@router.get("/diag")
def diag():
    key = os.getenv("OPENAI_API_KEY")
    return {
        "model": OPENAI_MODEL,
        "api_key_present": bool(key),
        "api_key_length": len(key) if key else 0,
        "prompt_exists": PROMPT_PATH.exists(),
    }

@router.get("/health")
def health():
    """
    Basic health check. Ensures DB is initialized and reports prompt existence.
    """
    init_db()
    return {
        "status": "ok",
        "model": OPENAI_MODEL,
        "allowed_models": ALLOWED_MODELS,
        "prompt_exists": PROMPT_PATH.exists(),
    }


@router.post("/analyze", response_model=AnalyzeResponseJSON | AnalyzeResponseMarkdown)
def analyze(req: AnalyzeRequest):
    """
    Main analysis endpoint:
    - Delegates orchestration to the service layer.
    - Returns parsed JSON or raw Markdown per requested output_format.
    """
    assistant_text = run_analysis(req)

    if req.output_format == "json":
        ok, parsed, err = try_parse_json(assistant_text)
        if not ok or parsed is None:
            raise HTTPException(
                status_code=500,
                detail=f"Assistant returned invalid JSON. {err}",
            )
        return AnalyzeResponseJSON(data=parsed)

    # Markdown path
    return AnalyzeResponseMarkdown(markdown=assistant_text)
