import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

from pdfsigner import SETTINGS_DIR, SETTINGS_FILE


@dataclass
class StampProfile:
    name: str = "standard"
    pages: str = "1-"
    position: str = "bottom-right"
    custom_x: float = 36
    custom_y: float = 36
    width_mm: float = 90
    height_mm: float = 35
    font_size: float = 8
    min_font_size: float = 6
    opacity: float = 1.0
    scale: float = 0.96
    include_owner: bool = True
    include_issuer: bool = True
    include_date: bool = True
    include_reason: bool = True
    include_serial: bool = True
    include_validity: bool = True
    include_custom: bool = False
    custom_text: str = ""
    auto_place: bool = False
    logo_path: str = ""
    logo_scale: int = 100

    def normalize(self):
        self.width_mm = max(40, min(200, self.width_mm))
        self.height_mm = max(15, min(100, self.height_mm))
        self.font_size = max(4, min(16, self.font_size))
        self.min_font_size = max(4, min(self.font_size, self.min_font_size))
        self.opacity = max(0.1, min(1.0, self.opacity))
        self.scale = max(0.1, min(2.0, self.scale))
        self.logo_scale = max(100, min(300, self.logo_scale))

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "StampProfile":
        valid = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in valid})


@dataclass
class ApplicationSettings:
    verify_after_signing: bool = False
    stamp_profile: StampProfile = field(default_factory=StampProfile)

    def to_dict(self):
        return {
            "verify_after_signing": self.verify_after_signing,
            "stamp_profile": self.stamp_profile.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ApplicationSettings":
        s = cls()
        s.verify_after_signing = d.get("verify_after_signing", False)
        if "stamp_profile" in d:
            s.stamp_profile = StampProfile.from_dict(d["stamp_profile"])
        return s


BUILT_IN_PROFILES = {
    "minimal": StampProfile(
        name="minimal", pages="1", width_mm=70, height_mm=25,
        font_size=7, min_font_size=6, include_issuer=False,
        include_reason=False, include_validity=True,
    ),
    "standard": StampProfile(name="standard"),
    "detailed": StampProfile(
        name="detailed", width_mm=120, height_mm=45,
        font_size=8, min_font_size=6,
    ),
}


def load_settings() -> ApplicationSettings:
    if not os.path.exists(SETTINGS_FILE):
        return ApplicationSettings()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ApplicationSettings.from_dict(data)
    except Exception:
        return ApplicationSettings()


def save_settings(settings: ApplicationSettings):
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings.to_dict(), f, indent=2, ensure_ascii=False)


def export_settings(path: str, settings: ApplicationSettings):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings.to_dict(), f, indent=2, ensure_ascii=False)


def import_settings(path: str) -> ApplicationSettings:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ApplicationSettings.from_dict(data)
