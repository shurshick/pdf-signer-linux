import os
import tempfile
import pytest
from pdfsigner.stamp import (
    create_stamp_image, validate_stamp_size, build_stamp_text,
    _truncate_hash, STAMP_BLUE, MM_TO_PX,
    MIN_STAMP_WIDTH_MM, MIN_STAMP_HEIGHT_MM, MIN_FONT_PT,
)
from pdfsigner.settings import StampProfile


def test_stamp_constants():
    assert STAMP_BLUE == (0, 74, 173)
    assert MM_TO_PX == 3.78
    assert MIN_STAMP_WIDTH_MM == 60
    assert MIN_STAMP_HEIGHT_MM == 20


def test_create_stamp_image_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "stamp.png")
        result = create_stamp_image(path)
        assert os.path.exists(path)
        assert result == path


def test_create_stamp_image_with_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "stamp.png")
        create_stamp_image(
            path,
            owner="Test Owner",
            issuer="Test Issuer",
            serial="123456",
            thumbprint="ABC123DEF456",
            reason="Test Reason",
            valid_from="01.01.2026",
            valid_to="31.12.2026",
            signature_fn="test.sig",
        )
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0


def test_create_stamp_image_with_profile():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "stamp.png")
        profile = StampProfile(width_mm=120, height_mm=45, font_size=10)
        create_stamp_image(path, owner="Test", profile=profile)
        assert os.path.exists(path)


def test_create_stamp_image_with_logo():
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow not available")

    with tempfile.TemporaryDirectory() as tmpdir:
        logo_path = os.path.join(tmpdir, "logo.png")
        img = Image.new("RGBA", (100, 50), (255, 0, 0, 255))
        img.save(logo_path)

        stamp_path = os.path.join(tmpdir, "stamp.png")
        profile = StampProfile(logo_path=logo_path, logo_scale=150)
        create_stamp_image(stamp_path, owner="Test", profile=profile)
        assert os.path.exists(stamp_path)


def test_validate_stamp_size_ok():
    errors = validate_stamp_size(90, 35, 8)
    assert len(errors) == 0


def test_validate_stamp_size_too_small():
    errors = validate_stamp_size(30, 10, 3)
    assert len(errors) == 3


def test_validate_stamp_size_width_only():
    errors = validate_stamp_size(50, 35, 8)
    assert len(errors) == 1


def test_validate_stamp_size_height_only():
    errors = validate_stamp_size(90, 10, 8)
    assert len(errors) == 1


def test_truncate_hash_short():
    assert _truncate_hash("ABC123") == "ABC123"


def test_truncate_hash_long():
    result = _truncate_hash("A" * 40)
    assert "..." in result
    assert len(result) < 40


def test_truncate_hash_with_spaces():
    result = _truncate_hash("AB CD EF GH IJ KL MN OP QR ST")
    assert " " not in result or "..." in result


def test_build_stamp_text():
    profile = StampProfile()
    text = build_stamp_text(
        profile,
        owner="Test Owner",
        issuer="Test Issuer",
        serial="SN123",
        reason="Test Reason",
        valid_from="01.01.2026",
        valid_to="31.12.2026",
    )
    assert "Владелец: Test Owner" in text
    assert "Издатель: Test Issuer" in text
    assert "Причина: Test Reason" in text
    assert "Серийный номер: SN123" in text


def test_build_stamp_text_minimal():
    profile = StampProfile(
        include_issuer=False,
        include_reason=False,
        include_serial=False,
        include_validity=False,
    )
    text = build_stamp_text(profile, owner="Test", issuer="", serial="", reason="")
    assert "Владелец: Test" in text
    assert "Издатель" not in text
    assert "Причина" not in text


def test_build_stamp_text_custom():
    profile = StampProfile(include_custom=True, custom_text="Custom line")
    text = build_stamp_text(profile, owner="T", issuer="", serial="", reason="")
    assert "Custom line" in text


def test_stamp_position_calculation():
    from pdfsigner.pdfstamp import _parse_page_range
    assert _parse_page_range("1-", 10) == set(range(10))
    assert _parse_page_range("1,3,5", 10) == {0, 2, 4}
    assert _parse_page_range("2-4", 10) == {1, 2, 3}
    assert _parse_page_range("", 5) == set(range(5))
