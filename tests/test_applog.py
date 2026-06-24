import os
import tempfile
import pytest
from pdfsigner.applog import _sanitize, log_info, log_error


def test_sanitize_normal():
    assert _sanitize("normal message") == "normal message"


def test_sanitize_password():
    result = _sanitize("password: secret123")
    assert "secret123" not in result
    assert "redacted" in result


def test_sanitize_pin():
    result = _sanitize("PIN=123456")
    assert "123456" not in result
    assert "redacted" in result


def test_sanitize_key():
    result = _sanitize("key: abcdef")
    assert "abcdef" not in result
    assert "redacted" in result


def test_sanitize_certificate():
    cert = "-----BEGIN CERTIFICATE-----\nMIIBkTCB+w...\n-----END CERTIFICATE-----"
    result = _sanitize(cert)
    assert "MIIBkTCB+w" not in result
    assert "redacted-certificate" in result


def test_sanitize_none():
    assert _sanitize(None) is None


def test_sanitize_empty():
    assert _sanitize("") == ""


def test_log_info():
    with tempfile.TemporaryDirectory() as tmpdir:
        from pdfsigner import LOG_DIR, LOG_FILE
        orig_log_dir = LOG_DIR
        import pdfsigner.applog as applog_mod
        old_log_dir = applog_mod.LOG_DIR if hasattr(applog_mod, 'LOG_DIR') else None

        log_path = os.path.join(tmpdir, "test.log")
        applog_mod.LOG_DIR = tmpdir
        applog_mod.LOG_FILE = log_path

        try:
            log_info("Test message")
            assert os.path.exists(log_path)
            with open(log_path) as f:
                content = f.read()
            assert "Test message" in content
            assert "INFO" in content
        finally:
            if old_log_dir is not None:
                applog_mod.LOG_DIR = old_log_dir


def test_log_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        import pdfsigner.applog as applog_mod
        log_path = os.path.join(tmpdir, "test.log")
        applog_mod.LOG_DIR = tmpdir
        applog_mod.LOG_FILE = log_path

        try:
            log_error("Something failed", ValueError("test error"))
            assert os.path.exists(log_path)
            with open(log_path) as f:
                content = f.read()
            assert "Something failed" in content
            assert "ERROR" in content
            assert "test error" in content
        finally:
            pass
