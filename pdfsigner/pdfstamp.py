import os
from typing import Optional

from pdfsigner.settings import StampProfile


def apply_stamp(
    input_pdf: str,
    output_pdf: str,
    stamp_image: str,
    pages: str = "1-",
    profile: Optional[StampProfile] = None,
) -> str:
    if not os.path.isfile(input_pdf):
        raise FileNotFoundError(f"Input PDF not found: {input_pdf}")
    if not os.path.isfile(stamp_image):
        raise FileNotFoundError(f"Stamp image not found: {stamp_image}")

    if profile is None:
        profile = StampProfile()
    profile.normalize()

    try:
        return _apply_stamp_pymupdf(input_pdf, output_pdf, stamp_image, pages, profile)
    except ImportError:
        pass

    try:
        return _apply_stamp_pypdf(input_pdf, output_pdf, stamp_image, pages, profile)
    except ImportError:
        pass

    raise RuntimeError(
        "No PDF library available. Install PyMuPDF: pip install PyMuPDF"
    )


def _apply_stamp_pymupdf(
    input_pdf: str, output_pdf: str, stamp_image: str,
    pages: str, profile: StampProfile,
) -> str:
    import fitz

    doc = fitz.open(input_pdf)
    stamp_doc = fitz.open(stamp_image)
    stamp_page = stamp_doc[0]

    page_indices = _parse_page_range(pages, len(doc))

    stamp_width_pt = profile.width_mm * 72.0 / 25.4
    stamp_height_pt = profile.height_mm * 72.0 / 25.4

    margin = 36

    for page_idx in page_indices:
        if page_idx < 0 or page_idx >= len(doc):
            continue
        page = doc[page_idx]
        rect = page.rect

        position = profile.position if hasattr(profile, 'position') else "bottom-right"

        if position == "bottom-right":
            x = rect.width - stamp_width_pt - margin
            y = margin
        elif position == "bottom-left":
            x = margin
            y = margin
        elif position == "top-right":
            x = rect.width - stamp_width_pt - margin
            y = rect.height - stamp_height_pt - margin
        elif position == "top-left":
            x = margin
            y = rect.height - stamp_height_pt - margin
        else:
            x = rect.width - stamp_width_pt - margin
            y = margin

        stamp_rect = fitz.Rect(x, y, x + stamp_width_pt, y + stamp_height_pt)
        page.insert_image(stamp_rect, filename=stamp_image, overlay=True)

    doc.save(output_pdf)
    doc.close()
    stamp_doc.close()
    return output_pdf


def _apply_stamp_pypdf(
    input_pdf: str, output_pdf: str, stamp_image: str,
    pages: str, profile: StampProfile,
) -> str:
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    import io

    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    stamp_width_pt = profile.width_mm * 72.0 / 25.4
    stamp_height_pt = profile.height_mm * 72.0 / 25.4

    page_indices = _parse_page_range(pages, len(reader.pages))

    position = profile.position if hasattr(profile, 'position') else "bottom-right"

    for i, page in enumerate(reader.pages):
        if i in page_indices:
            overlay = _create_overlay(stamp_image, stamp_width_pt, stamp_height_pt, position)
            page.merge_page(overlay)
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

    return output_pdf


def _create_overlay(stamp_image: str, width: float, height: float, position: str = "bottom-right"):
    from pypdf import PdfReader
    import io
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    img = ImageReader(stamp_image)

    page_width = 595
    page_height = 842
    margin = 36

    if position == "bottom-right":
        x = page_width - width - margin
        y = margin
    elif position == "bottom-left":
        x = margin
        y = margin
    elif position == "top-right":
        x = page_width - width - margin
        y = page_height - height - margin
    elif position == "top-left":
        x = margin
        y = page_height - height - margin
    else:
        x = page_width - width - margin
        y = margin

    c.drawImage(img, x, y, width, height, mask="auto")
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def _parse_page_range(pages: str, total: int) -> set:
    result = set()
    if not pages or pages.strip() == "1-":
        return set(range(total))

    for part in pages.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start = max(1, int(start)) - 1
            end = min(total, int(end) if end else total)
            result.update(range(start, end))
        else:
            idx = int(part) - 1
            if 0 <= idx < total:
                result.add(idx)

    return result
