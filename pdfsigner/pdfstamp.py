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

    for page_idx in page_indices:
        if page_idx < 0 or page_idx >= len(doc):
            continue
        page = doc[page_idx]
        rect = page.rect

        x = rect.width - stamp_width_pt - 36
        y = 36

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

    for i, page in enumerate(reader.pages):
        if i in page_indices:
            overlay = _create_overlay(stamp_image, stamp_width_pt, stamp_height_pt)
            page.merge_page(overlay)
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

    return output_pdf


def _create_overlay(stamp_image: str, width: float, height: float):
    from pypdf import PdfReader
    import io
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    img = ImageReader(stamp_image)
    x = 595 - width - 36
    y = 842 - height - 36
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
