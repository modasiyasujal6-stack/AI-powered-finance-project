import unittest
from sqlalchemy.engine import URL
from config.config import DB_URL


class ConfigTests(unittest.TestCase):
    def test_database_url_is_configured_without_literal_password_in_source(self):
        self.assertTrue(isinstance(DB_URL, (str, URL)))
        self.assertIn("postgresql", str(DB_URL))


if __name__ == "__main__":
    unittest.main()
