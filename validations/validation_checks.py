"""Data-quality checks for the finance_ops generated dataset."""
from sqlalchemy import text
from db.connection import get_engine
from utils.logger import logger

CHECKS = {
    "customers_count": ("SELECT COUNT(*) FROM finance_ops.customers", "positive"),
    "vendors_count": ("SELECT COUNT(*) FROM finance_ops.vendors", "positive"),
    "sales_count": ("SELECT COUNT(*) FROM finance_ops.sales_transactions", "positive"),
    "receivables_count": ("SELECT COUNT(*) FROM finance_ops.receivables", "positive"),
    "expenses_count": ("SELECT COUNT(*) FROM finance_ops.expense_entries", "positive"),
    "payables_count": ("SELECT COUNT(*) FROM finance_ops.payables", "positive"),
    "bank_transactions_count": ("SELECT COUNT(*) FROM finance_ops.bank_transactions", "positive"),
    "invalid_receivables_amounts": ("""
        SELECT COUNT(*) FROM finance_ops.receivables
        WHERE amount_due < 0 OR amount_received < 0 OR amount_received > amount_due
    """, "zero"),
    "invalid_payables_amounts": ("""
        SELECT COUNT(*) FROM finance_ops.payables
        WHERE amount_due < 0 OR amount_paid < 0 OR amount_paid > amount_due
    """, "zero"),
    "duplicate_account_names": ("""
        SELECT COUNT(*) FROM (
            SELECT account_name FROM finance_ops.accounts_master
            GROUP BY account_name HAVING COUNT(*) > 1
        ) duplicates
    """, "zero"),
    "missing_sales_customer_links": ("""
        SELECT COUNT(*) FROM finance_ops.sales_transactions s
        LEFT JOIN finance_ops.customers c ON c.customer_id = s.customer_id
        WHERE c.customer_id IS NULL
    """, "zero"),
    "missing_expense_vendor_links": ("""
        SELECT COUNT(*) FROM finance_ops.expense_entries e
        LEFT JOIN finance_ops.vendors v ON v.vendor_id = e.vendor_id
        WHERE v.vendor_id IS NULL
    """, "zero"),
    "invalid_bank_account_links": ("""
        SELECT COUNT(*) FROM finance_ops.bank_transactions b
        LEFT JOIN finance_ops.accounts_master a ON a.account_id = b.account_id
        WHERE a.account_id IS NULL
    """, "zero"),
    "receivable_customer_mismatches": ("""
        SELECT COUNT(*) FROM finance_ops.receivables r
        JOIN finance_ops.sales_transactions s ON s.sale_id = r.sale_id
        WHERE r.customer_id <> s.customer_id
    """, "zero"),
    "payable_vendor_mismatches": ("""
        SELECT COUNT(*) FROM finance_ops.payables p
        JOIN finance_ops.expense_entries e ON e.expense_id = p.expense_id
        WHERE p.vendor_id <> e.vendor_id
    """, "zero"),
    "missing_sales_receivable_links": ("""
        SELECT COUNT(*) FROM finance_ops.sales_transactions s
        LEFT JOIN finance_ops.receivables r ON s.sale_id = r.sale_id
        WHERE r.sale_id IS NULL
    """, "zero"),
    "orphan_receivables": ("""
        SELECT COUNT(*) FROM finance_ops.receivables r
        LEFT JOIN finance_ops.sales_transactions s ON s.sale_id = r.sale_id
        WHERE s.sale_id IS NULL
    """, "zero"),
    "missing_expense_payable_links": ("""
        SELECT COUNT(*) FROM finance_ops.expense_entries e
        LEFT JOIN finance_ops.payables p ON e.expense_id = p.expense_id
        WHERE p.expense_id IS NULL
    """, "zero"),
    "orphan_payables": ("""
        SELECT COUNT(*) FROM finance_ops.payables p
        LEFT JOIN finance_ops.expense_entries e ON e.expense_id = p.expense_id
        WHERE e.expense_id IS NULL
    """, "zero"),
    "duplicate_budget_month_department": ("""
        SELECT COUNT(*) FROM (
            SELECT department, month FROM finance_ops.budget
            GROUP BY department, month HAVING COUNT(*) > 1
        ) duplicates
    """, "zero"),
    "invalid_bank_transaction_amounts": ("""
        SELECT COUNT(*) FROM finance_ops.bank_transactions WHERE amount < 0
    """, "zero"),
}


def run_validations(engine=None, raise_on_error=True):
    engine = engine or get_engine()
    results = {}
    failures = []
    with engine.connect() as conn:
        for name, (sql, rule) in CHECKS.items():
            value = int(conn.execute(text(sql)).scalar_one())
            passed = value > 0 if rule == "positive" else value == 0
            results[name] = {"value": value, "passed": passed, "rule": rule}
            status = "PASS" if passed else "FAIL"
            print(f"[{status}] {name}: {value}")
            if not passed:
                failures.append(name)
    if failures:
        logger.error("Data validation failed: %s", ", ".join(failures))
        if raise_on_error:
            raise RuntimeError("Data validation failed: " + ", ".join(failures))
    else:
        logger.info("All %s data validation checks passed", len(results))
    return results
