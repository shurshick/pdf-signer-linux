from pdfsigner.diagnostics import run_diagnostics, format_report


def test_run_diagnostics():
    report = run_diagnostics("1.0.0")
    assert report.app_version == "1.0.0"
    assert len(report.items) > 0


def test_format_report():
    report = run_diagnostics("1.0.0")
    text = format_report(report)
    assert "PDF Signer Linux Diagnostics" in text
    assert "1.0.0" in text


def test_diagnostic_severity():
    from pdfsigner.diagnostics import DiagnosticItem
    item = DiagnosticItem("OK", "test", "message")
    assert item.severity == "OK"
