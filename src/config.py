"""Application configuration.

Loads settings from environment variables (via .env file) with sensible defaults.
All paths are resolved relative to the project root.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# --- LLM Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
GEMINI_API_KEY = GOOGLE_API_KEY
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "gemini").lower()
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.6-flash")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", MODEL_NAME)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

GENERATOR_TEMPERATURE = float(os.getenv("TEMPERATURE", "0.4"))
EVALUATOR_TEMPERATURE = float(os.getenv("EVAL_TEMPERATURE", "0.0"))

# --- Pipeline Configuration ---
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
MAX_MEMORY_INSTRUCTIONS = int(os.getenv("MAX_MEMORY_INSTRUCTIONS", "10"))

# --- Learner Profile ---
LEARNER_PROFILE = (
    "A 12th-grade graduate from India with limited English vocabulary "
    "and a non-English-medium educational background. They have zero "
    "prior knowledge of AI, machine learning, or programming. They want "
    "to kickstart a career in AI and need concepts explained in simple, "
    "everyday language with relatable analogies."
)

# --- Paths ---
DATA_DIR = PROJECT_ROOT / "data"
MEMORY_DB_PATH = DATA_DIR / "memory.db"
RUNS_DIR = DATA_DIR / "runs"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class Config:
    """Namespace for accessing configuration settings."""

    ROOT_DIR = PROJECT_ROOT
    DATA_DIR = DATA_DIR
    OUTPUT_DIR = OUTPUT_DIR
    DATABASE_PATH = MEMORY_DB_PATH
    RUNS_DIR = RUNS_DIR

    GEMINI_API_KEY = GEMINI_API_KEY
    GOOGLE_API_KEY = GOOGLE_API_KEY
    OPENAI_API_KEY = OPENAI_API_KEY

    DEFAULT_PROVIDER = DEFAULT_PROVIDER
    GEMINI_MODEL = GEMINI_MODEL
    OPENAI_MODEL = OPENAI_MODEL

    DEFAULT_MAX_RETRIES = MAX_RETRIES
    GENERATOR_TEMPERATURE = GENERATOR_TEMPERATURE
    EVALUATOR_TEMPERATURE = EVALUATOR_TEMPERATURE
    DEFAULT_LEARNER_PROFILE = LEARNER_PROFILE

    @classmethod
    def ensure_directories(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_api_key(cls, provider: str = None) -> str:
        prov = (provider or cls.DEFAULT_PROVIDER).lower()
        if prov in ["gemini", "google"]:
            return cls.GEMINI_API_KEY
        elif prov == "openai":
            return cls.OPENAI_API_KEY
        return ""
