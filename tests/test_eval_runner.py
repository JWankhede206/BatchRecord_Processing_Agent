from src.models.document_models import DocumentSection, ParsedDocument, ParsedPage
from src.models.extraction_models import BatchRecordExtraction, BatchRecordMetadata
from src.models.finding_models import EvalResult
from src.services.eval_runner import run_eval


def _make_parsed_doc(text: str = "Lot Number: ______ Signature ______") -> ParsedDocument:
    return ParsedDocument(
        file_name="test",
        file_path="/tmp/test.pdf",
        pages=[ParsedPage(page_number=1, text=text)],
    )


def _make_extraction(
    title: str | None = "Test Record",
    lot_number: str | None = None,
) -> BatchRecordExtraction:
    return BatchRecordExtraction(
        metadata=BatchRecordMetadata(title=title, lot_number=lot_number),
        sections=[],
        materials=[],
        equipment=[],
        procedure_steps=[],
    )


def test_eval_returns_eval_result():
    parsed_doc = _make_parsed_doc()
    extraction = _make_extraction()
    result = run_eval(parsed_doc, extraction, [])
    assert isinstance(result, EvalResult)
    assert result.file_name == "test"


def test_missing_sections_detected():
    parsed_doc = _make_parsed_doc()
    extraction = _make_extraction()
    result = run_eval(parsed_doc, extraction, [])
    missing = [f for f in result.findings if f.finding_type == "missing_section"]
    assert len(missing) == 14  # all target sections missing


def test_missing_field_detected():
    parsed_doc = _make_parsed_doc()
    extraction = _make_extraction(lot_number=None)
    result = run_eval(parsed_doc, extraction, [])
    missing_fields = [f for f in result.findings if f.finding_type == "missing_field"]
    assert any("lot_number" in f.message for f in missing_fields)


def test_template_document_detected():
    parsed_doc = _make_parsed_doc("______ " * 30)
    extraction = _make_extraction(lot_number=None)
    result = run_eval(parsed_doc, extraction, [])
    template = [f for f in result.findings if f.finding_type == "likely_template_document"]
    assert len(template) >= 1
