import random
from decimal import Decimal
from datetime import timedelta
from sqlalchemy import text

from db.connection import get_engine
from config.config import NUM_SALES, START_DATE, END_DATE
from utils.helpers import random_date, calculate_tax
from utils.logger import logger

def get_customer_ids():
    engine = get_engine()
    query = text("SELECT customer_id FROM finance_ops.customers")
    with engine.connect() as conn:
        return [row[0] for row in conn.execute(query).fetchall()]

def generate_sales_and_receivables(n=NUM_SALES):
    engine = get_engine()
    customer_ids = get_customer_ids()
    if not customer_ids and n:
        raise RuntimeError("No customers found. Generate master data before sales.")

    sales_query = text("""
        INSERT INTO finance_ops.sales_transactions
        (customer_id, sale_date, invoice_amount, tax_amount, total_amount, status)
        VALUES (:customer_id, :sale_date, :invoice_amount, :tax_amount, :total_amount, :status)
        RETURNING sale_id
    """)

    receivable_query = text("""
        INSERT INTO finance_ops.receivables
        (sale_id, customer_id, invoice_date, due_date, amount_due, amount_received, status)
        VALUES (:sale_id, :customer_id, :invoice_date, :due_date, :amount_due, :amount_received, :status)
    """)

    bank_query = text("""
        INSERT INTO finance_ops.bank_transactions
        (account_id, transaction_date, transaction_type, reference_type, reference_id, amount, description)
        VALUES (:account_id, :transaction_date, :transaction_type, :reference_type, :reference_id, :amount, :description)
    """)

    with engine.begin() as conn:
        for _ in range(n):
            sale_date = random_date(START_DATE, END_DATE)
        
            base_amount = Decimal(str(round(random.uniform(5000, 150000), 2)))
            tax = calculate_tax(base_amount)
            total = (base_amount + tax).quantize(Decimal("0.01"))
        
            customer_id = random.choice(customer_ids)
        
            due_days = random.choice([15, 30, 45])
            due_date = sale_date + timedelta(days=due_days)
        
            behavior = random.choices(
                ["early", "on_time", "slight_delay", "late", "unpaid"],
                weights=[20, 30, 20, 15, 15],
                k=1
            )[0]
        
            if behavior == "early":
                payment_date = due_date - timedelta(days=random.randint(1, 10))
                amount_received = total
                sale_status = "paid"
                receivable_status = "closed"
            
            elif behavior == "on_time":
                payment_date = due_date
                amount_received = total
                sale_status = "paid"
                receivable_status = "closed"
            
            elif behavior == "slight_delay":
                payment_date = due_date + timedelta(days=random.randint(1, 30))
                amount_received = total
                sale_status = "paid"
                receivable_status = "closed"
            
            elif behavior == "late":
                payment_date = due_date + timedelta(days=random.randint(31, 90))
                amount_received = Decimal(str(round(float(total) * random.uniform(0.4, 0.8), 2)))
                sale_status = "generated"
                receivable_status = "partial"
            
            else:  # unpaid
                payment_date = None
                amount_received = Decimal("0.00")
                sale_status = "generated"
                receivable_status = "pending"
        
            sale_result = conn.execute(sales_query, {
                "customer_id": customer_id,
                "sale_date": sale_date,
                "invoice_amount": base_amount,
                "tax_amount": tax,
                "total_amount": total,
                "status": sale_status
            })
        
            sale_id = sale_result.scalar_one()
        
            conn.execute(receivable_query, {
                "sale_id": sale_id,
                "customer_id": customer_id,
                "invoice_date": sale_date,
                "due_date": due_date,
                "amount_due": total,
                "amount_received": amount_received,
                "status": receivable_status
            })
        
            if amount_received > 0 and payment_date is not None:
                conn.execute(bank_query, {
                    "account_id": random.choice([1, 2, 5]),
                    "transaction_date": payment_date,
                    "transaction_type": "inflow",
                    "reference_type": "receivable",
                    "reference_id": sale_id,
                    "amount": amount_received,
                    "description": f"Customer payment {sale_id}"
                })

    logger.info(f"Inserted {n} sales + receivables + inflows")