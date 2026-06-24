import os
import pytest
from pdfsigner.certstore import (
    CertInfo, _is_separator, _after_colon, _extract_cn,
    _parse_certmgr_output, is_certmgr_available, is_csptest_available,
)


def test_certinfo_defaults():
    c = CertInfo()
    assert c.subject_cn == ""
    assert c.has_private_key is True


def test_certinfo_display_name():
    c = CertInfo(subject_cn="Test CN", issuer_cn="Test Issuer", serial="ABC")
    name = c.display_name
    assert "Test CN" in name
    assert "Test Issuer" in name
    assert "ABC" in name


def test_is_separator():
    assert _is_separator("1" + "-" * 40) is True
    assert _is_separator("short") is False
    assert _is_separator("12345") is False
    assert _is_separator("0" + "-" * 8) is True


def test_after_colon():
    assert _after_colon("Subject: CN=Test") == "CN=Test"
    assert _after_colon("NoColon") == "NoColon"
    assert _after_colon("Key:  Value ") == "Value"


def test_extract_cn():
    assert _extract_cn("CN=Test User, O=Org") == "Test User"
    assert _extract_cn("O=Org, CN=Test User") == "Test User"
    assert _extract_cn("No CN field") == "No CN field"


def test_parse_certmgr_output_empty():
    assert _parse_certmgr_output("") == []


def test_parse_certmgr_output_with_cert():
    output = """1----------------------------------------------
  Subject: CN=Test User, O=Test Org
  Issuer: CN=Test CA
  Serial number: 1234567890
  Thumbprint: ABC123DEF456
2----------------------------------------------
"""
    certs = _parse_certmgr_output(output)
    assert len(certs) == 1
    assert certs[0].subject_cn == "Test User"
    assert certs[0].issuer_cn == "Test CA"
    assert certs[0].serial == "1234567890"
    assert certs[0].thumbprint == "ABC123DEF456"


def test_parse_certmgr_output_multiple():
    output = """1----------------------------------------------
  Subject: CN=User One
  Thumbprint: AAA
2----------------------------------------------
  Subject: CN=User Two
  Thumbprint: BBB
3----------------------------------------------
"""
    certs = _parse_certmgr_output(output)
    assert len(certs) == 2
    assert certs[0].subject_cn == "User One"
    assert certs[1].subject_cn == "User Two"


def test_parse_certmgr_output_russian():
    output = """1----------------------------------------------
  Субъект: CN=Тестовый Пользователь
  Издатель: CN=Тестовый CA
  Серийный номер: ABCDEF
  Отпечаток: 1234567890ABCDEF
2----------------------------------------------
"""
    certs = _parse_certmgr_output(output)
    assert len(certs) == 1
    assert certs[0].subject_cn == "Тестовый Пользователь"
    assert certs[0].thumbprint == "1234567890ABCDEF"


def test_certmgr_availability():
    result = is_certmgr_available()
    assert isinstance(result, bool)


def test_csptest_availability():
    result = is_csptest_available()
    assert isinstance(result, bool)
