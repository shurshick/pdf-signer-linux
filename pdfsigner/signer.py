import os
import subprocess
from typing import Optional

from pdfsigner.certstore import CertInfo, CSPTESR_PATH


def sign_detached(pdf_path: str, cert: CertInfo, sig_path: str) -> str:
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if not os.path.isfile(CSPTESR_PATH):
        raise FileNotFoundError(f"csptest not found at {CSPTESR_PATH}")
    cert_id = cert.subject_cn or cert.thumbprint
    if not cert_id:
        raise ValueError("Certificate CN and thumbprint are both empty")
    cmd = [
        CSPTESR_PATH,
        "-sfsign", "-sign", "-detached", "-add",
        "-my", cert_id,
        "-in", os.path.abspath(pdf_path),
        "-out", os.path.abspath(sig_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"Signing error: {result.stderr or result.stdout}")
    if not os.path.isfile(sig_path):
        raise FileNotFoundError(f"Signature file not created: {sig_path}")
    return sig_path


def sign_embedded(pdf_path: str, cert: CertInfo, output_path: str) -> str:
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if not cert.subject_cn:
        raise ValueError("Certificate CN is empty")
    try:
        return _sign_embedded_pkcs11(pdf_path, cert, output_path)
    except Exception:
        return _sign_embedded_csptest_fallback(pdf_path, cert, output_path)


def _sign_embedded_pkcs11(pdf_path: str, cert: CertInfo, output_path: str) -> str:
    try:
        from pyhanko.sign import signers
        from pyhanko.sign.pkcs11 import PKCS11SigningContext
        from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter

        lib_paths = [
            "/opt/cprocsp/lib/amd64/librtpkcs11ecp.so",
            "/opt/cprocsp/lib/amd64/librtpkcs11.so",
        ]
        pkcs11_lib = None
        for p in lib_paths:
            if os.path.isfile(p):
                pkcs11_lib = p
                break
        if not pkcs11_lib:
            raise FileNotFoundError("PKCS#11 library not found")

        pkcs11_ctx = PKCS11SigningContext(
            pkcs11_library=pkcs11_lib,
            token_label="",
            key_label=cert.subject_cn,
        )
        signer_obj = signers.Pkcs11Signer(
            pkcs11_context=pkcs11_ctx,
            key_label=cert.subject_cn,
        )
        with open(pdf_path, "rb") as f:
            w = IncrementalPdfFileWriter(f)
        meta = signers.PdfSignatureMetadata(
            field_name="Signature1",
            reason="Signed with PDF Signer Linux",
            location=os.uname().nodename,
        )
        pdf_signer = signers.PdfSigner(meta, signer=signer_obj)
        with open(output_path, "wb") as out:
            pdf_signer.sign_pdf(w, output=out)
        return output_path
    except ImportError:
        raise RuntimeError("pyHanko not installed. Run: pip install pyhanko")
    except Exception as e:
        raise RuntimeError(f"PKCS#11 signing failed: {e}")


def _sign_embedded_csptest_fallback(pdf_path: str, cert: CertInfo, output_path: str) -> str:
    import shutil
    shutil.copy2(pdf_path, output_path)
    sig_path = output_path + ".sig"
    try:
        sign_detached(pdf_path, cert, sig_path)
        return output_path
    except Exception:
        if os.path.exists(sig_path):
            os.remove(sig_path)
        raise


def verify_signature(file_path: str) -> dict:
    result = {
        "status": "UNKNOWN",
        "details": [],
        "errors": [],
        "warnings": [],
    }
    if not os.path.isfile(file_path):
        result["status"] = "INVALID"
        result["errors"].append(f"File not found: {file_path}")
        return result
    result["details"].append(f"File: {os.path.basename(file_path)}")
    result["details"].append(f"Size: {os.path.getsize(file_path)} bytes")
    if file_path.endswith(".sig"):
        return _verify_detached(file_path, result)
    elif file_path.lower().endswith(".pdf"):
        return _verify_embedded(file_path, result)
    else:
        result["status"] = "INVALID"
        result["errors"].append("Unsupported file type")
        return result


def _verify_detached(sig_path: str, result: dict) -> dict:
    pdf_path = _find_matching_pdf(sig_path)
    if not pdf_path:
        result["status"] = "WARNING"
        result["warnings"].append("Matching PDF not found")
    else:
        result["details"].append(f"Original PDF: {os.path.basename(pdf_path)}")
    if os.path.isfile(CSPTESR_PATH):
        try:
            cmd = [CSPTESR_PATH, "-sfsign", "-verify", "-in", sig_path]
            if pdf_path:
                cmd.extend(["-data", pdf_path])
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                result["status"] = "VALID"
                result["details"].append("Signature verified successfully")
            else:
                result["status"] = "INVALID"
                result["errors"].append(f"Verification failed: {r.stderr or r.stdout}")
        except Exception as e:
            result["status"] = "WARNING"
            result["warnings"].append(f"Verification error: {e}")
    else:
        result["status"] = "WARNING"
        result["warnings"].append("csptest not available for verification")
    return result


def _verify_embedded(pdf_path: str, result: dict) -> dict:
    try:
        from pyhanko.pdf_utils.reader import PdfFileReader
        with open(pdf_path, "rb") as f:
            reader = PdfFileReader(f)
            if "/AcroForm" not in reader.trailer["/Root"]:
                result["status"] = "WARNING"
                result["warnings"].append("No signature field found")
                return result
        result["status"] = "VALID"
        result["details"].append("PDF signature structure found")
    except ImportError:
        result["status"] = "WARNING"
        result["warnings"].append("pyHanko not available for embedded verification")
    except Exception as e:
        result["status"] = "INVALID"
        result["errors"].append(f"Verification error: {e}")
    return result


def _find_matching_pdf(sig_path: str) -> Optional[str]:
    base = sig_path.rsplit(".sig", 1)[0]
    candidates = [
        base,
        base.replace("-signed", ""),
        base.replace("_signed", ""),
        base.replace("-stamped", ""),
        base.replace("_stamped", ""),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def format_verification_report(reports: list) -> str:
    lines = ["Signature Verification Report", ""]
    for i, r in enumerate(reports, 1):
        lines.append(f"--- File {i} [{r['status']}] ---")
        for d in r["details"]:
            lines.append(f"  {d}")
        for w in r["warnings"]:
            lines.append(f"  WARNING: {w}")
        for e in r["errors"]:
            lines.append(f"  ERROR: {e}")
        lines.append("")
    return "\n".join(lines)
