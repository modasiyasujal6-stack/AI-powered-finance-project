"""Defensive validation for AI-generated, read-only finance SQL.

This is a guardrail, not a substitute for using a PostgreSQL account that has
only SELECT privileges on the approved reporting views.
"""
import re

ALLOWED_SCHEMA = "finance_ops"
ALLOWED_VIEWS = {
    "vw_budget_vs_actual", "vw_cash_flow", "vw_cash_forecast_30_days",
    "vw_daily_cash_summary", "vw_dpo", "vw_dso",
    "vw_monthly_closing_summary", "vw_monthly_expenses", "vw_monthly_revenue",
    "vw_payables_aging", "vw_receivables_aging", "vw_running_cash_balance",
    "vw_top_outstanding_vendors", "vw_top_overdue_customers",
}

FORBIDDEN_WORDS = {
    "insert", "update", "delete", "drop", "alter", "truncate", "create",
    "grant", "revoke", "merge", "call", "copy", "execute", "prepare",
    "deallocate", "vacuum", "analyze", "refresh", "comment", "do", "set",
    "reset", "listen", "notify", "unlisten", "into",
}
ALLOWED_FUNCTIONS = {
    "sum", "avg", "count", "min", "max", "round", "coalesce", "nullif",
    "extract", "date_trunc", "date_part", "lower", "upper", "trim", "abs",
    "greatest", "least", "cast", "to_char", "substring", "length", "replace",
    "floor", "ceil", "ceiling", "percentile_cont", "row_number", "rank",
    "dense_rank", "lag", "lead", "first_value", "last_value", "string_agg",
    "array_agg", "json_agg", "bool_and", "bool_or", "nullif", "round",
    # SQL syntax constructs that use parentheses but are not callable functions.
    "in", "over", "filter",
}
FORBIDDEN_FUNCTIONS = {
    "pg_sleep", "pg_read_file", "pg_read_binary_file", "pg_ls_dir",
    "pg_stat_file", "set_config", "nextval", "setval", "lo_import",
    "lo_export", "dblink", "dblink_exec",
}


def clean_sql(query: str) -> str:
    """Remove common model markdown wrappers and one optional trailing ';'."""
    if not isinstance(query, str):
        raise ValueError("SQL query must be text.")
    query = query.strip()
    query = re.sub(r"^```(?:sql)?\s*", "", query, flags=re.IGNORECASE)
    query = re.sub(r"\s*```$", "", query)
    query = query.strip()
    if query.endswith(";"):
        query = query[:-1].strip()
    return query


def _remove_literals_and_comments(query: str) -> str:
    """Mask strings, quoted identifiers, and comments with a small SQL lexer.

    Dollar-quoted strings are rejected explicitly. This avoids treating text such
    as 'update -- not SQL' as an executable keyword or comment.
    """
    output = []
    i = 0
    length = len(query)
    while i < length:
        char = query[i]

        if char == "'":
            output.append("''")
            i += 1
            while i < length:
                if query[i] == "'":
                    if i + 1 < length and query[i + 1] == "'":
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            continue

        if char == '"':
            output.append('"identifier"')
            i += 1
            while i < length:
                if query[i] == '"':
                    if i + 1 < length and query[i + 1] == '"':
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            continue

        if char == "-" and i + 1 < length and query[i + 1] == "-":
            newline = query.find("\n", i + 2)
            if newline == -1:
                output.append(" ")
                break
            output.append("\n")
            i = newline + 1
            continue

        if char == "/" and i + 1 < length and query[i + 1] == "*":
            i += 2
            depth = 1
            while i < length and depth:
                if query.startswith("/*", i):
                    depth += 1
                    i += 2
                elif query.startswith("*/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            output.append(" ")
            continue

        if char == "$":
            match = re.match(r"\$[A-Za-z_0-9]*\$", query[i:])
            if match:
                raise ValueError("Dollar-quoted SQL is not allowed.")

        output.append(char)
        i += 1
    return "".join(output)


def validate_sql(query: str) -> bool:
    """Allow one SELECT over explicitly approved, schema-qualified views only."""
    query = clean_sql(query)
    if not query:
        raise ValueError("SQL query is empty.")
    safe_text = _remove_literals_and_comments(query)
    if ";" in safe_text:
        raise ValueError("Multiple SQL statements are not allowed.")
    lowered = safe_text.lower().strip()
    if not re.match(r"^select\b", lowered):
        raise ValueError("Only a single SELECT statement is allowed; CTEs are not accepted.")

    for word in FORBIDDEN_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            raise ValueError(f"Forbidden SQL operation detected: {word.upper()}")

    for function in FORBIDDEN_FUNCTIONS:
        if re.search(rf"\b{re.escape(function)}\s*\(", lowered):
            raise ValueError(f"Forbidden SQL function detected: {function}")

    # Only known analytical functions are accepted. This blocks untrusted
    # functions that can read files, sleep, access extensions, or have side effects.
    called_functions = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", lowered)
    for function in called_functions:
        if function not in ALLOWED_FUNCTIONS:
            raise ValueError(f"SQL function is not allow-listed: {function}")

    # Reject any FROM/JOIN relation that is not an approved, qualified view.
    relations = re.findall(
        r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\s*\.\s*[a-zA-Z_][a-zA-Z0-9_]*)?)",
        lowered,
    )
    if not relations:
        raise ValueError("Query must select from an approved finance reporting view.")

    for relation in relations:
        normalized = re.sub(r"\s+", "", relation)
        parts = normalized.split(".")
        if len(parts) != 2 or parts[0] != ALLOWED_SCHEMA:
            raise ValueError("Every table/view must be qualified as finance_ops.<approved_view>.")
        if parts[1] not in ALLOWED_VIEWS:
            raise ValueError(f"Unauthorized finance view: {parts[1]}")

    # Prevent direct system catalog / arbitrary function access.
    if re.search(r"\b(?:pg_catalog|information_schema)\s*\.", lowered):
        raise ValueError("System catalog access is not allowed.")
    if re.search(r"\b[a-zA-Z_][a-zA-Z0-9_]*\s*\.", lowered):
        # Dotted references are allowed only for finance_ops.<view> and its
        # column references (view.column); any other schema prefix is blocked.
        prefixes = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\.", lowered)
        allowed_prefixes = {"finance_ops"} | {r.split(".")[-1] for r in relations}
        if any(p not in allowed_prefixes for p in prefixes):
            raise ValueError("Query contains a disallowed qualified reference.")

    return True
