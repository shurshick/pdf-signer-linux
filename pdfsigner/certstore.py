import os
import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CertInfo:
    subject_cn: str = ""
    issuer_cn: str = ""
    thumbprint: str = ""
    serial: str = ""
    container: str = ""
    provider: str = ""
    label: str = ""
    has_private_key: bool = True
    pkcs11_session: object = None
    pkcs11_key_label: str = ""

    @property
    def display_name(self) -> str:
        parts = []
        if self.subject_cn:
            parts.append(self.subject_cn)
        if self.issuer_cn:
            parts.append(f"Issuer: {self.issuer_cn}")
        if self.serial:
            parts.append(f"SN: {self.serial}")
        return " | ".join(parts)


CERTMGR_PATHS = [
    "/opt/cprocsp/bin/amd64/certmgr",
    "/opt/cprocsp/bin/amd64/certmgr.exe",
    "/usr/bin/certmgr",
]
CSPTESR_PATHS = [
    "/opt/cprocsp/bin/amd64/csptest",
    "/opt/cprocsp/bin/amd64/csptest.exe",
    "/usr/bin/csptest",
]


def _find_executable(paths: list) -> Optional[str]:
    for p in paths:
        if os.path.isfile(p):
            return p
    return None


CERTMGR_PATH = _find_executable(CERTMGR_PATHS) or CERTMGR_PATHS[0]
CSPTESR_PATH = _find_executable(CSPTESR_PATHS) or CSPTESR_PATHS[0]


def is_certmgr_available() -> bool:
    return _find_executable(CERTMGR_PATHS) is not None


def is_csptest_available() -> bool:
    return _find_executable(CSPTESR_PATHS) is not None


def load_certificates() -> List[CertInfo]:
    certs = _load_from_certmgr()
    certs.extend(_load_from_pkcs11())
    seen = set()
    unique = []
    for c in certs:
        key = f"{c.subject_cn}:{c.thumbprint}"
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def _load_from_certmgr() -> List[CertInfo]:
    from pdfsigner.applog import log_info, log_error
    certmgr = _find_executable(CERTMGR_PATHS)
    if not certmgr:
        log_info("certmgr not found in: " + ", ".join(CERTMGR_PATHS))
        return []
    log_info(f"certmgr found at: {certmgr}")
    try:
        result = subprocess.run(
            [certmgr, "-list", "-store", "uMy"],
            capture_output=True, text=True, timeout=10,
        )
        log_info(f"certmgr exit code: {result.returncode}")
        log_info(f"certmgr stdout ({len(result.stdout)} bytes): {result.stdout[:2000]}")
        if result.stderr:
            log_info(f"certmgr stderr: {result.stderr[:500]}")
        if result.returncode != 0:
            return []
        certs = _parse_certmgr_output(result.stdout)
        log_info(f"parsed {len(certs)} certificate(s) from certmgr")
        return certs
    except FileNotFoundError:
        log_error("certmgr not found", Exception(certmgr))
        return []
    except Exception as e:
        log_error("certmgr failed", e)
        return []


def _parse_certmgr_output(output: str) -> List[CertInfo]:
    from pdfsigner.applog import log_info
    certs = []
    current = None
    lines = output.splitlines()
    log_info(f"parsing {len(lines)} lines from certmgr")
    for line in lines:
        raw = line
        line = line.strip()
        if not line:
            continue
        if _is_separator(line):
            if current and current.subject_cn:
                current.label = current.display_name
                certs.append(current)
            current = CertInfo()
            continue
        if current is None:
            current = CertInfo()
        if "Subject" in line or "Субъект" in line or "SUBJECT" in line.upper():
            current.subject_cn = _extract_cn(_after_colon(line))
            log_info(f"  found subject_cn: {current.subject_cn}")
        elif "Issuer" in line or "Издатель" in line:
            current.issuer_cn = _extract_cn(_after_colon(line))
        elif "Serial" in line or "Серийный" in line:
            current.serial = _after_colon(line).strip()
        elif "thumbprint" in line.lower() or "отпечаток" in line.lower():
            current.thumbprint = _after_colon(line).strip()
        elif "Container" in line or "Контейнер" in line:
            current.container = _after_colon(line).strip()
        elif "provider" in line.lower() or "провайдер" in line.lower():
            current.provider = _after_colon(line).strip()
        elif "private" in line.lower() or "закрытый" in line.lower() or "key" in line.lower():
            current.has_private_key = True
    if current and current.subject_cn:
        current.label = current.display_name
        certs.append(current)
    log_info(f"parsed result: {len(certs)} cert(s)")
    return certs


def _load_from_pkcs11() -> List[CertInfo]:
    try:
        import pkcs11
        from pkcs11 import Mechanism
        lib_paths = [
            "/opt/cprocsp/lib/amd64/librtpkcs11ecp.so",
            "/opt/cprocsp/lib/amd64/librtpkcs11.so",
        ]
        for lib_path in lib_paths:
            if not os.path.isfile(lib_path):
                continue
            try:
                lib = pkcs11.lib(lib_path)
                tokens = lib.get_tokens()
                for token in tokens:
                    certs = _extract_certs_from_token(token)
                    if certs:
                        return certs
            except Exception:
                continue
    except ImportError:
        pass
    return []


def _extract_certs_from_token(token) -> List[CertInfo]:
    certs = []
    try:
        with token.open(rw=False) as session:
            objects = session.find_objects(object_class=8)
            for obj in objects:
                try:
                    der = obj[0].read()
                    cert = _parse_der_cert(der)
                    if cert:
                        cert.pkcs11_session = session
                        cert.has_private_key = True
                        cert.label = cert.display_name
                        certs.append(cert)
                except Exception:
                    continue
    except Exception:
        pass
    return certs


def _parse_der_cert(der_bytes: bytes) -> Optional[CertInfo]:
    try:
        from cryptography import x509
        cert = x509.load_der_x509_certificate(der_bytes)
        subject = cert.subject
        issuer = cert.issuer
        cn = ""
        for attr in subject:
            if attr.oid == x509.oid.NameOID.COMMON_NAME:
                cn = attr.value
        issuer_cn = ""
        for attr in issuer:
            if attr.oid == x509.oid.NameOID.COMMON_NAME:
                issuer_cn = attr.value
        serial = format(cert.serial_number, 'X')
        thumbprint = cert.fingerprint(cert.signature_hash_algorithm).hex().upper()
        not_after = cert.not_after_utc
        return CertInfo(
            subject_cn=cn,
            issuer_cn=issuer_cn,
            thumbprint=thumbprint,
            serial=serial,
        )
    except Exception:
        return None


def _is_separator(line: str) -> bool:
    stripped = line.strip()
    if len(stripped) < 4:
        return False
    i = 0
    while i < len(stripped) and stripped[i].isdigit():
        i += 1
    if i == 0 or i >= len(stripped):
        return False
    rest = stripped[i:]
    return all(c == '-' for c in rest) and len(rest) >= 3


def _after_colon(s: str) -> str:
    if ":" not in s:
        return s.strip()
    parts = s.split(":", 1)
    return parts[1].strip() if len(parts) > 1 else ""


def _extract_cn(s: str) -> str:
    for part in s.split(","):
        part = part.strip()
        if part.startswith("CN="):
            return part[3:]
    return s
