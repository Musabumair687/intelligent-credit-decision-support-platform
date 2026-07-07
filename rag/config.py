from pathlib import Path
from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=True)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

if __name__ == "__main__":
    print("PROJECT_ROOT:", PROJECT_ROOT)
    print("GOOGLE_API_KEY:", GOOGLE_API_KEY)
    print("LLM_MODEL:", LLM_MODEL)
    print("EMBEDDING_MODEL:", EMBEDDING_MODEL)