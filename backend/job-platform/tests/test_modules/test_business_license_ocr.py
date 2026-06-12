"""
Business license OCR field extraction tests.
"""
from PIL import Image

from app.core.config import settings
from app.modules.company_certification.ocr import (
    _prepare_ocr_input_paths,
    extract_business_license_fields,
)


def test_extract_business_license_fields_from_rapidocr_lines():
    lines = [
        "国家企业信用信息公示系统网址：http://www.gsxt.gov.cn",
        "经营范围",
        "法定代表人",
        "91330110MADBJF8A81",
        "统一社会信用代码",
        "类型有限责任公司（自然人独资）",
        "俞杏林",
        "杭州毅创越新信息咨询有限公司",
        "营业执照",
        "住",
        "成立日期",
        "注册资本",
        "登记机关",
        "所",
        "2024年03月05日",
        "幢3037室",
        "浙江省杭州市余杭区良渚街道丁公路136号3",
        "壹佰万元整",
    ]

    result = extract_business_license_fields(lines, scores=[0.95] * len(lines))

    assert result.source == "rapidocr"
    assert result.unified_social_credit_code == "91330110MADBJF8A81"
    assert result.company_name == "杭州毅创越新信息咨询有限公司"
    assert result.legal_representative == "俞杏林"
    assert result.registered_address == "浙江省杭州市余杭区良渚街道丁公路136号3幢3037室"
    assert result.confidence == 0.95
    assert "杭州毅创越新信息咨询有限公司" in result.raw_text


def test_prepare_pdf_input_renders_png_pages(tmp_path):
    original_max_pages = settings.OCR_PDF_MAX_PAGES
    settings.OCR_PDF_MAX_PAGES = 1
    try:
        pdf_path = tmp_path / "license.pdf"
        render_dir = tmp_path / "rendered"
        render_dir.mkdir()
        Image.new("RGB", (120, 80), "white").save(pdf_path, "PDF")

        paths = _prepare_ocr_input_paths(pdf_path, render_dir)

        assert len(paths) == 1
        assert paths[0].suffix == ".png"
        assert paths[0].exists()
    finally:
        settings.OCR_PDF_MAX_PAGES = original_max_pages


def test_prepare_heif_input_converts_png(tmp_path):
    from pillow_heif import register_heif_opener

    register_heif_opener()
    heif_path = tmp_path / "license.heif"
    render_dir = tmp_path / "rendered"
    render_dir.mkdir()
    Image.new("RGB", (120, 80), "white").save(heif_path, "HEIF")

    paths = _prepare_ocr_input_paths(heif_path, render_dir)

    assert len(paths) == 1
    assert paths[0].suffix == ".png"
    assert paths[0].exists()
