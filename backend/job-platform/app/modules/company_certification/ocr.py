"""
Business license OCR providers and field extraction.
"""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable, Optional, Sequence

from app.core.config import settings


@dataclass
class BusinessLicenseOcrResult:
    company_name: Optional[str]
    unified_social_credit_code: Optional[str]
    legal_representative: Optional[str]
    registered_address: Optional[str]
    confidence: float
    source: str
    raw_text: Optional[str]


_CREDIT_CODE_RE = re.compile(r"[0-9A-Z]{18}")
_COMPANY_SUFFIX_RE = re.compile(
    r"[\u4e00-\u9fffA-Za-z0-9（）()·]{4,}"
    r"(?:有限责任公司|股份有限公司|有限公司|公司|合伙企业|个人独资企业|中心|店|厂|社)"
)
_PERSON_RE = re.compile(r"^[\u4e00-\u9fff·]{2,4}$")

_LEGAL_LABELS = ("法定代表人", "法定代表", "负责人", "经营者", "投资人")
_LABEL_WORDS = {
    "名称",
    "称",
    "类型",
    "类",
    "住所",
    "住",
    "所",
    "经营范围",
    "注册资本",
    "成立日期",
    "登记机关",
    "营业执照",
    "副本",
}
_ADDRESS_BAD_WORDS = (
    "国家企业信用",
    "公示系统",
    "经营范围",
    "信用代码",
    "统一社会",
    "营业执照",
    "登记机关",
    "市场主体",
    "二维码",
    "报送",
    "监制",
    "扫描",
    "服务",
    "销售",
    "开发",
    "咨询",
)
_ADDRESS_HEAD_RE = re.compile(
    r"[\u4e00-\u9fff]{0,8}(?:省|自治区|市)[\u4e00-\u9fff0-9A-Za-z（）()·\-号室幢栋弄楼层单元座路街道镇村园区]+"
)
_ADDRESS_TAIL_RE = re.compile(r"[\u4e00-\u9fff0-9A-Za-z（）()·\-]*(?:号|室|幢|栋|楼|层|单元|座|弄)")
_HEIF_EXTENSIONS = {".heic", ".heif"}


class OcrPreparationError(RuntimeError):
    """Raised when an uploaded file cannot be converted for OCR."""


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "").strip()


def _normalize_lines(lines: Iterable[str]) -> list[str]:
    return [cleaned for line in lines if (cleaned := _clean_text(str(line)))]


def _contains_any(text: str, words: Sequence[str]) -> bool:
    return any(word in text for word in words)


def _find_credit_code(lines: Sequence[str]) -> Optional[str]:
    compact_text = "".join(lines).upper()
    match = _CREDIT_CODE_RE.search(compact_text)
    return match.group(0) if match else None


def _find_company_name(lines: Sequence[str]) -> Optional[str]:
    candidates: list[str] = []
    for line in lines:
        if _contains_any(line, ("类型", "型", "营业执照", "国家", "公示系统")):
            continue
        if match := _COMPANY_SUFFIX_RE.search(line):
            candidate = match.group(0)
            if "公司" in candidate and len(candidate) >= 6:
                candidates.append(candidate)

    if candidates:
        return max(candidates, key=len)
    return None


def _is_person_candidate(line: str) -> bool:
    if line in _LABEL_WORDS or _contains_any(line, _LEGAL_LABELS):
        return False
    if not _PERSON_RE.match(line):
        return False
    if _contains_any(line, ("省", "市", "区", "县", "路", "街", "道", "号", "室", "幢", "公司")):
        return False
    return True


def _find_legal_representative(lines: Sequence[str]) -> Optional[str]:
    label_indexes = [
        index for index, line in enumerate(lines) if _contains_any(line, _LEGAL_LABELS)
    ]
    for index in label_indexes:
        for candidate in lines[index + 1 : index + 35]:
            if _is_person_candidate(candidate):
                return candidate

    for line in lines:
        if _is_person_candidate(line):
            return line
    return None


def _is_address_head(line: str) -> bool:
    if len(line) < 8 or _contains_any(line, _ADDRESS_BAD_WORDS):
        return False
    return bool(_ADDRESS_HEAD_RE.search(line)) and _contains_any(
        line, ("路", "街", "道", "号", "室", "幢", "栋", "楼", "镇", "村", "园")
    )


def _is_address_tail(line: str) -> bool:
    if len(line) < 2 or len(line) > 24 or _contains_any(line, _ADDRESS_BAD_WORDS):
        return False
    return bool(_ADDRESS_TAIL_RE.fullmatch(line) or _ADDRESS_TAIL_RE.search(line))


def _find_registered_address(lines: Sequence[str]) -> Optional[str]:
    for index, line in enumerate(lines):
        if not _is_address_head(line):
            continue

        parts = [line]
        if index > 0 and _is_address_tail(lines[index - 1]):
            parts.append(lines[index - 1])
        if index + 1 < len(lines) and _is_address_tail(lines[index + 1]):
            parts.append(lines[index + 1])
        return "".join(parts)

    for line in lines:
        if _is_address_tail(line) and len(line) >= 8:
            return line
    return None


def _average_score(scores: Optional[Sequence[float]]) -> float:
    if not scores:
        return 0.0
    return round(sum(float(score) for score in scores) / len(scores), 4)


def extract_business_license_fields(
    lines: Iterable[str],
    scores: Optional[Sequence[float]] = None,
    source: str = "rapidocr",
) -> BusinessLicenseOcrResult:
    normalized_lines = _normalize_lines(lines)
    return BusinessLicenseOcrResult(
        company_name=_find_company_name(normalized_lines),
        unified_social_credit_code=_find_credit_code(normalized_lines),
        legal_representative=_find_legal_representative(normalized_lines),
        registered_address=_find_registered_address(normalized_lines),
        confidence=_average_score(scores),
        source=source,
        raw_text="\n".join(normalized_lines) if normalized_lines else None,
    )


@lru_cache(maxsize=1)
def _rapidocr_engine():
    from rapidocr import RapidOCR

    return RapidOCR()


def _render_pdf_pages(file_path: Path, output_dir: Path) -> list[Path]:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:  # pragma: no cover - dependency should be installed
        raise OcrPreparationError("PDF OCR requires pypdfium2") from exc

    try:
        pdf = pdfium.PdfDocument(str(file_path))
    except Exception as exc:
        raise OcrPreparationError(f"Cannot open PDF: {exc}") from exc

    rendered_paths: list[Path] = []
    try:
        page_count = len(pdf)
        max_pages = min(page_count, max(1, int(settings.OCR_PDF_MAX_PAGES)))
        if max_pages <= 0:
            raise OcrPreparationError("PDF has no pages")

        scale = max(1.0, float(settings.OCR_PDF_RENDER_SCALE))
        for page_index in range(max_pages):
            page = pdf[page_index]
            bitmap = page.render(scale=scale)
            image = bitmap.to_pil().convert("RGB")
            rendered_path = output_dir / f"{file_path.stem}_page_{page_index + 1}.png"
            image.save(rendered_path)
            rendered_paths.append(rendered_path)
    finally:
        close = getattr(pdf, "close", None)
        if callable(close):
            close()

    return rendered_paths


def _convert_heif_to_png(file_path: Path, output_dir: Path) -> list[Path]:
    try:
        from PIL import Image
        from pillow_heif import register_heif_opener
    except ImportError as exc:  # pragma: no cover - dependency should be installed
        raise OcrPreparationError("HEIC/HEIF OCR requires pillow-heif") from exc

    register_heif_opener()
    try:
        with Image.open(file_path) as image:
            converted_path = output_dir / f"{file_path.stem}.png"
            image.convert("RGB").save(converted_path)
    except Exception as exc:
        raise OcrPreparationError(f"Cannot convert HEIC/HEIF image: {exc}") from exc

    return [converted_path]


def _prepare_ocr_input_paths(file_path: Path, output_dir: Path) -> list[Path]:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return _render_pdf_pages(file_path, output_dir)
    if suffix in _HEIF_EXTENSIONS:
        return _convert_heif_to_png(file_path, output_dir)
    return [file_path]


def _run_rapidocr_sync(file_path: Path) -> BusinessLicenseOcrResult:
    try:
        with TemporaryDirectory(prefix="business_license_ocr_") as tmp:
            input_paths = _prepare_ocr_input_paths(file_path, Path(tmp))
            lines: list[str] = []
            scores: list[float] = []
            engine = _rapidocr_engine()

            for input_path in input_paths:
                result = engine(str(input_path), text_score=settings.OCR_CONFIDENCE_THRESHOLD)
                lines.extend(result.txts or [])
                scores.extend(result.scores or [])
    except Exception as exc:  # pragma: no cover - depends on optional native OCR runtime
        return BusinessLicenseOcrResult(
            company_name=None,
            unified_social_credit_code=None,
            legal_representative=None,
            registered_address=None,
            confidence=0.0,
            source="rapidocr_error",
            raw_text=f"RapidOCR failed: {exc}",
        )

    if not lines:
        return BusinessLicenseOcrResult(
            company_name=None,
            unified_social_credit_code=None,
            legal_representative=None,
            registered_address=None,
            confidence=0.0,
            source="rapidocr_empty",
            raw_text=None,
        )
    return extract_business_license_fields(lines, scores=scores, source="rapidocr")


async def run_business_license_ocr(
    file_path: Path,
    original_name: str,
    mock_parser,
) -> BusinessLicenseOcrResult:
    provider = settings.OCR_PROVIDER.strip().lower()
    if provider in {"mock", "dev_mock"}:
        parsed = mock_parser(original_name)
        return BusinessLicenseOcrResult(
            company_name=parsed["company_name"],
            unified_social_credit_code=parsed["unified_social_credit_code"],
            legal_representative=parsed["legal_representative"],
            registered_address=parsed["registered_address"],
            confidence=float(parsed["confidence"]),
            source="dev_mock",
            raw_text=parsed["raw_text"],
        )

    if provider == "rapidocr":
        return await asyncio.to_thread(_run_rapidocr_sync, file_path)

    parsed = mock_parser(original_name)
    return BusinessLicenseOcrResult(
        company_name=parsed["company_name"],
        unified_social_credit_code=parsed["unified_social_credit_code"],
        legal_representative=parsed["legal_representative"],
        registered_address=parsed["registered_address"],
        confidence=float(parsed["confidence"]),
        source=f"unsupported_provider:{provider}:dev_mock",
        raw_text=parsed["raw_text"],
    )
