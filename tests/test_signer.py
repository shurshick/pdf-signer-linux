import os
import tempfile
import pytest
from pdfsigner.signer import (
    verify_signature, format_verification_report,
    _find_matching_pdf,
)
from pdfsigner.certstore import CertInfo


def test_verify_signature_not_found():
    result = verify_signature("/nonexistent/file.pdf")
    assert result["status"] == "INVALID"
    assert len(result["errors"]) > 0


def test_verify_signature_unsupported():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"test")
        path = f.name
    try:
        result = verify_signature(path)
        assert result["status"] == "INVALID"
    finally:
        os.unlink(path)


def test_verify_signature_sig_file():
    with tempfile.NamedTemporaryFile(suffix=".sig", delete=False) as f:
        f.write(b"test")
        path = f.name
    try:
        result = verify_signature(path)
        assert "details" in result
    finally:
        os.unlink(path)


def test_format_verification_report():
    reports = [
        {
            "status": "VALID",
            "details": ["File: test.pdf", "Size: 1024 bytes"],
            "warnings": [],
            "errors": [],
        },
        {
            "status": "INVALID",
            "details": ["File: bad.pdf"],
            "warnings": [],
            "errors": ["Verification failed"],
        },
    ]
    report = format_verification_report(reports)
    assert "VALID" in report
    assert "INVALID" in report
    assert "test.pdf" in report
    assert "Verification failed" in report


def test_find_matching_pdf_no_match():
    with tempfile.TemporaryDirectory() as tmpdir:
        sig_path = os.path.join(tmpdir, "test.sig")
        with open(sig_path, "w") as f:
            f.write("test")
        result = _find_matching_pdf(sig_path)
        assert result is None


def test_find_matching_pdf_with_match():
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "test.pdf")
        sig_path = os.path.join(tmpdir, "test.pdf.sig")
        with open(pdf_path, "w") as f:
            f.write("test")
        with open(sig_path, "w") as f:
            f.write("test")
        result = _find_matching_pdf(sig_path)
        assert result == pdf_path


def test_find_matching_pdf_stamped():
    with tempfile.TemporaryDirectory() as tmpdir:
        original = os.path.join(tmpdir, "test.pdf")
        stamped = os.path.join(tmpdir, "test-stamped.pdf")
        sig_path = os.path.join(tmpdir, "test-stamped.pdf.sig")
        with open(original, "w") as f:
            f.write("test")
        with open(stamped, "w") as f:
            f.write("test")
        with open(sig_path, "w") as f:
            f.write("test")
        result = _find_matching_pdf(sig_path)
        assert result == stamped


def test_format_verification_report_empty():
    report = format_verification_report([])
    assert "Signature Verification Report" in report


def test_sign_detached_no_file():
    from pdfsigner.signer import sign_detached
    cert = CertInfo(subject_cn="Test")
    with pytest.raises(FileNotFoundError):
        sign_detached("/nonexistent.pdf", cert, "/tmp/test.sig")


def test_sign_detached_no_cn():
    from pdfsigner.signer import sign_detached
    cert = CertInfo(subject_cn="")
    with pytest.raises((ValueError, FileNotFoundError)):
        sign_detached("/tmp/test.pdf", cert, "/tmp/test.sig")


def test_sign_embedded_no_file():
    from pdfsigner.signer import sign_embedded
    cert = CertInfo(subject_cn="Test")
    with pytest.raises(FileNotFoundError):
        sign_embedded("/nonexistent.pdf", cert, "/tmp/output.pdf")
