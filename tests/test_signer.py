from pdfsigner.signer import format_verification_report


def test_format_verification_report():
    reports = [
        {
            "status": "VALID",
            "details": ["File: test.pdf", "Size: 12345"],
            "errors": [],
            "warnings": [],
        }
    ]
    text = format_verification_report(reports)
    assert "VALID" in text
    assert "test.pdf" in text


def test_format_verification_report_with_warnings():
    reports = [
        {
            "status": "WARNING",
            "details": ["File: test.sig"],
            "errors": [],
            "warnings": ["Matching PDF not found"],
        }
    ]
    text = format_verification_report(reports)
    assert "WARNING" in text
    assert "Matching PDF not found" in text


def test_format_verification_report_empty():
    text = format_verification_report([])
    assert "Signature Verification Report" in text
