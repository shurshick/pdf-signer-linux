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
    lang: str = "ru",
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

    logo_img = None
    logo_offset_x = 0
    if profile.logo_path and os.path.isfile(profile.logo_path):
        try:
            logo_img = Image.open(profile.logo_path)
            if logo_img.mode != "RGBA":
                logo_img = logo_img.convert("RGBA")
            max_logo_h = int(h * 0.6)
            max_logo_w = int(w * 0.25)
            logo_img.thumbnail((max_logo_w, max_logo_h), Image.LANCZOS)
            scale_factor = profile.logo_scale / 100.0
            new_w = int(logo_img.width * scale_factor)
            new_h = int(logo_img.height * scale_factor)
            logo_img = logo_img.resize((new_w, new_h), Image.LANCZOS)
            logo_offset_x = new_w + 4
        except Exception:
            logo_img = None

    if logo_img:
        logo_x = 6
        logo_y = (h - logo_img.height) // 2
        img.paste(logo_img, (logo_x, logo_y), logo_img)

    is_ru = lang == "ru"
    header = "Документ подписан электронной подписью" if is_ru else "Document signed electronically"
    text_x = 8 + logo_offset_x
    draw.text((text_x, 6), header, fill=blue, font=title_font)
    draw.line([(text_x, 6 + font_size + 6), (w - 8, 6 + font_size + 6)], fill=light_blue, width=1)

    left_x = text_x
    right_x = w // 2 + logo_offset_x // 2
    y = 6 + font_size + 14
    line_h = font_size + 6

    left_lines = []
    if owner:
        left_lines.append(f"{'Владелец' if is_ru else 'Owner'}: {owner}")
    if profile.include_issuer and issuer:
        left_lines.append(f"{'Издатель' if is_ru else 'Issuer'}: {issuer}")
    if profile.include_date:
        left_lines.append(f"{'Дата' if is_ru else 'Date'}: {time.strftime('%d.%m.%Y')}")
    if profile.include_reason and reason:
        left_lines.append(f"{'Причина' if is_ru else 'Reason'}: {reason}")

    right_lines = []
    if serial:
        right_lines.append(f"{'Серийный' if is_ru else 'Serial'}: {serial}")
    if profile.include_validity and valid_from and valid_to:
        right_lines.append(f"{'Действителен' if is_ru else 'Valid'}: {valid_from} - {valid_to}")
    if thumbprint:
        right_lines.append(f"SHA1: {_truncate_hash(thumbprint)}")
    if signature_fn:
        right_lines.append(f"{'ЭП' if is_ru else 'Sig'}: {signature_fn}")

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
        errors.append(f"Stamp size cannot be smaller than {MIN_STAMP_WIDTH_MM}x{MIN_STAMP_HEIGHT_MM} mm.")
    if height_mm < MIN_STAMP_HEIGHT_MM:
        errors.append(f"Stamp size cannot be smaller than {MIN_STAMP_WIDTH_MM}x{MIN_STAMP_HEIGHT_MM} mm.")
    if font_size < MIN_FONT_PT:
        errors.append(f"Font size cannot be smaller than {MIN_FONT_PT} pt.")
    return errors


def build_stamp_text(profile: StampProfile, owner: str, issuer: str, serial: str,
                     reason: str, valid_from: str = "", valid_to: str = "",
                     lang: str = "ru") -> str:
    is_ru = lang == "ru"
    header = "Документ подписан электронной подписью" if is_ru else "Document signed electronically"
    lines = [header]
    if profile.include_owner and owner:
        lines.append(f"{'Владелец' if is_ru else 'Owner'}: {owner}")
    if profile.include_issuer and issuer:
        lines.append(f"{'Издатель' if is_ru else 'Issuer'}: {issuer}")
    if profile.include_date:
        lines.append(f"{'Дата' if is_ru else 'Date'}: {time.strftime('%d.%m.%Y')}")
    if profile.include_reason and reason:
        lines.append(f"{'Причина' if is_ru else 'Reason'}: {reason}")
    if profile.include_serial and serial:
        lines.append(f"{'Серийный номер' if is_ru else 'Serial number'}: {serial}")
    if profile.include_validity and valid_from and valid_to:
        lines.append(f"{'Действителен' if is_ru else 'Valid'}: {valid_from} - {valid_to}")
    if profile.include_custom and profile.custom_text:
        lines.append(profile.custom_text)
    return "\n".join(lines)


def find_smart_placement(pdf_path: str, stamp_w: float, stamp_h: float) -> tuple:
    try:
        import fitz
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            doc.close()
            return (36.0, 36.0)
        page = doc[0]
        blocks = page.get_text("blocks")
        text_rects = []
        for b in blocks:
            if b[6] == 0:
                text_rects.append(fitz.Rect(b[:4]))
        doc.close()
        if not text_rects:
            return (36.0, 36.0)
        page_rect = page.rect
        margin = 36.0
        candidates = [
            (page_rect.width - stamp_w - margin, margin),
            (margin, margin),
            (page_rect.width - stamp_w - margin, page_rect.height - stamp_h - margin),
            (margin, page_rect.height - stamp_h - margin),
        ]
        for cx, cy in candidates:
            stamp_rect = fitz.Rect(cx, cy, cx + stamp_w, cy + stamp_h)
            overlap = False
            for tr in text_rects:
                if stamp_rect.intersects(tr):
                    overlap = True
                    break
            if not overlap:
                return (cx, cy)
        return (page_rect.width - stamp_w - margin, margin)
    except ImportError:
        return (36.0, 36.0)
    except Exception:
        return (36.0, 36.0)
