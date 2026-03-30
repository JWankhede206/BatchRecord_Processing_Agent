from ..config import TARGET_SECTIONS
from ..models.document_models import DocumentSection, ParsedDocument
from ..openai_client import chat_json
from ..utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a pharmaceutical batch record analyst.
Given the full text of a batch record PDF (with page numbers), identify which of the following sections are present:

{sections}

For each section found, return:
- name: the section identifier from the list above (snake_case)
- start_page: first page where the section appears
- end_page: last page where the section appears
- raw_text: the key text content of that section (abbreviated if very long, max ~500 chars)
- confidence: your confidence that this section is correctly identified (0.0 to 1.0)

Return a JSON object with a key "sections" containing an array of section objects.
Only include sections you actually find in the document. Use the exact snake_case names from the list above."""


def extract_sections(parsed_doc: ParsedDocument) -> list[DocumentSection]:
    logger.info("Extracting sections from %s", parsed_doc.file_name)

    page_texts = []
    for page in parsed_doc.pages:
        page_texts.append(f"--- PAGE {page.page_number} ---\n{page.text}")
    full_text = "\n\n".join(page_texts)

    system = SYSTEM_PROMPT.format(sections="\n".join(f"- {s}" for s in TARGET_SECTIONS))
    result = chat_json(system, full_text)

    sections = []
    for item in result.get("sections", []):
        sections.append(DocumentSection(**item))

    logger.info("Found %d sections in %s", len(sections), parsed_doc.file_name)
    return sections
