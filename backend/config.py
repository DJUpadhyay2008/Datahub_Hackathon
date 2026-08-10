# ==============================================================================
# FILE: backend/config.py
# WHY THIS FILE EXISTS:
#   Centralizes application settings, environment variables, and default configuration parameters.
# WHAT IT DOES:
#   1. Reads configuration settings for DataHub GMS, PostgreSQL, Gemini API, and llama.cpp.
#   2. Configured to automatically target the local llama-server running Gemma 4 E2B on http://localhost:8080/v1.
# HOW IT INTERACTS WITH DATAHUB:
#   Provides the base URL and API keys needed by `datahub_client.py` and `ai_grounding.py`.
# ==============================================================================

import os
from pydantic import BaseModel

class Settings(BaseModel):
    # DataHub Metadata Service Settings (Runs on 8080 if Docker GMS is enabled, or fallback GMS)
    DATAHUB_GMS_URL: str = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080")
    
    # LLM Settings (Defaults to active local llama-server Gemma 4 E2B model)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "llama_cpp")  # Options: "llama_cpp", "gemini"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    LLAMA_CPP_URL: str = os.getenv("LLAMA_CPP_URL", "http://localhost:8080/v1")  # Active local llama-server port
    LLAMA_CPP_MODEL: str = os.getenv("LLAMA_CPP_MODEL", "gemma-4-E2B-it-UD-Q4_K_XL.gguf")

    # PostgreSQL Demo DB Connection
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5433"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ecommerce_db")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "demo_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "demo_password")

settings = Settings()
