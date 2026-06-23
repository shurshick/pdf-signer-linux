import os
import time
from pdfsigner.settings import StampProfile, ApplicationSettings, BUILT_IN_PROFILES


def test_default_stamp_profile():
    p = StampProfile()
    assert p.name == "standard"
    assert p.width_mm == 90
    assert p.height_mm == 35
    assert p.font_size == 8
    assert p.include_owner is True


def test_stamp_profile_normalize():
    p = StampProfile(width_mm=10, height_mm=5, font_size=2, opacity=2.0, logo_scale=50)
    p.normalize()
    assert p.width_mm == 40
    assert p.height_mm == 15
    assert p.font_size == 4
    assert p.opacity == 1.0
    assert p.logo_scale == 100


def test_stamp_profile_to_dict():
    p = StampProfile(name="test", width_mm=100)
    d = p.to_dict()
    assert d["name"] == "test"
    assert d["width_mm"] == 100


def test_stamp_profile_from_dict():
    d = {"name": "custom", "width_mm": 80, "height_mm": 30}
    p = StampProfile.from_dict(d)
    assert p.name == "custom"
    assert p.width_mm == 80


def test_built_in_profiles():
    assert "minimal" in BUILT_IN_PROFILES
    assert "standard" in BUILT_IN_PROFILES
    assert "detailed" in BUILT_IN_PROFILES
    assert BUILT_IN_PROFILES["minimal"].width_mm == 70
    assert BUILT_IN_PROFILES["detailed"].width_mm == 120


def test_application_settings():
    s = ApplicationSettings()
    assert s.verify_after_signing is False
    d = s.to_dict()
    s2 = ApplicationSettings.from_dict(d)
    assert s2.verify_after_signing is False


def test_export_import_settings(tmp_path):
    from pdfsigner.settings import export_settings, import_settings

    settings = ApplicationSettings(verify_after_signing=True)
    path = str(tmp_path / "settings.json")
    export_settings(path, settings)
    imported = import_settings(path)
    assert imported.verify_after_signing is True
