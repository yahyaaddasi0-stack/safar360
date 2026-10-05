"""Resolve a Railway-provided service account through GOOGLE_APPLICATION_CREDENTIALS.

Google Cloud's Python SDK expects a file path. Railway stores secrets as environment
values, so a JSON or base64-encoded JSON in that *same* variable is materialized
as a private 0600 file. No credential contents are logged or committed.
"""

import base64
import json
import os
import tempfile
from pathlib import Path

from fastapi import HTTPException
from google.oauth2 import service_account


CREDENTIALS_ENV = "GOOGLE_APPLICATION_CREDENTIALS"


def _missing_credentials() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail="Google Cloud service-account credentials unavailable; configure GOOGLE_APPLICATION_CREDENTIALS",
    )


def _credential_file() -> Path:
    raw = os.environ.get(CREDENTIALS_ENV, "").strip()
    if not raw:
        raise _missing_credentials()

    # A JSON value must be handled before Path(): a long JSON value raises ENAMETOOLONG.
    if raw.startswith("{"):
        serialized = raw
    else:
        try:
            supplied_path = Path(raw)
            if supplied_path.is_file():
                return supplied_path
        except (OSError, ValueError):
            pass
        try:
            serialized = base64.b64decode(raw, validate=True).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            raise _missing_credentials() from None

    try:
        payload = json.loads(serialized)
        if not isinstance(payload, dict) or payload.get("type") != "service_account":
            raise ValueError("Expected a service account")
        if not all(payload.get(key) for key in ("project_id", "private_key", "client_email")):
            raise ValueError("Incomplete service account")
    except (ValueError, TypeError):
        raise _missing_credentials() from None

    fd, path = tempfile.mkstemp(prefix="safar360-gcp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(payload, output, ensure_ascii=False)
        os.chmod(path, 0o600)
        os.environ[CREDENTIALS_ENV] = path
        return Path(path)
    except Exception:
        Path(path).unlink(missing_ok=True)
        raise _missing_credentials() from None


def load_service_account() -> service_account.Credentials:
    """Use exclusively the configured service account, never implicit machine ADC."""
    path = _credential_file()
    try:
        return service_account.Credentials.from_service_account_file(str(path))
    except (OSError, ValueError, KeyError):
        raise _missing_credentials() from None
