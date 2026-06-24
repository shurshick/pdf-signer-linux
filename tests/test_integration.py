import os
import tempfile
import pytest
from pdfsigner.settings import StampProfile, ApplicationSettings, save_settings, load_settings
from pdfsigner.stamp import create_stamp_image
from pdfsigner.pdfstamp import apply_stamp
from pdfsigner.i18n import t, set_lang


def test_full_stamp_workflow():
    with tempfile.TemporaryDirectory() as tmpdir:
        stamp_path = os.path.join(tmpdir, "stamp.png")
        profile = StampProfile(
            name="test",
            width_mm=90,
            height_mm=35,
            font_size=8,
            include_issuer=True,
            include_date=True,
        )
        create_stamp_image(
            stamp_path,
            owner="Test User",
            issuer="Test CA",
            serial="12345",
            thumbprint="ABCDEF1234567890",
            reason="Test signing",
            valid_from="01.01.2026",
            valid_to="31.12.2026",
            signature_fn="test.sig",
            profile=profile,
        )
        assert os.path.exists(stamp_path)
        assert os.path.getsize(stamp_path) > 0


def test_i18n_ru():
    set_lang("ru")
    assert t("files") == "PDF-файлы"
    assert t("sign") == "Подписать"
    assert t("ready") == "Готово"


def test_i18n_en():
    set_lang("en")
    assert t("files") == "PDF files"
    assert t("sign") == "Sign"
    assert t("ready") == "Ready"


def test_i18n_format():
    set_lang("ru")
    result = t("file_count", count=5, size="1.2 MB")
    assert "5" in result
    assert "1.2 MB" in result


def test_i18n_missing_key():
    set_lang("ru")
    result = t("nonexistent_key")
    assert result == "nonexistent_key"


def test_settings_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_path = os.path.join(tmpdir, "settings.json")
        from pdfsigner import SETTINGS_FILE
        import pdfsigner
        pdfsigner.SETTINGS_FILE = settings_path

        s = ApplicationSettings(verify_after_signing=True)
        s.stamp_profile.name = "custom"
        s.stamp_profile.logo_path = "/tmp/logo.png"
        save_settings(s)

        loaded = load_settings()
        assert loaded.verify_after_signing is True
        assert loaded.stamp_profile.name == "custom"
        assert loaded.stamp_profile.logo_path == "/tmp/logo.png"


def test_stamp_profile_auto_place():
    p = StampProfile(auto_place=True)
    assert p.auto_place is True


def test_stamp_profile_custom_position():
    p = StampProfile(use_custom_position=True, custom_x=100, custom_y=200)
    assert p.use_custom_position is True
    assert p.custom_x == 100
    assert p.custom_y == 200


def test_stamp_profile_logo():
    p = StampProfile(logo_path="/tmp/test.png", logo_scale=200)
    assert p.logo_path == "/tmp/test.png"
    assert p.logo_scale == 200
