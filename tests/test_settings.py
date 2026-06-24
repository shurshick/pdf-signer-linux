import os
import json
import tempfile
import pytest
from pdfsigner.settings import (
    StampProfile, ApplicationSettings, BUILT_IN_PROFILES,
    load_settings, save_settings, export_settings, import_settings,
)


def test_stamp_profile_defaults():
    p = StampProfile()
    assert p.name == "standard"
    assert p.position == "bottom-right"
    assert p.width_mm == 90.0
    assert p.height_mm == 35.0


def test_stamp_profile_normalize():
    p = StampProfile(width_mm=10, height_mm=5, font_size=2)
    p.normalize()
    assert p.width_mm == 40.0
    assert p.height_mm == 15.0
    assert p.font_size == 4.0


def test_stamp_profile_to_dict():
    p = StampProfile(name="test", width_mm=100)
    d = p.to_dict()
    assert d["name"] == "test"
    assert d["width_mm"] == 100


def test_stamp_profile_from_dict():
    d = {"name": "custom", "pages": "1-3", "logo_path": "/tmp/logo.png"}
    p = StampProfile.from_dict(d)
    assert p.name == "custom"
    assert p.pages == "1-3"
    assert p.logo_path == "/tmp/logo.png"


def test_stamp_profile_from_dict_ignores_unknown():
    d = {"name": "custom", "unknown_field": 123}
    p = StampProfile.from_dict(d)
    assert p.name == "custom"


def test_application_settings_defaults():
    s = ApplicationSettings()
    assert s.verify_after_signing is False
    assert s.stamp_profile.name == "standard"


def test_application_settings_to_dict():
    s = ApplicationSettings(verify_after_signing=True)
    d = s.to_dict()
    assert d["verify_after_signing"] is True
    assert "stamp_profile" in d


def test_application_settings_from_dict():
    d = {
        "verify_after_signing": True,
        "stamp_profile": {"name": "minimal", "pages": "1"}
    }
    s = ApplicationSettings.from_dict(d)
    assert s.verify_after_signing is True
    assert s.stamp_profile.name == "minimal"


def test_built_in_profiles():
    assert "minimal" in BUILT_IN_PROFILES
    assert "standard" in BUILT_IN_PROFILES
    assert "detailed" in BUILT_IN_PROFILES
    assert BUILT_IN_PROFILES["minimal"].width_mm == 70
    assert BUILT_IN_PROFILES["detailed"].width_mm == 120


def test_save_and_load_settings():
    with tempfile.TemporaryDirectory() as tmpdir:
        from pdfsigner import SETTINGS_DIR, SETTINGS_FILE
        orig_dir = os.environ.get("PDFSIGNER_SETTINGS_DIR")
        os.environ["PDFSIGNER_SETTINGS_DIR"] = tmpdir

        s = ApplicationSettings(verify_after_signing=True)
        s.stamp_profile.name = "custom"
        save_settings(s)

        loaded = load_settings()
        assert loaded.verify_after_signing is True
        assert loaded.stamp_profile.name == "custom"

        if orig_dir:
            os.environ["PDFSIGNER_SETTINGS_DIR"] = orig_dir
        else:
            os.environ.pop("PDFSIGNER_SETTINGS_DIR", None)


def test_export_import_settings():
    with tempfile.TemporaryDirectory() as tmpdir:
        s = ApplicationSettings(verify_after_signing=True)
        s.stamp_profile.logo_path = "/tmp/test.png"

        export_path = os.path.join(tmpdir, "export.json")
        export_settings(export_path, s)

        assert os.path.exists(export_path)
        with open(export_path) as f:
            data = json.load(f)
        assert data["verify_after_signing"] is True
        assert data["stamp_profile"]["logo_path"] == "/tmp/test.png"

        imported = import_settings(export_path)
        assert imported.verify_after_signing is True
        assert imported.stamp_profile.logo_path == "/tmp/test.png"
