"""Export finance reporting views to a formatted multi-sheet Excel workbook."""
from datetime import datetime
from copy import copy
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db.connection import get_engine
from utils.logger import logger

PROJECT_DIR = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_DIR / "reports" / "output"
REPORT_FILE = REPORT_DIR / "finance_operations_report.xlsx"

REPORT_QUERIES = {
    "Monthly Revenue": "SELECT * FROM finance_ops.vw_monthly_revenue ORDER BY month",
    "Monthly Expenses": "SELECT * FROM finance_ops.vw_monthly_expenses ORDER BY month, department",
    "Budget vs Actual": "SELECT * FROM finance_ops.vw_budget_vs_actual ORDER BY month, department",
    "Receivables Aging": "SELECT * FROM finance_ops.vw_receivables_aging ORDER BY due_date",
    "Payables Aging": "SELECT * FROM finance_ops.vw_payables_aging ORDER BY due_date",
    "Cash Flow": "SELECT * FROM finance_ops.vw_cash_flow ORDER BY transaction_date",
}


def _format_worksheet(worksheet):
    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    for cell in worksheet[1]:
        font = copy(cell.font)
        font.bold = True
        cell.font = font
    for column_cells in worksheet.columns:
        letter = column_cells[0].column_letter
        max_len = max((len(str(cell.value)) if cell.value is not None else 0) for cell in column_cells[:200])
        worksheet.column_dimensions[letter].width = min(max(max_len + 2, 12), 34)


def generate_finance_report(engine=None, report_file=None):
    engine = engine or get_engine()
    output_file = Path(report_file) if report_file else REPORT_FILE
    output_file.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Finance report generation started")

    try:
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            for sheet_name, query in REPORT_QUERIES.items():
                with engine.connect() as conn:
                    df = pd.read_sql_query(text(query), conn)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                _format_worksheet(writer.sheets[sheet_name])
                print(f"{sheet_name}: {len(df):,} rows exported")

            info = pd.DataFrame({
                "Generated At": [datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")],
                "Report Sheets": [len(REPORT_QUERIES)],
                "Source": ["PostgreSQL finance_ops reporting views"],
            })
            info.to_excel(writer, sheet_name="Report Info", index=False)
            _format_worksheet(writer.sheets["Report Info"])

        logger.info("Finance report generated: %s", output_file)
        print(f"\nReport generated successfully: {output_file}")
        return output_file
    except Exception:
        logger.exception("Finance report generation failed")
        raise


if __name__ == "__main__":
    generate_finance_report()
