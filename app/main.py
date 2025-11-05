"""
AI Security Analyst Assistant — FastAPI entry point (revised for schema/debug)

Why this revision?
- Ensures fully qualified imports (app.*) so uvicorn reload never grabs stale modules.
- Adds startup diagnostics to confirm the *actual* AnalyzeRequest being imported,
  including its fields (so you can verify 'inputs' is present).
- Verifies prompt file existence and initializes the SQLite DB.

Run (PowerShell):
    $env:OPENAI_API_KEY="sk-..."    # set before launching
    $env:OPENAI_MODEL="gpt-3.5-turbo"
    python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"""
from dotenv import load_dotenv
load_dotenv()


#from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Fully-qualified imports so module resolution is stable under uvicorn
from app.route.analyze_route import router as analyze_router
from app.route.auth_route import router as auth_router
from app.data.db_config import init_db

APP_ROOT = Path(__file__).resolve().parent
PROMPTS_DIR = APP_ROOT / "prompts"
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system_prompt.txt"
DATA_DIR = APP_ROOT / "data"

DEFAULT_CORS_ORIGINS: List[str] = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Security Analyst Assistant API",
        version="0.3.0",
        description="Prompt-only security analysis service (no RAG, no fine-tuning).",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS for local dev UIs
    app.add_middleware(
        CORSMiddleware,
        allow_origins=DEFAULT_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(analyze_router)
    app.include_router(auth_router)

    @app.get("/", tags=["root"])
    def root():
        return {
            "service": "AI Security Analyst Assistant",
            "status": "ok",
            "docs": "/docs",
        }

    @app.on_event("startup")
    def _startup():
        # Basic logging setup once
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

        # Ensure directories exist
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize DB (creates tables if missing)
        try:
            init_db()
            logging.info("SQLite initialized at: %s", (DATA_DIR / "app.db"))
        except Exception as ex:
            logging.warning("DB init warning: %s: %s", type(ex).__name__, ex)

        # Prompt presence check
        if not SYSTEM_PROMPT_PATH.exists():
            logging.warning(
                "System prompt not found at %s. Create this file and paste your spec.",
                SYSTEM_PROMPT_PATH,
            )
        else:
            logging.info("Found system prompt at %s", SYSTEM_PROMPT_PATH)

        # --- Schema diagnostics (helps catch stale imports) ---
        try:
            from app.schemas import analyze_schema as _schema  # local import to reflect runtime state
            fields = list(_schema.AnalyzeRequest.model_fields.keys())
            logging.info(
                "Loaded AnalyzeRequest from: %s | fields=%s",
                getattr(_schema, "__file__", "unknown"),
                fields,
            )
            # Optional sanity: assert the 'inputs' field is present
            if "inputs" not in fields:
                logging.warning(
                    "AnalyzeRequest.inputs is NOT present. "
                    "Ensure you're editing app/schemas/analyze_schema.py and reload."
                )
        except Exception as ex:
            logging.warning("Schema import warning: %s: %s", type(ex).__name__, ex)

    return app


# App instance for uvicorn
app = create_app()

# Allow direct `python app/main.py` execution (optional; uvicorn -m is preferred)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
