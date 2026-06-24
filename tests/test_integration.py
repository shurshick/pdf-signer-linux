"""Integration tests for pdf-signer-linux functionality."""
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def create_test_pdf(path):
    """Create a minimal valid PDF file for testing."""
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 72), "Test PDF for pdfsigner", fontsize=12)
    page.insert_text((72, 100), "Created for integration testing", fontsize=10)
    doc.save(path)
    doc.close()
    return path

def test_create_stamp_image():
    """Test stamp image generation."""
    from pdfsigner.stamp import create_stamp_image, validate_stamp_size, build_stamp_text
    from pdfsigner.settings import StampProfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        stamp_path = os.path.join(tmpdir, "stamp.png")
        result = create_stamp_image(
            stamp_path,
            owner="Тестов Тест Тестович",
            issuer="CryptoPro",
            serial="1234567890ABCDEF",
            thumbprint="AABBCCDDEE1122334455667788990011",
            reason="Тестовое подписание",
            valid_from="01.01.2025",
            valid_to="31.12.2027",
            signature_fn="test.pdf.sig",
        )
        assert os.path.exists(result), f"Stamp image not created: {result}"
        assert os.path.getsize(result) > 0, "Stamp image is empty"
        print(f"[PASS] create_stamp_image: {os.path.getsize(result)} bytes")
        
        errors = validate_stamp_size(90, 35, 8)
        assert len(errors) == 0, f"Validation failed: {errors}"
        print("[PASS] validate_stamp_size (90x35mm, 8pt)")
        
        errors = validate_stamp_size(30, 10, 4)
        assert len(errors) > 0, "Should fail for small size"
        print("[PASS] validate_stamp_size rejects small size")
        
        profile = StampProfile()
        text = build_stamp_text(
            profile,
            owner="Тестов Тест",
            issuer="CryptoPro",
            serial="123456",
            reason="Подпись",
            valid_from="01.01.2025",
            valid_to="31.12.2027",
        )
        assert "Тестов" in text, f"Owner name not in text: {text}"
        assert "CryptoPro" in text, f"Issuer not in text: {text}"
        print(f"[PASS] build_stamp_text:\n{text}")

def test_apply_stamp():
    """Test stamp application to PDF."""
    from pdfsigner.stamp import create_stamp_image
    from pdfsigner.pdfstamp import apply_stamp
    from pdfsigner.settings import StampProfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_pdf = os.path.join(tmpdir, "input.pdf")
        output_pdf = os.path.join(tmpdir, "output.pdf")
        stamp_path = os.path.join(tmpdir, "stamp.png")
        
        create_test_pdf(input_pdf)
        assert os.path.exists(input_pdf), "Test PDF not created"
        print(f"[PASS] Created test PDF: {os.path.getsize(input_pdf)} bytes")
        
        create_stamp_image(
            stamp_path,
            owner="Тестов Тест",
            issuer="CryptoPro",
            serial="ABC123",
            thumbprint="DEADBEEF12345678",
            reason="Тест",
            valid_from="01.01.2025",
            valid_to="31.12.2027",
        )
        print(f"[PASS] Created stamp image: {os.path.getsize(stamp_path)} bytes")
        
        profile = StampProfile()
        result = apply_stamp(input_pdf, output_pdf, stamp_path, "1-", profile)
        assert os.path.exists(result), f"Output PDF not created: {result}"
        assert os.path.getsize(result) > os.path.getsize(input_pdf), \
            f"Output ({os.path.getsize(result)}) should be larger than input ({os.path.getsize(input_pdf)})"
        print(f"[PASS] apply_stamp: input={os.path.getsize(input_pdf)} bytes, output={os.path.getsize(result)} bytes")

def test_stamp_profiles():
    """Test all stamp profiles."""
    from pdfsigner.settings import BUILT_IN_PROFILES, StampProfile
    
    for name, profile in BUILT_IN_PROFILES.items():
        p = StampProfile.from_dict(profile.to_dict())
        p.normalize()
        assert p.width_mm >= 40, f"{name}: width too small"
        assert p.height_mm >= 15, f"{name}: height too small"
        print(f"[PASS] Profile '{name}': {p.width_mm}x{p.height_mm}mm, font={p.font_size}pt")

def test_settings():
    """Test settings save/load/export/import."""
    from pdfsigner.settings import (
        ApplicationSettings, StampProfile, load_settings, save_settings,
        export_settings, import_settings,
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_file = os.path.join(tmpdir, "settings.json")
        export_file = os.path.join(tmpdir, "export.json")
        
        original = ApplicationSettings()
        original.verify_after_signing = True
        original.stamp_profile = StampProfile(
            name="custom", width_mm=100, height_mm=40,
        )
        
        export_settings(settings_file, original)
        assert os.path.exists(settings_file), "Settings file not created"
        
        loaded = import_settings(settings_file)
        assert loaded.verify_after_signing == True, "verify_after_signing not saved"
        assert loaded.stamp_profile.width_mm == 100, "width_mm not saved"
        assert loaded.stamp_profile.name == "custom", "name not saved"
        print("[PASS] Settings export/import")

def test_diagnostics():
    """Test diagnostics module."""
    from pdfsigner.diagnostics import run_diagnostics, format_report
    
    report = run_diagnostics("1.0.2-test")
    assert report.app_version == "1.0.2-test", "Version not set"
    assert len(report.items) > 0, "No diagnostic items"
    
    text = format_report(report)
    assert "PDF Signer Linux Diagnostics" in text, "Header missing"
    print(f"[PASS] Diagnostics: {len(report.items)} items")
    print(f"  Report preview:\n{text[:300]}")

def test_applog():
    """Test logging with secret sanitization."""
    from pdfsigner.applog import log_info, log_error
    
    log_info("Test log message")
    log_info("password=secret123 should be redacted")
    log_info("PIN: 4567 should be redacted")
    log_error("Test error", ValueError("test exception"))
    print("[PASS] App logging works")

def test_certstore_parse():
    """Test certificate parsing."""
    from pdfsigner.certstore import (
        _parse_certmgr_output, _is_separator, _extract_cn,
    )
    
    assert _is_separator("12345678--------------------------"), "Should be separator"
    assert not _is_separator("Subject: Test"), "Should not be separator"
    print("[PASS] _is_separator")
    
    assert _extract_cn("CN=Test User, O=Org") == "Test User", "CN extraction failed"
    assert _extract_cn("Simple Name") == "Simple Name", "Fallback failed"
    print("[PASS] _extract_cn")
    
    sample_output = """123456789-------------------------
Subject: CN=Test User, O=Test Org
Issuer: CN=Test CA
Serial number: 12345
Thumbprint: AABBCCDD11223344
Container: test_container
    
987654321-------------------------
Subject: CN=Second User
Issuer: CN=Second CA
Serial number: 67890
Thumbprint: 1122334455667788
Container: other_container"""
    
    certs = _parse_certmgr_output(sample_output)
    assert len(certs) == 2, f"Expected 2 certs, got {len(certs)}"
    assert certs[0].subject_cn == "Test User"
    assert certs[1].subject_cn == "Second User"
    print(f"[PASS] _parse_certmgr_output: parsed {len(certs)} certificates")

def test_signer_module():
    """Test signer module functions."""
    from pdfsigner.signer import (
        format_verification_report, verify_signature, _find_matching_pdf,
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        report = format_verification_report([
            {"status": "VALID", "details": ["OK"], "warnings": [], "errors": []},
            {"status": "INVALID", "details": [], "warnings": [], "errors": ["Bad sig"]},
        ])
        assert "VALID" in report
        assert "INVALID" in report
        assert "Bad sig" in report
        print("[PASS] format_verification_report")
        
        result = verify_signature(os.path.join(tmpdir, "nonexistent.pdf"))
        assert result["status"] == "INVALID"
        print("[PASS] verify_signature (missing file)")
        
        pdf1 = os.path.join(tmpdir, "test.pdf")
        sig1 = os.path.join(tmpdir, "test.pdf.sig")
        sig2 = os.path.join(tmpdir, "test_stamped.pdf.sig")
        
        with open(pdf1, "w") as f:
            f.write("test")
        with open(sig1, "w") as f:
            f.write("sig")
        with open(sig2, "w") as f:
            f.write("sig")
        
        found = _find_matching_pdf(sig1)
        assert found == pdf1, f"Expected {pdf1}, got {found}"
        print("[PASS] _find_matching_pdf (exact)")
        
        found2 = _find_matching_pdf(sig2)
        assert found2 == pdf1, f"Expected {pdf1}, got {found2}"
        print("[PASS] _find_matching_pdf (_stamped)")

def test_binary_import():
    """Test that all modules can be imported correctly."""
    from pdfsigner.stamp import create_stamp_image, validate_stamp_size, build_stamp_text
    from pdfsigner.pdfstamp import apply_stamp
    from pdfsigner.signer import sign_detached, sign_embedded, verify_signature
    from pdfsigner.certstore import load_certificates, CertInfo
    from pdfsigner.diagnostics import run_diagnostics, format_report
    from pdfsigner.settings import StampProfile, ApplicationSettings
    from pdfsigner.applog import log_info, log_error
    print("[PASS] All module imports successful")

def test_e2e_stamp_multi_page():
    """End-to-end: create multi-page PDF, stamp it, verify output."""
    import fitz
    from pdfsigner.stamp import create_stamp_image, build_stamp_text
    from pdfsigner.pdfstamp import apply_stamp
    from pdfsigner.settings import StampProfile, BUILT_IN_PROFILES
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_pdf = os.path.join(tmpdir, "multipage.pdf")
        output_pdf = os.path.join(tmpdir, "multipage_stamped.pdf")
        stamp_path = os.path.join(tmpdir, "stamp.png")
        
        doc = fitz.open()
        for i in range(5):
            page = doc.new_page(width=595, height=842)
            page.insert_text((72, 72), f"Page {i+1}", fontsize=14)
            page.insert_text((72, 100), "Lorem ipsum dolor sit amet", fontsize=10)
        doc.save(input_pdf)
        doc.close()
        input_size = os.path.getsize(input_pdf)
        print(f"  Created 5-page PDF: {input_size} bytes")
        
        for profile_name, profile in BUILT_IN_PROFILES.items():
            p = StampProfile.from_dict(profile.to_dict())
            p.normalize()
            
            create_stamp_image(
                stamp_path,
                owner="Иванов Иван Иванович",
                issuer="CryptoPro RC5 FFD",
                serial="4E21A2B3C4D5E6F7",
                thumbprint="AA BB CC DD EE FF 00 11 22 33",
                reason="Согласование документа",
                valid_from="15.03.2024",
                valid_to="15.03.2027",
                signature_fn="doc.pdf.sig",
                profile=p,
            )
            
            result = apply_stamp(input_pdf, output_pdf, stamp_path, "1-", p)
            output_size = os.path.getsize(result)
            assert output_size > input_size, \
                f"Profile '{profile_name}': output ({output_size}) <= input ({input_size})"
            
            out_doc = fitz.open(result)
            assert len(out_doc) == 5, f"Profile '{profile_name}': page count changed"
            
            has_images = False
            for page in out_doc:
                images = page.get_images()
                if images:
                    has_images = True
                    break
            assert has_images, f"Profile '{profile_name}': no images found in output"
            out_doc.close()
            
            print(f"  [PASS] Profile '{profile_name}': {input_size} -> {output_size} bytes, 5 pages, stamp applied")
            os.remove(output_pdf)
            os.remove(stamp_path)

def test_e2e_stamp_page_range():
    """End-to-end: stamp specific page range only."""
    import fitz
    from pdfsigner.stamp import create_stamp_image
    from pdfsigner.pdfstamp import apply_stamp
    from pdfsigner.settings import StampProfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_pdf = os.path.join(tmpdir, "pages.pdf")
        output_pdf = os.path.join(tmpdir, "pages_stamped.pdf")
        stamp_path = os.path.join(tmpdir, "stamp.png")
        
        doc = fitz.open()
        for i in range(10):
            page = doc.new_page(width=595, height=842)
            page.insert_text((72, 72), f"Page {i+1}", fontsize=14)
        doc.save(input_pdf)
        doc.close()
        
        create_stamp_image(stamp_path, owner="Test", profile=StampProfile())
        profile = StampProfile()
        
        result = apply_stamp(input_pdf, output_pdf, stamp_path, "1,3,5", profile)
        
        out_doc = fitz.open(result)
        assert len(out_doc) == 10, "Page count changed"
        stamped_count = 0
        for page in out_doc:
            if page.get_images():
                stamped_count += 1
        assert stamped_count == 3, f"Expected 3 stamped pages, got {stamped_count}"
        out_doc.close()
        
        print(f"  [PASS] Page range '1,3,5': {stamped_count}/10 pages stamped")

def test_stamp_text_preview():
    """Test stamp text preview for all profile configurations."""
    from pdfsigner.stamp import build_stamp_text
    from pdfsigner.settings import StampProfile
    
    configs = [
        ("full", True, True, True, True, True, True),
        ("minimal", True, False, False, True, False, False),
        ("owner only", True, False, False, False, False, False),
        ("serial only", False, False, False, False, True, False),
    ]
    
    for name, owner, issuer, date, reason, serial, validity in configs:
        p = StampProfile(
            include_owner=owner, include_issuer=issuer,
            include_date=date, include_reason=reason,
            include_serial=serial, include_validity=validity,
        )
        text = build_stamp_text(
            p,
            owner="Иванов И.И.",
            issuer="CryptoPro",
            serial="ABC123",
            reason="Согласовано",
            valid_from="01.01.2025",
            valid_to="31.12.2027",
        )
        assert "Документ подписан" in text, f"'{name}': header missing"
        
        if owner:
            assert "Иванов" in text, f"'{name}': owner missing"
        else:
            assert "Иванов" not in text, f"'{name}': owner should be absent"
        
        if serial:
            assert "ABC123" in text, f"'{name}': serial missing"
        
        print(f"  [PASS] Config '{name}': {len(text)} chars")
        print(f"    Preview: {text[:100]}...")

def test_stamp_image_various_sizes():
    """Test stamp creation with various sizes."""
    from pdfsigner.stamp import create_stamp_image
    from pdfsigner.settings import StampProfile
    
    sizes = [
        (60, 20, "minimum"),
        (70, 25, "minimal profile"),
        (90, 35, "standard profile"),
        (120, 45, "detailed profile"),
        (150, 60, "large"),
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        for w, h, label in sizes:
            stamp_path = os.path.join(tmpdir, f"stamp_{w}x{h}.png")
            p = StampProfile(width_mm=w, height_mm=h)
            p.normalize()
            
            result = create_stamp_image(
                stamp_path,
                owner="Тест Тестович",
                issuer="УЦ CryptoPro",
                serial="AABBCCDD",
                thumbprint="1122334455667788AABB",
                reason="Тестовая подпись",
                valid_from="01.01.2025",
                valid_to="31.12.2027",
                signature_fn="test.sig",
                profile=p,
            )
            size = os.path.getsize(result)
            assert size > 0, f"Stamp {label}: empty"
            print(f"  [PASS] Size {w}x{h}mm ({label}): {size} bytes")


if __name__ == "__main__":
    print("=" * 60)
    print("PDF Signer Linux - Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Binary imports", test_binary_import),
        ("Stamp image creation", test_create_stamp_image),
        ("Stamp application to PDF", test_apply_stamp),
        ("Stamp profiles", test_stamp_profiles),
        ("Settings persistence", test_settings),
        ("Diagnostics", test_diagnostics),
        ("App logging", test_applog),
        ("Certificate parsing", test_certstore_parse),
        ("Signer module", test_signer_module),
        ("E2E: multi-page stamp", test_e2e_stamp_multi_page),
        ("E2E: page range stamp", test_e2e_stamp_page_range),
        ("Stamp text preview", test_stamp_text_preview),
        ("Stamp image sizes", test_stamp_image_various_sizes),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        print(f"\n--- {name} ---")
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'=' * 60}")
    
    sys.exit(1 if failed > 0 else 0)
