import os
import subprocess
from dataclasses import dataclass
from typing import List


@dataclass
class DiagnosticItem:
    severity: str
    title: str
    message: str


@dataclass
class CertificateDiagnostic:
    subject: str
    issuer: str
    thumbprint: str
    suitable: bool
    message: str


@dataclass
class DiagnosticReport:
    app_version: str = ""
    items: List[DiagnosticItem] = None
    certificates: List[CertificateDiagnostic] = None

    def __post_init__(self):
        if self.items is None:
            self.items = []
        if self.certificates is None:
            self.certificates = []


def run_diagnostics(app_version: str) -> DiagnosticReport:
    from pdfsigner import APP_VERSION
    from pdfsigner.certstore import (
        is_certmgr_available, is_csptest_available,
        load_certificates, CERTMGR_PATH, CSPTESR_PATH,
    )

    report = DiagnosticReport(app_version=app_version or APP_VERSION)

    if is_certmgr_available():
        report.items.append(DiagnosticItem("OK", "certmgr", f"{CERTMGR_PATH} found"))
    else:
        report.items.append(DiagnosticItem("ERROR", "certmgr", f"{CERTMGR_PATH} not found"))

    if is_csptest_available():
        report.items.append(DiagnosticItem("OK", "csptest", f"{CSPTESR_PATH} found"))
    else:
        report.items.append(DiagnosticItem("ERROR", "csptest", f"{CSPTESR_PATH} not found"))

    try:
        certs = load_certificates()
        if not certs:
            report.items.append(DiagnosticItem("WARNING", "Certificates", "No certificates found"))
        else:
            report.items.append(DiagnosticItem("OK", "Certificates", f"{len(certs)} certificate(s) found"))
            for c in certs:
                report.certificates.append(CertificateDiagnostic(
                    subject=c.subject_cn,
                    issuer=c.issuer_cn,
                    thumbprint=c.thumbprint,
                    suitable=True,
                    message="Ready",
                ))
    except Exception as e:
        report.items.append(DiagnosticItem("ERROR", "Certificates", str(e)))

    return report


def format_report(report: DiagnosticReport) -> str:
    from pdfsigner import APP_VERSION
    lines = [
        f"PDF Signer Linux Diagnostics",
        f"Version: {report.app_version or APP_VERSION}",
        "",
    ]
    for item in report.items:
        lines.append(f"[{item.severity}] {item.title}: {item.message}")
    if report.certificates:
        lines.append("")
        lines.append(f"Certificates ({len(report.certificates)}):")
        for i, c in enumerate(report.certificates, 1):
            lines.append(f"  {i}. {c.subject}")
            lines.append(f"     Issuer: {c.issuer}")
            lines.append(f"     Thumbprint: {c.thumbprint}")
            lines.append(f"     Status: {c.message}")
    return "\n".join(lines)
