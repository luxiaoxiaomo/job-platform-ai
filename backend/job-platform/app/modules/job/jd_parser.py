"""
JD document extraction and lightweight field parsing.
"""
from __future__ import annotations

import asyncio
import csv
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from zipfile import ZipFile

from app.core.config import settings
from app.modules.company_certification.ocr import _prepare_ocr_input_paths, _rapidocr_engine


DOCUMENT_EXTENSIONS = {".txt", ".md", ".csv", ".docx", ".xlsx"}
OCR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic", ".heif", ".pdf"}
ALLOWED_JD_EXTENSIONS = DOCUMENT_EXTENSIONS | OCR_EXTENSIONS


@dataclass
class JdParseResult:
    source: str
    raw_text: str
    confidence: float
    title: Optional[str]
    city: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    experience: Optional[str]
    education: Optional[str]
    description: Optional[str]
    requirement: Optional[str]
    benefits: Optional[str]
    tags: list[str]
    missing_fields: list[str]


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def _xml_text(xml_content: bytes) -> list[str]:
    root = ET.fromstring(xml_content)
    texts: list[str] = []
    for node in root.iter():
        if node.tag.endswith("}t") or node.tag.endswith("}v") or node.tag == "t" or node.tag == "v":
            if node.text and node.text.strip():
                texts.append(node.text.strip())
    return texts


def _extract_docx_text(file_path: Path) -> str:
    with ZipFile(file_path) as archive:
        names = [
            name
            for name in archive.namelist()
            if name.startswith("word/") and name.endswith(".xml")
        ]
        chunks: list[str] = []
        for name in names:
            if name == "word/document.xml" or name.startswith("word/header") or name.startswith("word/footer"):
                chunks.extend(_xml_text(archive.read(name)))
    return "\n".join(chunks)


def _extract_xlsx_text(file_path: Path) -> str:
    with ZipFile(file_path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_strings = _xml_text(archive.read("xl/sharedStrings.xml"))

        values: list[str] = []
        sheet_names = [
            name
            for name in archive.namelist()
            if name.startswith("xl/worksheets/") and name.endswith(".xml")
        ]
        for name in sheet_names:
            root = ET.fromstring(archive.read(name))
            for cell in root.iter():
                if not cell.tag.endswith("}c") and cell.tag != "c":
                    continue
                cell_type = cell.attrib.get("t")
                value_node = next(
                    (
                        child
                        for child in cell
                        if child.tag.endswith("}v") or child.tag.endswith("}t") or child.tag in {"v", "t"}
                    ),
                    None,
                )
                if value_node is None or not value_node.text:
                    continue
                raw_value = value_node.text.strip()
                if cell_type == "s" and raw_value.isdigit():
                    index = int(raw_value)
                    if index < len(shared_strings):
                        values.append(shared_strings[index])
                else:
                    values.append(raw_value)
    return "\n".join(values)


def _extract_csv_text(content: bytes) -> str:
    decoded = _decode_text(content)
    rows = csv.reader(decoded.splitlines())
    return "\n".join(" ".join(cell.strip() for cell in row if cell.strip()) for row in rows)


def _run_document_ocr_sync(file_path: Path) -> tuple[str, float, str]:
    with TemporaryDirectory(prefix="jd_ocr_") as tmp:
        input_paths = _prepare_ocr_input_paths(file_path, Path(tmp))
        engine = _rapidocr_engine()
        lines: list[str] = []
        scores: list[float] = []
        for input_path in input_paths:
            result = engine(str(input_path), text_score=settings.OCR_CONFIDENCE_THRESHOLD)
            lines.extend(result.txts or [])
            scores.extend(result.scores or [])
    confidence = round(sum(scores) / len(scores), 4) if scores else 0.0
    return "\n".join(line.strip() for line in lines if str(line).strip()), confidence, "rapidocr"


async def extract_jd_text(file_path: Path, original_name: str, content: bytes) -> tuple[str, float, str]:
    suffix = file_path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return _decode_text(content), 1.0, "text"
    if suffix == ".csv":
        return _extract_csv_text(content), 1.0, "csv"
    if suffix == ".docx":
        return await asyncio.to_thread(_extract_docx_text, file_path), 1.0, "docx"
    if suffix == ".xlsx":
        return await asyncio.to_thread(_extract_xlsx_text, file_path), 1.0, "xlsx"
    if suffix in OCR_EXTENSIONS:
        if settings.OCR_PROVIDER.strip().lower() in {"mock", "dev_mock"}:
            return _mock_jd_text(original_name), 0.78, "dev_mock"
        return await asyncio.to_thread(_run_document_ocr_sync, file_path)
    return "", 0.0, "unsupported"


def _mock_jd_text(original_name: str) -> str:
    title = Path(original_name).stem or "Frontend Developer"
    return (
        f"Job title: {title}\n"
        "City: Shanghai\n"
        "Salary: 15-25K\n"
        "Experience: 1-3 years\n"
        "Education: Bachelor\n"
        "Responsibilities:\n"
        "Build and maintain the recruiting platform frontend, integrate APIs, and improve page performance.\n"
        "Requirements:\n"
        "Familiar with React, component development, and real project delivery.\n"
        "Benefits:\n"
        "Social insurance, annual leave, flexible work."
    )


def _normalize_text(text: str) -> str:
    return re.sub(r"\r\n?", "\n", text or "").strip()


def _compact_lines(text: str) -> list[str]:
    return [line.strip() for line in _normalize_text(text).splitlines() if line.strip()]


def _label_value(lines: list[str], labels: tuple[str, ...]) -> Optional[str]:
    label_pattern = "|".join(re.escape(label) for label in labels)
    pattern = re.compile(rf"^(?:{label_pattern})\s*[:：]\s*(.+)$", re.IGNORECASE)
    for line in lines:
        if match := pattern.search(line):
            return match.group(1).strip()
    for index, line in enumerate(lines):
        if any(label.lower() == line.lower().rstrip(":：") for label in labels):
            if index + 1 < len(lines):
                return lines[index + 1].strip()
    return None


def _section_text(lines: list[str], start_labels: tuple[str, ...], stop_labels: tuple[str, ...]) -> Optional[str]:
    start_index: Optional[int] = None
    for index, line in enumerate(lines):
        normalized = line.rstrip(":：").lower()
        if any(label.lower() == normalized for label in start_labels) or any(
            line.lower().startswith(f"{label.lower()}:") or line.startswith(f"{label}：")
            for label in start_labels
        ):
            start_index = index
            inline = line.split(":", 1)[1].strip() if ":" in line else ""
            inline = line.split("：", 1)[1].strip() if "：" in line else inline
            collected = [inline] if inline else []
            for next_line in lines[index + 1 :]:
                next_normalized = next_line.rstrip(":：").lower()
                if any(label.lower() == next_normalized for label in stop_labels):
                    break
                collected.append(next_line)
            return "\n".join(item for item in collected if item).strip() or None
    if start_index is None:
        return None
    return None


def _salary(text: str) -> tuple[Optional[int], Optional[int]]:
    patterns = [
        r"(\d{1,3})\s*[kK千]\s*[-~至到]\s*(\d{1,3})\s*[kK千]?",
        r"(\d{1,3})\s*[-~至到]\s*(\d{1,3})\s*[kK千]",
    ]
    for pattern in patterns:
        if match := re.search(pattern, text):
            low = int(match.group(1))
            high = int(match.group(2))
            if high >= low:
                return low, high
    return None, None


def _infer_title(lines: list[str]) -> Optional[str]:
    value = _label_value(lines, ("岗位名称", "职位名称", "招聘岗位", "岗位", "职位", "Job title", "Title"))
    if value:
        return value[:100]
    for line in lines[:8]:
        cleaned = re.sub(r"^(招聘|急聘|诚聘)\s*", "", line).strip()
        if 2 <= len(cleaned) <= 40 and not re.search(r"[:：]|薪资|城市|地点|要求|职责", cleaned):
            return cleaned
    return None


def _infer_tags(text: str) -> list[str]:
    keywords = [
        "React",
        "Vue",
        "JavaScript",
        "TypeScript",
        "Python",
        "Java",
        "FastAPI",
        "SQL",
        "Excel",
        "销售",
        "运营",
        "客服",
        "设计",
        "产品",
    ]
    lowered = text.lower()
    tags = []
    for keyword in keywords:
        if keyword.lower() in lowered and keyword not in tags:
            tags.append(keyword)
    return tags[:10]


def parse_jd_fields(raw_text: str, source: str, confidence: float) -> JdParseResult:
    text = _normalize_text(raw_text)
    lines = _compact_lines(text)
    salary_min, salary_max = _salary(text)
    stop_labels = (
        "任职要求",
        "职位要求",
        "岗位要求",
        "要求",
        "Requirements",
        "福利待遇",
        "薪资福利",
        "Benefits",
        "工作职责",
        "岗位职责",
        "职责",
        "Responsibilities",
    )
    description = _section_text(
        lines,
        ("工作职责", "岗位职责", "职位描述", "岗位描述", "职责", "Responsibilities"),
        stop_labels,
    )
    requirement = _section_text(
        lines,
        ("任职要求", "职位要求", "岗位要求", "要求", "Requirements"),
        stop_labels,
    )
    benefits = _section_text(
        lines,
        ("福利待遇", "薪资福利", "福利", "Benefits"),
        ("工作职责", "岗位职责", "任职要求", "职位要求", "Requirements", "Responsibilities"),
    )

    title = _infer_title(lines)
    city = _label_value(lines, ("工作城市", "工作地点", "地点", "城市", "City", "Location"))
    experience = _label_value(lines, ("经验", "工作经验", "Experience"))
    education = _label_value(lines, ("学历", "Education"))
    if not city:
        city_match = re.search(r"(北京|上海|广州|深圳|杭州|南京|苏州|成都|武汉|西安|重庆|天津|青岛|厦门)", text)
        city = city_match.group(1) if city_match else None

    fallback_body = "\n".join(lines[:12]).strip()
    if not description and fallback_body:
        description = fallback_body[:1500]

    fields = {
        "title": title,
        "city": city,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "description": description,
        "requirement": requirement,
    }
    missing = [field for field, value in fields.items() if value in (None, "")]

    return JdParseResult(
        source=source,
        raw_text=text,
        confidence=confidence,
        title=title,
        city=city,
        salary_min=salary_min,
        salary_max=salary_max,
        experience=experience,
        education=education,
        description=description,
        requirement=requirement,
        benefits=benefits,
        tags=_infer_tags(text),
        missing_fields=missing,
    )
