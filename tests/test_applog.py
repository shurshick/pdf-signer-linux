import os
from pdfsigner.applog import _sanitize, log_info


def test_sanitize_password():
    assert "<redacted>" in _sanitize("password=secret123")
    assert "<redacted>" in _sanitize("PIN:=12345")


def test_sanitize_pem():
    text = "-----BEGIN CERTIFICATE-----\ndata\n-----END CERTIFICATE-----"
    assert "<redacted-certificate>" in _sanitize(text)


def test_sanitize_normal():
    assert _sanitize("normal message") == "normal message"


def test_sanitize_empty():
    assert _sanitize("") == ""


def test_log_info(tmp_path):
    from pdfsigner import applog
    applog.LOG_DIR = str(tmp_path / "logs")
    applog.LOG_FILE = str(tmp_path / "logs" / "app.log")
    log_info("test message")
    assert os.path.exists(applog.LOG_FILE)
