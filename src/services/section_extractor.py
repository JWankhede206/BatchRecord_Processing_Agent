from ..config import TARGET_SECTIONS
from ..models.document_models import DocumentSection, ParsedDocument
from ..openai_client import achat_json_vision, chat_json
from ..utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a pharmaceutical batch record analyst.
Given the full text of a batch record PDF (with page numbers and extracted tables), identify which of the following sections are present:

{sections}

Tables in the text are shown as markdown with [BLANK] marking empty cells and page images are provided for visual confirmation.

For each section found, return:
- name: the section identifier from the list above (snake_case)
- start_page: first page where the section appears
- end_page: last page where the section appears
- raw_text: the key text content of that section (abbreviated if very long, max ~500 chars)
- confidence: your confidence that this section is correctly identified (0.0 to 1.0)

Return a JSON object with a key "sections" containing an array of section objects.
Only include sections you actually find in the document. Use the exact snake_case names from the list above."""


def _build_prompt(parsed_doc: ParsedDocument) -> tuple[str, str, list[str]]:
    page_texts = [
        f"--- PAGE {p.page_number} ---\n{p.enriched_text or p.text}"
        for p in parsed_doc.pages
    ]
    full_text = "\n\n".join(page_texts)
    system = SYSTEM_PROMPT.format(sections="\n".join(f"- {s}" for s in TARGET_SECTIONS))
    images = [p.image_b64 for p in parsed_doc.pages if p.image_b64]
    return system, full_text, images


def _parse_result(result: dict, file_name: str) -> list[DocumentSection]:
    sections = [DocumentSection(**item) for item in result.get("sections", [])]
    logger.info("Found %d sections in %s", len(sections), file_name)
    return sections


def extract_sections(parsed_doc: ParsedDocument) -> list[DocumentSection]:
    logger.info("Extracting sections from %s", parsed_doc.file_name)
    system, full_text, _ = _build_prompt(parsed_doc)
    result = chat_json(system, full_text)
    return _parse_result(result, parsed_doc.file_name)


async def aextract_sections(parsed_doc: ParsedDocument) -> list[DocumentSection]:
    logger.info("Extracting sections from %s (async+vision)", parsed_doc.file_name)
    system, full_text, images = _build_prompt(parsed_doc)
    result = await achat_json_vision(system, full_text, images)
    return _parse_result(result, parsed_doc.file_name)
