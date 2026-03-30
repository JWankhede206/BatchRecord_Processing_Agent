from pathlib import Path

from src.models.document_models import ParsedDocument
from src.services.pdf_parser import parse_pdf

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_parse_pdf_returns_parsed_document():
    pdf_path = DATA_DIR / "batch_records.pdf"
    if not pdf_path.exists():
        return
    result = parse_pdf(pdf_path)
    assert isinstance(result, ParsedDocument)
    assert result.file_name == "batch_records"
    assert len(result.pages) == 17


def test_parsed_pages_have_text():
    pdf_path = DATA_DIR / "batch_records.pdf"
    if not pdf_path.exists():
        return
    result = parse_pdf(pdf_path)
    for page in result.pages:
        assert page.page_number >= 1
        assert isinstance(page.text, str)
    assert "Batch Record" in result.pages[0].text
