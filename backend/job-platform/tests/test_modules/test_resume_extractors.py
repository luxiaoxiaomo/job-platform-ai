"""
Resume extractor tests.
"""

from pathlib import Path
from types import SimpleNamespace

from app.modules.company_certification import ocr as shared_ocr
from app.modules.resume import extractors


def test_pdf_without_embedded_text_falls_back_to_shared_ocr(monkeypatch):
    pdf_path = Path("scan.pdf")

    monkeypatch.setattr(extractors, "extract_pdf_text", lambda path: "")
    monkeypatch.setattr(shared_ocr, "_prepare_ocr_input_paths", lambda path, output_dir: [Path(path)])
    monkeypatch.setattr(
        shared_ocr,
        "_rapidocr_engine",
        lambda: lambda path, text_score=None: SimpleNamespace(
            txts=["Han Yuxia", "Senior Product Manager", "Bachelor 7 years"],
            scores=[0.98, 0.96, 0.95],
        ),
    )

    text, extractor = extractors.extract_resume_text(pdf_path, ".pdf")

    assert extractor == "rapidocr"
    assert "Han Yuxia" in text
    assert "Senior Product Manager" in text
