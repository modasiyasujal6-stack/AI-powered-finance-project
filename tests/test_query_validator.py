import unittest
from utils.query_validator import clean_sql, validate_sql


class QueryValidatorTests(unittest.TestCase):
    def test_accepts_approved_select(self):
        query = "SELECT SUM(total_revenue) AS total_revenue FROM finance_ops.vw_monthly_revenue WHERE month >= DATE '2025-01-01' AND month < DATE '2026-01-01'"
        self.assertTrue(validate_sql(query))

    def test_removes_markdown_fence(self):
        self.assertEqual(clean_sql("```sql\nSELECT * FROM finance_ops.vw_dso;\n```"), "SELECT * FROM finance_ops.vw_dso")

    def test_rejects_insert(self):
        with self.assertRaises(ValueError):
            validate_sql("INSERT INTO finance_ops.vw_monthly_revenue VALUES (1)")

    def test_rejects_multiple_statements(self):
        with self.assertRaises(ValueError):
            validate_sql("SELECT * FROM finance_ops.vw_dso; SELECT * FROM finance_ops.vw_dpo")

    def test_rejects_unapproved_view(self):
        with self.assertRaises(ValueError):
            validate_sql("SELECT * FROM finance_ops.customers")

    def test_rejects_unqualified_table(self):
        with self.assertRaises(ValueError):
            validate_sql("SELECT * FROM customers")

    def test_rejects_system_catalog(self):
        with self.assertRaises(ValueError):
            validate_sql("SELECT * FROM information_schema.tables JOIN finance_ops.vw_dso ON true")

    def test_rejects_side_effect_function(self):
        with self.assertRaises(ValueError):
            validate_sql("SELECT pg_sleep(5) FROM finance_ops.vw_dso")


    def test_rejects_unapproved_function(self):
        with self.assertRaises(ValueError):
            validate_sql("SELECT custom_extension_function(1) FROM finance_ops.vw_dso")


    def test_semicolon_and_keywords_inside_string_are_safe(self):
        self.assertTrue(validate_sql("SELECT 'update; drop -- text' AS note FROM finance_ops.vw_dso"))

    def test_rejects_dollar_quoted_sql(self):
        with self.assertRaises(ValueError):
            validate_sql("SELECT $$hello$$ AS note FROM finance_ops.vw_dso")

    def test_keyword_in_string_is_not_mistaken_for_dml(self):
        self.assertTrue(validate_sql("SELECT 'update customer' AS note FROM finance_ops.vw_dso"))


if __name__ == "__main__":
    unittest.main()
