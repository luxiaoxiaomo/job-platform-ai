"""
Resume text extraction strategies.
"""

from pathlib import Path
import shutil
import tempfile
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET

from app.core.config import settings
from app.modules.company_certification import ocr as shared_ocr


class ResumeExtractionError(ValueError):
    """Raised when a resume file cannot be extracted."""


PDF_TEXT_MIN_CHARS = 20


def extract_docx_text(path: Path) -> str:
    """Extract plain text from a DOCX file."""
    try:
        with ZipFile(path) as archive:
            xml_bytes = archive.read("word/document.xml")
    except (BadZipFile, KeyError) as exc:
        raise ResumeExtractionError("Invalid DOCX resume file") from exc

    root = ET.fromstring(xml_bytes)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        text = "".join(
            node.text or "" for node in paragraph.findall(".//w:t", namespace)
        ).strip()
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs).strip()


def extract_pdf_text(path: Path) -> str:
    """Extract embedded text from a text-based PDF file."""
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise ResumeExtractionError("PDF text extraction requires pypdfium2") from exc

    try:
        pdf = pdfium.PdfDocument(str(path))
    except Exception as exc:
        raise ResumeExtractionError("Invalid PDF resume file") from exc

    pages: list[str] = []
    try:
        for page_index in range(len(pdf)):
            page = pdf[page_index]
            textpage = None
            try:
                textpage = page.get_textpage()
                page_text = (textpage.get_text_range() or "").strip()
                if page_text:
                    pages.append(page_text)
            finally:
                if textpage is not None:
                    textpage.close()
                page.close()
    finally:
        close = getattr(pdf, "close", None)
        if callable(close):
            close()

    return "\n".join(pages).strip()


def extract_ocr_text(path: Path) -> str:
    """Extract text from an image-like resume file with the shared OCR engine."""
    tmp = None
    try:
        temp_parent = path.parent if path.parent.exists() else None
        tmp = tempfile.mkdtemp(prefix="resume_ocr_", dir=temp_parent)
        input_paths = shared_ocr._prepare_ocr_input_paths(path, Path(tmp))
        engine = shared_ocr._rapidocr_engine()
        lines: list[str] = []
        for input_path in input_paths:
            result = engine(
                str(input_path), text_score=settings.OCR_CONFIDENCE_THRESHOLD
            )
            lines.extend(
                str(line).strip() for line in (result.txts or []) if str(line).strip()
            )
    except Exception as exc:
        raise ResumeExtractionError(f"OCR resume extraction failed: {exc}") from exc
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)

    return "\n".join(lines).strip()


def extract_resume_text(path: Path, extension: str) -> tuple[str, str]:
    """Extract text and return the extractor name."""
    if extension == ".docx":
        return extract_docx_text(path), "docx"
    if extension == ".pdf":
        text = extract_pdf_text(path)
        if len(text.strip()) >= PDF_TEXT_MIN_CHARS:
            return text, "pdf_text"
        return extract_ocr_text(path), "rapidocr"
    raise ResumeExtractionError(f"{extension} text extraction is not available yet")
