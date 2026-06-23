import os
import time
from typing import Optional
from pdfsigner.settings import StampProfile


STAMP_BLUE = (0, 74, 173)
MM_TO_PX = 3.78
MIN_STAMP_WIDTH_MM = 60
MIN_STAMP_HEIGHT_MM = 20
MIN_FONT_PT = 6


def create_stamp_image(
    path: str,
    owner: str = "",
    issuer: str = "",
    serial: str = "",
    thumbprint: str = "",
    reason: str = "",
    valid_from: str = "",
    valid_to: str = "",
    signature_fn: str = "",
    profile: Optional[StampProfile] = None,
) -> str:
    from PIL import Image, ImageDraw, ImageFont

    if profile is None:
        profile = StampProfile()
    profile.normalize()

    w_mm = max(MIN_STAMP_WIDTH_MM, profile.width_mm)
    h_mm = max(MIN_STAMP_HEIGHT_MM, profile.height_mm)
    w = int(w_mm * MM_TO_PX)
    h = int(h_mm * MM_TO_PX)

    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    blue = STAMP_BLUE + (255,)
    light_blue = STAMP_BLUE + (180,)

    font_size = max(MIN_FONT_PT, int(profile.font_size * MM_TO_PX / 3))
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(MIN_FONT_PT, font_size - 2))
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size + 2)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans.ttf", font_size)
            small_font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans.ttf", max(MIN_FONT_PT, font_size - 2))
            title_font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", font_size + 2)
        except OSError:
            font = ImageFont.load_default()
            small_font = font
            title_font = font

    draw.rectangle([0, 0, w - 1, h - 1], outline=light_blue, width=2)

    header = "Документ подписан электронной подписью"
    draw.text((8, 6), header, fill=blue, font=title_font)
    draw.line([(8, 6 + font_size + 6), (w - 8, 6 + font_size + 6)], fill=light_blue, width=1)

    left_x = 8
    right_x = w // 2
    col_w = w // 2 - 16
    y = 6 + font_size + 14
    line_h = font_size + 6

    left_lines = []
    if owner:
        left_lines.append(f"Владелец: {owner}")
    if profile.include_issuer and issuer:
        left_lines.append(f"Издатель: {issuer}")
    if profile.include_date:
        left_lines.append(f"Дата: {time.strftime('%d.%m.%Y')}")
    if profile.include_reason and reason:
        left_lines.append(f"Причина: {reason}")

    right_lines = []
    if serial:
        right_lines.append(f"Серийный: {serial}")
    if profile.include_validity and valid_from and valid_to:
        right_lines.append(f"Действителен: {valid_from} - {valid_to}")
    if thumbprint:
        right_lines.append(f"SHA1: {_truncate_hash(thumbprint)}")
    if signature_fn:
        right_lines.append(f"ЭП: {signature_fn}")

    for i, line in enumerate(left_lines):
        if y + i * line_h > h - 10:
            break
        draw.text((left_x, y + i * line_h), line, fill=blue, font=font)

    for i, line in enumerate(right_lines):
        if y + i * line_h > h - 10:
            break
        draw.text((right_x, y + i * line_h), line, fill=blue, font=small_font)

    img.save(path, "PNG")
    return path


def _truncate_hash(hash_str: str) -> str:
    h = hash_str.replace(" ", "").upper()
    if len(h) <= 24:
        return h
    return h[:16] + "..." + h[-8:]


def validate_stamp_size(width_mm: float, height_mm: float, font_size: float) -> list:
    errors = []
    if width_mm < MIN_STAMP_WIDTH_MM:
        errors.append(f"Размер штампа не может быть меньше {MIN_STAMP_WIDTH_MM}x{MIN_STAMP_HEIGHT_MM} мм.")
    if height_mm < MIN_STAMP_HEIGHT_MM:
        errors.append(f"Размер штампа не может быть меньше {MIN_STAMP_WIDTH_MM}x{MIN_STAMP_HEIGHT_MM} мм.")
    if font_size < MIN_FONT_PT:
        errors.append(f"Размер шрифта не может быть меньше {MIN_FONT_PT} pt.")
    return errors


def build_stamp_text(profile: StampProfile, owner: str, issuer: str, serial: str,
                     reason: str, valid_from: str = "", valid_to: str = "") -> str:
    lines = ["Документ подписан электронной подписью"]
    if profile.include_owner and owner:
        lines.append(f"Владелец: {owner}")
    if profile.include_issuer and issuer:
        lines.append(f"Издатель: {issuer}")
    if profile.include_date:
        lines.append(f"Дата: {time.strftime('%d.%m.%Y')}")
    if profile.include_reason and reason:
        lines.append(f"Причина: {reason}")
    if profile.include_serial and serial:
        lines.append(f"Серийный номер: {serial}")
    if profile.include_validity and valid_from and valid_to:
        lines.append(f"Действителен: {valid_from} - {valid_to}")
    return "\n".join(lines)
