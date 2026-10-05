"""Tests for Railway secret-to-file handling; no real credential is used."""

import base64
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from app.core.gcp_auth import _credential_file


DUMMY = {
    "type": "service_account",
    "project_id": "example-project",
    "client_email": "example@example.invalid",
    "private_key": "private-value-for-test-only",
}


class GoogleCredentialsTests(unittest.TestCase):
    def test_railway_json_value_becomes_private_file(self):
        with patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": json.dumps(DUMMY)}):
            path = _credential_file()
            try:
                self.assertEqual(os.environ["GOOGLE_APPLICATION_CREDENTIALS"], str(path))
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
                self.assertEqual(json.loads(path.read_text())["project_id"], "example-project")
                self.assertEqual(_credential_file(), path)
            finally:
                path.unlink(missing_ok=True)

    def test_base64_encoded_json_is_accepted(self):
        encoded = base64.b64encode(json.dumps(DUMMY).encode()).decode()
        with patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": encoded}):
            path = _credential_file()
            try:
                self.assertTrue(path.exists())
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            finally:
                path.unlink(missing_ok=True)

    def test_existing_file_is_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing.json"
            path.write_text(json.dumps(DUMMY))
            with patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": str(path)}):
                self.assertEqual(_credential_file(), path)

    def test_absent_or_invalid_credentials_return_503(self):
        for value in ("", "not-a-path-or-service-account", '{"type":"service_account"}'):
            with self.subTest(value=value[:10]), patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": value}):
                with self.assertRaises(HTTPException) as caught:
                    _credential_file()
                self.assertEqual(caught.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
