from unittest.mock import patch

from src.models.document_models import DocumentSection, ParsedDocument, ParsedPage


def _make_parsed_doc() -> ParsedDocument:
    return ParsedDocument(
        file_name="test",
        file_path="/tmp/test.pdf",
        pages=[ParsedPage(page_number=1, text="Section 1: Approvals\nSignature fields here")],
    )


MOCK_RESPONSE = {
    "sections": [
        {
            "name": "approvals",
            "start_page": 1,
            "end_page": 1,
            "raw_text": "Section 1: Approvals",
            "confidence": 0.95,
        }
    ]
}


@patch("src.services.section_extractor.chat_json", return_value=MOCK_RESPONSE)
def test_extract_sections_returns_list(mock_chat):
    from src.services.section_extractor import extract_sections

    result = extract_sections(_make_parsed_doc())
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], DocumentSection)
    assert result[0].name == "approvals"
    assert result[0].confidence == 0.95


@patch("src.services.section_extractor.chat_json", return_value={"sections": []})
def test_extract_sections_empty(mock_chat):
    from src.services.section_extractor import extract_sections

    result = extract_sections(_make_parsed_doc())
    assert result == []
