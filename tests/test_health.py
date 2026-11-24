import os
import unittest
from unittest.mock import patch

import pymysql
from fastapi import HTTPException

from app.main import connect, health, health_db


class HealthTests(unittest.TestCase):
    def test_process_health(self):
        self.assertEqual(health(), {"status": "ok"})

    @patch.dict(os.environ, {"DB_HOST": "db.example", "DB_NAME": "steady", "DB_USER": "user", "DB_PASSWORD": "secret", "DB_SSL_CA": "/tmp/rds-ca.pem"})
    @patch("app.main.pymysql.connect")
    def test_rds_tls_verifies_certificate_and_hostname(self, mock_connect):
        connect()
        options = mock_connect.call_args.kwargs
        self.assertEqual(options["ssl_ca"], "/tmp/rds-ca.pem")
        self.assertTrue(options["ssl_verify_cert"])
        self.assertTrue(options["ssl_verify_identity"])

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
