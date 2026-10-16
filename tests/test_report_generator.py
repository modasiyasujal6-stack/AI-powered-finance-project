import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from reports.report_generator import generate_finance_report, REPORT_QUERIES


class FakeConnection:
    pass

class FakeEngine:
    @contextmanager
    def connect(self):
        yield FakeConnection()


class ReportGeneratorTests(unittest.TestCase):
    def test_generates_workbook_with_expected_sheets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "test_report.xlsx"
            with patch("reports.report_generator.pd.read_sql_query", return_value=pd.DataFrame({"metric": [1, 2]})):
                result = generate_finance_report(engine=FakeEngine(), report_file=output)
            self.assertEqual(Path(result), output)
            self.assertTrue(output.exists())
            # Close the workbook explicitly so Windows can remove the temp folder.
            with pd.ExcelFile(output) as workbook:
                self.assertEqual(set(workbook.sheet_names), set(REPORT_QUERIES) | {"Report Info"})
                self.assertEqual(len(workbook.sheet_names), len(REPORT_QUERIES) + 1)


if __name__ == "__main__":
    unittest.main()
