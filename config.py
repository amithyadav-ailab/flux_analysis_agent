import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv:
    load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
PORT = int(os.getenv("PORT", "8000"))
LLM_ENABLED = bool(OPENAI_API_KEY)
DEFAULT_THRESHOLD_PERCENT = float(os.getenv("DEFAULT_THRESHOLD_PERCENT", "0"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")