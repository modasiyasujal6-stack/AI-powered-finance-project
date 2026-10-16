"""Execute validated read-only SQL using a read-only transaction."""
import pandas as pd
from sqlalchemy import text
from utils.query_validator import validate_sql, clean_sql


def execute_read_query(query, engine):
    query = clean_sql(query)
    validate_sql(query)
    # PostgreSQL read-only transaction is an additional safety layer. Use a
    # transaction-scoped connection and always roll back after a successful read.
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            conn.execute(text("SET TRANSACTION READ ONLY"))
            result = pd.read_sql_query(text(query), conn)
            trans.rollback()
            return result
        except Exception:
            if trans.is_active:
                trans.rollback()
            raise
