import pytest
from pdfsigner.diagnostics import (
    run_diagnostics, format_report, DiagnosticReport,
    DiagnosticItem, CertificateDiagnostic,
)


def test_diagnostic_item():
    item = DiagnosticItem(severity="OK", title="Test", message="All good")
    assert item.severity == "OK"
    assert item.title == "Test"


def test_certificate_diagnostic():
    c = CertificateDiagnostic(
        subject="Test", issuer="CA", thumbprint="ABC",
        suitable=True, message="Ready"
    )
    assert c.suitable is True


def test_diagnostic_report_defaults():
    r = DiagnosticReport()
    assert r.items == []
    assert r.certificates == []


def test_run_diagnostics():
    report = run_diagnostics("1.0.0")
    assert report.app_version == "1.0.0"
    assert len(report.items) > 0


def test_format_report():
    report = DiagnosticReport(app_version="1.0.0")
    report.items.append(DiagnosticItem("OK", "Test", "All good"))
    report.certificates.append(CertificateDiagnostic(
        subject="User", issuer="CA", thumbprint="ABC",
        suitable=True, message="Ready"
    ))
    text = format_report(report)
    assert "PDF Signer Linux Diagnostics" in text
    assert "1.0.0" in text
    assert "[OK] Test: All good" in text
    assert "User" in text


def test_format_report_empty():
    report = DiagnosticReport()
    text = format_report(report)
    assert "PDF Signer Linux Diagnostics" in text
