import os
import unittest
from unittest.mock import patch

import pymysql
from fastapi import HTTPException

from app.main import health, health_db


class HealthTests(unittest.TestCase):
    def test_process_health(self):
        self.assertEqual(health(), {"status": "ok"})

    @patch.dict(os.environ, {"DB_HOST": "localhost", "DB_NAME": "steady", "DB_USER": "user", "DB_PASSWORD": "secret"})
    @patch("app.main.pymysql.connect")
    def test_database_health_runs_query(self, connect):
        cursor = connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        self.assertEqual(health_db(), {"status": "ok"})
        cursor.execute.assert_called_once_with("SELECT 1")

    @patch.dict(os.environ, {"DB_HOST": "localhost", "DB_NAME": "steady", "DB_USER": "user", "DB_PASSWORD": "secret"})
    @patch("app.main.pymysql.connect", side_effect=pymysql.OperationalError("secret"))
    def test_database_failure_is_safe(self, connect):
        with self.assertRaises(HTTPException) as caught:
            health_db()
        self.assertEqual(caught.exception.status_code, 503)
        self.assertEqual(caught.exception.detail, "Database tidak tersedia")


if __name__ == "__main__":
    unittest.main()
