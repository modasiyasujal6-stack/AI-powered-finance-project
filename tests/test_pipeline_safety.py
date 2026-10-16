import unittest
from contextlib import contextmanager
from main import ensure_managed_tables_empty, MANAGED_TABLES


class FakeResult:
    def __init__(self, value):
        self.value = value
    def scalar_one(self):
        return self.value


class FakeConnection:
    def __init__(self, counts):
        self.counts = counts
    def execute(self, statement):
        sql = str(statement)
        for table, count in self.counts.items():
            if f"finance_ops.{table}" in sql:
                return FakeResult(count)
        return FakeResult(0)


class FakeEngine:
    def __init__(self, counts):
        self.conn = FakeConnection(counts)
    @contextmanager
    def connect(self):
        yield self.conn


class PipelineSafetyTests(unittest.TestCase):
    def test_empty_tables_allow_pipeline(self):
        engine = FakeEngine({table: 0 for table in MANAGED_TABLES})
        self.assertIsNone(ensure_managed_tables_empty(engine))

    def test_populated_tables_stop_pipeline(self):
        counts = {table: 0 for table in MANAGED_TABLES}
        counts["customers"] = 200
        with self.assertRaisesRegex(RuntimeError, "customers=200"):
            ensure_managed_tables_empty(FakeEngine(counts))


if __name__ == "__main__":
    unittest.main()
