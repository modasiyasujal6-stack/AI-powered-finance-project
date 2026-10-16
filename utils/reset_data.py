"""Reset generated finance_ops data. This operation permanently deletes rows."""
from sqlalchemy import text
from db.connection import get_engine
from utils.logger import logger

RESET_QUERIES = [
    "TRUNCATE TABLE finance_ops.bank_transactions RESTART IDENTITY CASCADE",
    "TRUNCATE TABLE finance_ops.receivables RESTART IDENTITY CASCADE",
    "TRUNCATE TABLE finance_ops.payables RESTART IDENTITY CASCADE",
    "TRUNCATE TABLE finance_ops.sales_transactions RESTART IDENTITY CASCADE",
    "TRUNCATE TABLE finance_ops.expense_entries RESTART IDENTITY CASCADE",
    "TRUNCATE TABLE finance_ops.budget RESTART IDENTITY CASCADE",
    "TRUNCATE TABLE finance_ops.customers RESTART IDENTITY CASCADE",
    "TRUNCATE TABLE finance_ops.vendors RESTART IDENTITY CASCADE",
    "TRUNCATE TABLE finance_ops.accounts_master RESTART IDENTITY CASCADE",
]


def reset_finance_ops_data(engine=None):
    """Delete generated rows and restart identities; call only after explicit confirmation."""
    engine = engine or get_engine()
    with engine.begin() as conn:
        for query in RESET_QUERIES:
            conn.execute(text(query))
    logger.warning("finance_ops generated data was reset")
    print("finance_ops generated data reset successfully.")
