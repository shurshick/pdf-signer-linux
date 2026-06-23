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


CERTMGR_PATH = "/opt/cprocsp/bin/amd64/certmgr"
CSPTESR_PATH = "/opt/cprocsp/bin/amd64/csptest"


def is_certmgr_available() -> bool:
    return os.path.isfile(CERTMGR_PATH)


def is_csptest_available() -> bool:
    return os.path.isfile(CSPTESR_PATH)


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
    if not is_certmgr_available():
        return []
    try:
        result = subprocess.run(
            [CERTMGR_PATH, "-list", "-store", "uMy"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return []
        return _parse_certmgr_output(result.stdout)
    except Exception:
        return []


def _parse_certmgr_output(output: str) -> List[CertInfo]:
    certs = []
    current = None
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if _is_separator(line):
            if current:
                current.label = current.display_name
                certs.append(current)
            current = CertInfo()
            continue
        if current is None:
            continue
        if line.startswith("Subject:") or line.startswith("Субъект:"):
            current.subject_cn = _extract_cn(_after_colon(line))
        elif line.startswith("Issuer:") or line.startswith("Издатель:"):
            current.issuer_cn = _extract_cn(_after_colon(line))
        elif line.startswith("Serial number:") or line.startswith("Серийный номер:"):
            current.serial = _after_colon(line).strip()
        elif "thumbprint" in line.lower() or "отпечаток" in line.lower():
            current.thumbprint = _after_colon(line).strip()
        elif line.startswith("Container:") or line.startswith("Контейнер:"):
            current.container = _after_colon(line).strip()
        elif "provider" in line.lower() or "провайдер" in line.lower():
            current.provider = _after_colon(line).strip()
    if current:
        current.label = current.display_name
        certs.append(current)
    return certs


def _load_from_pkcs11() -> List[CertInfo]:
    try:
        import pkcs11
        from pkcs11 import Mechanism
        from pkcs11.util.ec import decode_named_curve_parameters
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
        from cryptography.hazmat.primitives import serialization
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
        return CertInfo(
            subject_cn=cn,
            issuer_cn=issuer_cn,
            thumbprint=thumbprint,
            serial=serial,
        )
    except Exception:
        return None


def _is_separator(line: str) -> bool:
    if len(line) < 8:
        return False
    i = 0
    while i < len(line) and line[i].isdigit():
        i += 1
    if i == 0 or i >= len(line):
        return False
    return all(c == '-' for c in line[i:])


def _after_colon(s: str) -> str:
    parts = s.split(":", 1)
    return parts[1].strip() if len(parts) > 1 else ""


def _extract_cn(s: str) -> str:
    for part in s.split(","):
        part = part.strip()
        if part.startswith("CN="):
            return part[3:]
    return s
