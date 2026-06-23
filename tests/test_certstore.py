import os
from pdfsigner.certstore import (
    _is_separator, _after_colon, _extract_cn,
    _parse_certmgr_output, CertInfo,
)


def test_is_separator():
    assert _is_separator("12345678--------") is True
    assert _is_separator("---") is False
    assert _is_separator("") is False
    assert _is_separator("ABCDEFGH") is False


def test_after_colon():
    assert _after_colon("Subject: CN=Test") == "CN=Test"
    assert _after_colon("No colon") == ""
    assert _after_colon("Key: value: with: colons") == "value: with: colons"


def test_extract_cn():
    assert _extract_cn("CN=Test User, O=Org") == "Test User"
    assert _extract_cn("O=Org, CN=Test User") == "Test User"
    assert _extract_cn("No CN here") == "No CN here"


def test_parse_certmgr_single():
    output = """12345678--------------------------
Субъект: CN=Test User, O=Test Org
Издатель: CN=Test CA, O=Test Org
Серийный номер: 1234567890
SHA1 отпечаток: AB CD EF 01 23 45 67 89
"""
    certs = _parse_certmgr_output(output)
    assert len(certs) == 1
    assert certs[0].subject_cn == "Test User"
    assert certs[0].issuer_cn == "Test CA"


def test_parse_certmgr_multiple():
    output = """12345678--------------------------
Субъект: CN=First User
Издатель: CN=CA1
98765432--------------------------
Субъект: CN=Second User
Издатель: CN=CA2
"""
    certs = _parse_certmgr_output(output)
    assert len(certs) == 2
    assert certs[0].subject_cn == "First User"
    assert certs[1].subject_cn == "Second User"


def test_parse_certmgr_empty():
    certs = _parse_certmgr_output("")
    assert len(certs) == 0


def test_cert_info_display_name():
    c = CertInfo(subject_cn="User", issuer_cn="CA", serial="123")
    assert "User" in c.display_name
    assert "CA" in c.display_name
