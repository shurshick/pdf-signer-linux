import time
from pdfsigner.stamp import (
    create_stamp_image, validate_stamp_size, build_stamp_text,
    _truncate_hash, MIN_STAMP_WIDTH_MM, MIN_STAMP_HEIGHT_MM, MIN_FONT_PT,
)
from pdfsigner.settings import StampProfile


def test_create_stamp_image(tmp_path):
    path = str(tmp_path / "stamp.png")
    result = create_stamp_image(
        path,
        owner="Test User",
        issuer="Test CA",
        serial="12345",
        thumbprint="AABBCCDD",
        reason="Test",
        valid_from="01.01.2025",
        valid_to="01.01.2027",
    )
    assert os.path.exists(result)
    assert os.path.getsize(result) > 0


def test_create_stamp_with_profile(tmp_path):
    from pdfsigner import os
    path = str(tmp_path / "stamp_profile.png")
    profile = StampProfile(width_mm=120, height_mm=45)
    result = create_stamp_image(path, owner="User", profile=profile)
    assert os.path.exists(result)


def test_validate_stamp_size_ok():
    errors = validate_stamp_size(100, 50, 8)
    assert len(errors) == 0


def test_validate_stamp_size_too_small():
    errors = validate_stamp_size(40, 15, 4)
    assert len(errors) > 0


def test_build_stamp_text():
    profile = StampProfile()
    text = build_stamp_text(
        profile, owner="Test User", issuer="Test CA",
        serial="12345", reason="Test reason",
        valid_from="01.01.2025", valid_to="01.01.2027",
    )
    assert "Документ подписан электронной подписью" in text
    assert "Test User" in text
    assert "Test CA" in text


def test_build_stamp_text_minimal():
    profile = StampProfile(
        include_owner=False, include_issuer=False,
        include_date=False, include_reason=False,
        include_serial=False, include_validity=False,
    )
    text = build_stamp_text(profile, owner="User", issuer="CA",
                           serial="123", reason="reason")
    assert "User" not in text
    assert "CA" not in text


def test_truncate_hash():
    assert _truncate_hash("AABB") == "AABB"
    assert _truncate_hash("AABBCCDDEE11223344556677889900") == "AABBCCDDEE112233...77889900"
    assert _truncate_hash("AA BB CC") == "AABBCC"


import os
