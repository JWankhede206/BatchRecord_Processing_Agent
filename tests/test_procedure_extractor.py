from unittest.mock import patch

from src.models.document_models import ParsedDocument, ParsedPage
from src.models.extraction_models import ProcedureStep


def _make_parsed_doc() -> ParsedDocument:
    return ParsedDocument(
        file_name="test",
        file_path="/tmp/test.pdf",
        pages=[ParsedPage(page_number=7, text="Step 1: Weigh materials")],
    )


MOCK_RESPONSE = {
    "steps": [
        {
            "step_number": 1,
            "title": "Weigh materials",
            "instruction_text": "Weigh the API and excipients separately.",
            "page_number": 7,
            "expected_entries": ["weight of each material"],
            "limits_or_targets": [],
            "notes": ["Check for lumps"],
            "labels": ["Fexofenadine blend"],
        }
    ]
}


@patch("src.services.procedure_extractor.chat_json", return_value=MOCK_RESPONSE)
def test_extract_procedure_returns_steps(mock_chat):
    from src.services.procedure_extractor import extract_procedure

    result = extract_procedure(_make_parsed_doc())
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], ProcedureStep)
    assert result[0].step_number == 1
    assert result[0].title == "Weigh materials"
    assert len(result[0].expected_entries) == 1


@patch("src.services.procedure_extractor.chat_json", return_value={"steps": []})
def test_extract_procedure_empty(mock_chat):
    from src.services.procedure_extractor import extract_procedure

    result = extract_procedure(_make_parsed_doc())
    assert result == []
