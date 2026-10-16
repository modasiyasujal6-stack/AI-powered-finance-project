"""Central configuration loaded from environment variables / .env."""
from datetime import date
import os

from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()

# Prefer a complete URL when provided. Otherwise build it safely so special
# characters in credentials/database names are URL-encoded by SQLAlchemy.
_db_url = os.getenv("DATABASE_URL", "").strip()
if _db_url:
    DB_URL = _db_url
else:
    DB_URL = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "Finance_ops_&_cash_flow_intelligence"),
    )

NUM_ACCOUNTS = 5
NUM_CUSTOMERS = 200
NUM_VENDORS = 100
NUM_SALES = 5000
NUM_EXPENSES = 3000

START_DATE = date(2024, 1, 1)
END_DATE = date(2026, 12, 31)

DEPARTMENTS = ["Finance", "HR", "Operations", "Marketing", "Sales", "IT"]
VENDOR_CATEGORIES = ["Utilities", "Logistics", "Software", "Office Supplies", "Consulting", "Maintenance"]
INDUSTRIES = ["Retail", "Manufacturing", "Healthcare", "Technology", "Education", "FMCG"]
CURRENCIES = ["INR"]

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))

# AI provider can be "groq" (cloud API) or "ollama" (local model).
# Groq is opt-in so no data is sent to a cloud provider without configuration.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions").strip()
GROQ_TIMEOUT_SECONDS = int(os.getenv("GROQ_TIMEOUT_SECONDS", "45"))
