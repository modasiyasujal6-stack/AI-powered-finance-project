import unittest
from utils.schema_validator import validate_columns


class SchemaValidatorTests(unittest.TestCase):
    def setUp(self):
        self.schema = {
            "vw_monthly_revenue": ["month", "invoice_amount", "tax_amount", "total_revenue"],
            "vw_top_overdue_customers": ["customer_name", "total_overdue"],
            "vw_dso": ["month", "avg_receivable", "total_credit_sales", "dso"],
        }

    def test_accepts_known_columns(self):
        query = "SELECT SUM(total_revenue) AS revenue_2025 FROM finance_ops.vw_monthly_revenue WHERE month >= DATE '2025-01-01'"
        self.assertTrue(validate_columns(query, self.schema))


    def test_accepts_date_trunc_and_extract(self):
        query = "SELECT EXTRACT(YEAR FROM month) AS fiscal_year, DATE_TRUNC('month', month) AS month_start FROM finance_ops.vw_monthly_revenue"
        self.assertTrue(validate_columns(query, self.schema))

    def test_rejects_unknown_view(self):
        with self.assertRaises(ValueError):
            validate_columns("SELECT amount FROM finance_ops.vw_unknown", self.schema)

    def test_rejects_unknown_identifier(self):
        with self.assertRaises(ValueError):
            validate_columns("SELECT year FROM finance_ops.vw_monthly_revenue", self.schema)

    def test_accepts_ranking_query(self):
        query = "SELECT customer_name, total_overdue FROM finance_ops.vw_top_overdue_customers ORDER BY total_overdue DESC LIMIT 5"
        self.assertTrue(validate_columns(query, self.schema))


if __name__ == "__main__":
    unittest.main()
