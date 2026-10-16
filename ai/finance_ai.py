"""Natural-language finance analytics using local Ollama and read-only SQL."""
import requests
from sqlalchemy.exc import ProgrammingError

from config.config import (
    GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL, GROQ_TIMEOUT_SECONDS,
    LLM_PROVIDER, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS, OLLAMA_URL,
)
from db.connection import get_engine
from utils.query_executor import execute_read_query
from utils.query_validator import validate_sql, clean_sql
from utils.schema_validator import get_database_schema, build_schema_context, validate_columns
from utils.logger import logger

BUSINESS_RULES = """
Use only the available finance_ops reporting views and their discovered columns.
- Monthly revenue: vw_monthly_revenue; total revenue is SUM(total_revenue).
- Department expenses: vw_monthly_expenses; total expense is SUM(total_expense).
- Profit: vw_monthly_closing_summary.net_profit.
- Budget comparison: vw_budget_vs_actual; variance_amount and variance_pct.
- Daily cash flow: vw_daily_cash_summary; net_cash_flow.
- Forecast: vw_cash_forecast_30_days.
- DSO / DPO: vw_dso.dso / vw_dpo.dpo.
- Top overdue customers: vw_top_overdue_customers (customer_name, total_overdue).
- Top outstanding vendors: vw_top_outstanding_vendors (vendor_name, total_outstanding).
- Detailed aging: vw_receivables_aging and vw_payables_aging.
Use date-range filters on actual date columns; do not assume a year column exists.
"""

STRICT_RULES = """
Return exactly one PostgreSQL SELECT statement, with no markdown fences.
Use only schema-qualified finance_ops reporting views supplied in the schema.
Do not use CTEs, DML, DDL, system catalogs, unapproved tables, or side-effecting functions.
Every column must exist in the supplied schema. For ranking, include the entity and
metric, ORDER BY the metric in the requested direction, and LIMIT to the requested N.
"""


def _ollama_generate(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0},
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT_SECONDS)
        response.raise_for_status()
        generated = response.json().get("response", "").strip()
    except requests.RequestException as exc:
        raise RuntimeError(
            "Could not reach Ollama. Make sure Ollama is running and the configured model is installed."
        ) from exc
    except (ValueError, AttributeError) as exc:
        raise RuntimeError("Ollama returned an unexpected response.") from exc
    if not generated:
        raise RuntimeError("Ollama returned an empty SQL response.")
    return generated


def _groq_generate(prompt: str) -> str:
    """Generate text with Groq's OpenAI-compatible chat-completions API."""
    if not GROQ_API_KEY:
        raise RuntimeError(
            "LLM_PROVIDER is set to 'groq' but GROQ_API_KEY is missing from .env. "
            "Add your key locally, or set LLM_PROVIDER=ollama to use the local model."
        )
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You generate safe PostgreSQL read-only SQL. Return SQL only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_completion_tokens": 1200,
    }
    try:
        response = requests.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=GROQ_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        generated = response.json()["choices"][0]["message"]["content"].strip()
    except requests.RequestException as exc:
        # Never print the request headers or API key in the error message.
        raise RuntimeError(
            "Groq API request failed. Check internet access, API key, model ID, and free-tier limits."
        ) from exc
    except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        raise RuntimeError("Groq returned an unexpected or empty response.") from exc
    if not generated:
        raise RuntimeError("Groq returned an empty SQL response.")
    return generated


def _generate_with_configured_provider(prompt: str) -> str:
    provider = LLM_PROVIDER or "ollama"
    if provider == "groq":
        return _groq_generate(prompt)
    if provider == "ollama":
        return _ollama_generate(prompt)
    raise RuntimeError("Unsupported LLM_PROVIDER. Set it to 'groq' or 'ollama'.")


def generate_sql(user_question: str, schema_context: str) -> str:
    prompt = f"""You are a careful PostgreSQL finance data analyst.
Convert the user's question into one safe read-only SQL SELECT query.

AVAILABLE DATABASE SCHEMA:
{schema_context}

FINANCE BUSINESS RULES:
{BUSINESS_RULES}

SECURITY RULES:
{STRICT_RULES}

USER QUESTION:
{user_question}

Return SQL only."""
    return _generate_with_configured_provider(prompt)


def correct_sql(user_question: str, bad_sql: str, validation_error: str, schema_context: str) -> str:
    prompt = f"""Correct this invalid PostgreSQL finance query.
Return exactly one safe SELECT statement, no markdown.
Use only the schema-qualified finance_ops reporting views and columns below.
Do not use CTEs, DML/DDL, system catalogs, or side-effecting functions.

SCHEMA:
{schema_context}

USER QUESTION:
{user_question}

INVALID SQL:
{bad_sql}

VALIDATION ERROR:
{validation_error}

BUSINESS RULES:
{BUSINESS_RULES}

SECURITY RULES:
{STRICT_RULES}

Return SQL only."""
    return _generate_with_configured_provider(prompt)


def ask_finance_ai(question: str, engine=None):
    """Generate, validate, and execute one read-only finance query.

    Returns a dictionary with the raw pandas DataFrame and the validated SQL.
    """
    question = (question or "").strip()
    if not question:
        raise ValueError("Enter a finance question first.")
    if len(question) > 500:
        raise ValueError("Please keep the question under 500 characters.")

    engine = engine or get_engine()
    database_schema = get_database_schema(engine)
    schema_context = build_schema_context(database_schema)
    generated_sql = generate_sql(question, schema_context)

    last_error = None
    for attempt in range(3):
        cleaned_sql = clean_sql(generated_sql)
        try:
            validate_sql(cleaned_sql)
            validate_columns(cleaned_sql, database_schema)
            result = execute_read_query(cleaned_sql, engine)
            logger.info("AI finance query succeeded; returned %s rows", len(result))
            return {"data": result, "sql": cleaned_sql}
        except (ValueError, ProgrammingError) as exc:
            last_error = exc
            logger.warning("Generated SQL failed validation (attempt %s): %s", attempt + 1, exc)
            if attempt == 2:
                break
            generated_sql = correct_sql(question, cleaned_sql, str(exc), schema_context)

    raise ValueError(f"AI could not produce a safe query after 3 attempts: {last_error}")
