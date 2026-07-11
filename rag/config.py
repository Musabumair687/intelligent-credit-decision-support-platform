"""
config.py

Central configuration for the Intelligent Credit Decision Support Platform.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

# ---------------------------------------------------------
# Project Root
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------
# Load Environment Variables
# ---------------------------------------------------------

load_dotenv(PROJECT_ROOT / ".env", override=True)

# ---------------------------------------------------------
# API Keys
# ---------------------------------------------------------

# Google Gemini (Embeddings)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Groq (LLM)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ---------------------------------------------------------
# Models
# ---------------------------------------------------------

LLM_MODEL = os.getenv("LLM_MODEL")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

# ---------------------------------------------------------
# Project Paths
# ---------------------------------------------------------

DOCUMENT_PATH = PROJECT_ROOT / "docs" / "raw"

VECTOR_DB_PATH = PROJECT_ROOT / "vector_db"

# ---------------------------------------------------------
# Chroma
# ---------------------------------------------------------

COLLECTION_NAME = "credit_policy"

# ---------------------------------------------------------
# Retrieval Defaults
# ---------------------------------------------------------

TOP_K = 5

SEARCH_TYPE = "rrf_retriever"

# ---------------------------------------------------------
# Test
# ---------------------------------------------------------

if __name__ == "__main__":

    print("=" * 60)
    print("PROJECT CONFIGURATION")
    print("=" * 60)

    print("PROJECT_ROOT      :", PROJECT_ROOT)
    print("DOCUMENT_PATH     :", DOCUMENT_PATH)
    print("VECTOR_DB_PATH    :", VECTOR_DB_PATH)

    print()

    print("GOOGLE_API_KEY    :", GOOGLE_API_KEY)
    print("GROQ_API_KEY      :", GROQ_API_KEY)

    print()

    print("LLM_MODEL         :", LLM_MODEL)
    print("EMBEDDING_MODEL   :", EMBEDDING_MODEL)

    print()

    print("COLLECTION_NAME   :", COLLECTION_NAME)
    print("TOP_K             :", TOP_K)
    print("SEARCH_TYPE       :", SEARCH_TYPE)