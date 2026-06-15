"""
Resume text extraction strategies.
"""
from pathlib import Path
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET


class ResumeExtractionError(ValueError):
    """Raised when a resume file cannot be extracted."""


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
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", namespace)).strip()
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs).strip()


def extract_resume_text(path: Path, extension: str) -> tuple[str, str]:
    """Extract text and return the extractor name."""
    if extension == ".docx":
        return extract_docx_text(path), "docx"
    raise ResumeExtractionError(f"{extension} text extraction is not available yet")
