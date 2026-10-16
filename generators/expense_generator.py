import random
from decimal import Decimal
from datetime import timedelta
from sqlalchemy import text

from db.connection import get_engine
from config.config import NUM_EXPENSES, START_DATE, END_DATE, DEPARTMENTS
from utils.helpers import random_date, choose_payable_status
from utils.logger import logger

def get_vendor_ids():
    engine = get_engine()
    query = text("SELECT vendor_id FROM finance_ops.vendors")
    with engine.connect() as conn:
        return [row[0] for row in conn.execute(query).fetchall()]

def get_vendor_terms():
    engine = get_engine()
    query = text("SELECT vendor_id, payment_terms FROM finance_ops.vendors")
    with engine.connect() as conn:
        return {row[0]: row[1] for row in conn.execute(query).fetchall()}

def generate_expenses_and_payables(n=NUM_EXPENSES):
    engine = get_engine()
    vendor_ids = get_vendor_ids()
    if not vendor_ids and n:
        raise RuntimeError("No vendors found. Generate master data before expenses.")
    vendor_terms = get_vendor_terms()

    expense_query = text("""
        INSERT INTO finance_ops.expense_entries
        (vendor_id, expense_date, department, expense_amount)
        VALUES (:vendor_id, :expense_date, :department, :expense_amount)
        RETURNING expense_id
    """)

    payable_query = text("""
        INSERT INTO finance_ops.payables
        (expense_id, vendor_id, bill_date, due_date, amount_due, amount_paid, status)
        VALUES (:expense_id, :vendor_id, :bill_date, :due_date, :amount_due, :amount_paid, :status)
    """)

    bank_query = text("""
        INSERT INTO finance_ops.bank_transactions
        (account_id, transaction_date, transaction_type, reference_type, reference_id, amount, description)
        VALUES (:account_id, :transaction_date, :transaction_type, :reference_type, :reference_id, :amount, :description)
    """)

    with engine.begin() as conn:
        for _ in range(n):
            vendor_id = random.choice(vendor_ids)
            expense_date = random_date(START_DATE, END_DATE)
            amount = Decimal(str(round(random.uniform(2000, 100000), 2)))
            department = random.choice(DEPARTMENTS)

            expense_result = conn.execute(expense_query, {
                "vendor_id": vendor_id,
                "expense_date": expense_date,
                "department": department,
                "expense_amount": amount
            })

            expense_id = expense_result.scalar_one()

            due_days = vendor_terms[vendor_id]
            due_date = expense_date + timedelta(days=due_days)

            payable_status = choose_payable_status()

            if payable_status == "paid":
                amount_paid = amount
            elif payable_status == "partial":
                amount_paid = Decimal(str(round(float(amount) * random.uniform(0.25, 0.75), 2)))
            else:
                amount_paid = Decimal("0.00")

            conn.execute(payable_query, {
                "expense_id": expense_id,
                "vendor_id": vendor_id,
                "bill_date": expense_date,
                "due_date": due_date,
                "amount_due": amount,
                "amount_paid": amount_paid,
                "status": payable_status
            })

            if amount_paid > 0:
                payment_date = expense_date + timedelta(days=random.randint(1, due_days + 15))
                conn.execute(bank_query, {
                    "account_id": random.choice([1, 2, 4]),
                    "transaction_date": payment_date,
                    "transaction_type": "outflow",
                    "reference_type": "payable",
                    "reference_id": expense_id,
                    "amount": amount_paid,
                    "description": f"Vendor payment for expense_id {expense_id}"
                })

    logger.info(f"Inserted {n} expenses + payables + outflows")