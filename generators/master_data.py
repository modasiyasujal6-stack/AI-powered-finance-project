"""Create master data only when the target tables are empty."""
import random
from datetime import date
from faker import Faker
from sqlalchemy import text

from db.connection import get_engine
from config.config import NUM_CUSTOMERS, NUM_VENDORS, DEPARTMENTS, VENDOR_CATEGORIES, INDUSTRIES, START_DATE, END_DATE
from utils.logger import logger

fake = Faker("en_IN")


def _assert_master_tables_empty(conn):
    tables = ("accounts_master", "customers", "vendors", "budget")
    populated = []
    for table in tables:
        count = conn.execute(text(f"SELECT COUNT(*) FROM finance_ops.{table}")).scalar_one()
        if count:
            populated.append(f"{table}={count}")
    if populated:
        raise RuntimeError(
            "Master-data tables are not empty (" + ", ".join(populated) + "). "
            "Refusing to append duplicate seed data. Run the pipeline with its explicit reset option only if you intend to replace generated data."
        )


def build_budget_records():
    """Build one budget row per configured month and department."""
    return [
        {"department": department, "month": date(year, month, 1).isoformat(),
         "budget_amount": round(random.uniform(200000, 1500000), 2)}
        for year in range(START_DATE.year, END_DATE.year + 1)
        for month in range(1, 13)
        if START_DATE <= date(year, month, 1) <= END_DATE
        for department in DEPARTMENTS
    ]

def load_master_data():
    """Insert accounts, customers, vendors and monthly budgets atomically."""
    engine = get_engine()
    accounts = [
        {"account_name": "Main Bank Account", "account_type": "bank", "currency": "INR"},
        {"account_name": "Payroll Bank Account", "account_type": "bank", "currency": "INR"},
        {"account_name": "Petty Cash", "account_type": "cash", "currency": "INR"},
        {"account_name": "Corporate Credit Card", "account_type": "credit", "currency": "INR"},
        {"account_name": "Collections Account", "account_type": "bank", "currency": "INR"},
    ]
    customers = [
        {"customer_name": fake.company(), "industry": random.choice(INDUSTRIES),
         "credit_limit": round(random.uniform(50000, 500000), 2)}
        for _ in range(NUM_CUSTOMERS)
    ]
    vendors = [
        {"vendor_name": fake.company(), "category": random.choice(VENDOR_CATEGORIES),
         "payment_terms": random.choice([7, 15, 30, 45])}
        for _ in range(NUM_VENDORS)
    ]
    budgets = build_budget_records()

    with engine.begin() as conn:
        _assert_master_tables_empty(conn)
        conn.execute(text("""
            INSERT INTO finance_ops.accounts_master (account_name, account_type, currency)
            VALUES (:account_name, :account_type, :currency)
        """), accounts)
        conn.execute(text("""
            INSERT INTO finance_ops.customers (customer_name, industry, credit_limit)
            VALUES (:customer_name, :industry, :credit_limit)
        """), customers)
        conn.execute(text("""
            INSERT INTO finance_ops.vendors (vendor_name, category, payment_terms)
            VALUES (:vendor_name, :category, :payment_terms)
        """), vendors)
        conn.execute(text("""
            INSERT INTO finance_ops.budget (department, month, budget_amount)
            VALUES (:department, :month, :budget_amount)
        """), budgets)

    logger.info("Inserted %s accounts, %s customers, %s vendors and %s budgets",
                len(accounts), len(customers), len(vendors), len(budgets))
    print(f"Master data inserted: {len(accounts)} accounts, {len(customers)} customers, "
          f"{len(vendors)} vendors, {len(budgets)} budget rows.")
