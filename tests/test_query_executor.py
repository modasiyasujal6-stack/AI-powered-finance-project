import unittest
from contextlib import contextmanager
from unittest.mock import patch
import pandas as pd
from utils.query_executor import execute_read_query


class FakeTransaction:
    def __init__(self):
        self.is_active = True
        self.rolled_back = False
    def rollback(self):
        self.rolled_back = True
        self.is_active = False

class FakeConnection:
    def __init__(self):
        self.transaction = FakeTransaction()
        self.statements = []
    def begin(self):
        return self.transaction
    def execute(self, statement):
        self.statements.append(str(statement))
        return None

class FakeEngine:
    def __init__(self):
        self.connection = FakeConnection()
    @contextmanager
    def connect(self):
        yield self.connection


class QueryExecutorTests(unittest.TestCase):
    def test_sets_read_only_and_rolls_back(self):
        engine = FakeEngine()
        expected = pd.DataFrame({"dso": [12.5]})
        with patch("utils.query_executor.pd.read_sql_query", return_value=expected):
            result = execute_read_query("SELECT dso FROM finance_ops.vw_dso", engine)
        self.assertTrue(result.equals(expected))
        self.assertIn("SET TRANSACTION READ ONLY", engine.connection.statements[0])
        self.assertTrue(engine.connection.transaction.rolled_back)

    def test_rejects_unsafe_query_before_connection(self):
        engine = FakeEngine()
        with self.assertRaises(ValueError):
            execute_read_query("DELETE FROM finance_ops.vw_dso", engine)
        self.assertEqual(engine.connection.statements, [])


if __name__ == "__main__":
    unittest.main()
