"""Run the end-to-end finance data generation, validation and reporting pipeline."""
import argparse
import time

from sqlalchemy import text
from db.connection import get_engine
from generators.master_data import load_master_data
from generators.sales_generator import generate_sales_and_receivables
from generators.expense_generator import generate_expenses_and_payables
from validations.validation_checks import run_validations
from utils.logger import logger
from utils.reset_data import reset_finance_ops_data
from reports.report_generator import generate_finance_report

MANAGED_TABLES = (
    "accounts_master", "customers", "vendors", "budget", "sales_transactions",
    "receivables", "expense_entries", "payables", "bank_transactions",
)


def ensure_managed_tables_empty(engine=None):
    """Prevent accidental append/rerun duplicates unless reset was explicitly chosen."""
    engine = engine or get_engine()
    populated = []
    with engine.connect() as conn:
        for table in MANAGED_TABLES:
            count = conn.execute(text(f"SELECT COUNT(*) FROM finance_ops.{table}")).scalar_one()
            if count:
                populated.append(f"{table}={count}")
    if populated:
        raise RuntimeError(
            "Pipeline stopped to protect existing data. These tables are not empty: "
            + ", ".join(populated)
            + ". If this is a disposable generated dataset and you intentionally want to replace it, "
              "rerun with --reset --confirm-reset. That option permanently deletes rows in the managed tables."
        )


def run_pipeline(reset=False):
    start_time = time.time()
    logger.info("Pipeline started; reset=%s", reset)
    print("Finance Operations Analytics pipeline started...")

    if reset:
        print("WARNING: resetting generated finance_ops data...")
        reset_finance_ops_data()
    else:
        ensure_managed_tables_empty()

    print("\n[1/4] Generating master data...")
    load_master_data()
    print("\n[2/4] Generating sales, receivables, expenses and payables...")
    generate_sales_and_receivables()
    generate_expenses_and_payables()

    print("\n[3/4] Running data-quality validations...")
    run_validations(raise_on_error=True)

    print("\n[4/4] Generating Excel report...")
    report_path = generate_finance_report()

    total_time = round(time.time() - start_time, 2)
    logger.info("Pipeline completed successfully in %s seconds", total_time)
    print(f"\nPipeline completed successfully in {total_time} seconds.")
    print(f"Excel report: {report_path}")
    return {"duration_seconds": total_time, "report_path": str(report_path)}


def main():
    parser = argparse.ArgumentParser(description="Generate and report on Finance Operations Analytics data.")
    parser.add_argument(
        "--reset", action="store_true",
        help="Permanently clear the generated finance_ops tables before generating a fresh dataset.",
    )
    parser.add_argument(
        "--confirm-reset", action="store_true",
        help="Required together with --reset to confirm that existing generated data may be deleted.",
    )
    args = parser.parse_args()
    if args.confirm_reset and not args.reset:
        parser.error("--confirm-reset can only be used with --reset.")
    if args.reset and not args.confirm_reset:
        parser.error("Reset is destructive. Add both --reset --confirm-reset only if you intend to delete existing generated data.")
    run_pipeline(reset=args.reset)


if __name__ == "__main__":
    main()
