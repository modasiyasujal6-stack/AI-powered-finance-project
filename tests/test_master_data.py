import unittest
from generators.master_data import build_budget_records
from config.config import DEPARTMENTS


class MasterDataTests(unittest.TestCase):
    def test_budget_covers_configured_date_range_without_duplicate_periods(self):
        budgets = build_budget_records()
        self.assertEqual(len(budgets), 36 * len(DEPARTMENTS))
        periods = [(row["department"], row["month"]) for row in budgets]
        self.assertEqual(len(periods), len(set(periods)))
        self.assertIn((DEPARTMENTS[0], "2026-12-01"), periods)


if __name__ == "__main__":
    unittest.main()
