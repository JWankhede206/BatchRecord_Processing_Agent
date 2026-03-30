from ..models.document_models import ParsedDocument
from ..models.extraction_models import ProcedureStep
from ..openai_client import chat_json
from ..utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a pharmaceutical batch record analyst.
Given the text of a batch record, extract the production procedure steps in order.

Return a JSON object with a key "steps" containing an array of step objects. Each step should have:
- step_number: integer step number
- title: brief title for the step
- instruction_text: the full instruction text
- page_number: the page where this step appears
- expected_entries: list of strings describing entries/recordings expected (e.g. weights, times, signatures)
- limits_or_targets: list of strings describing any limits, tolerances, or target values mentioned
- notes: list of any notes or cautions mentioned in the step
- labels: list of any labels or identifiers to be applied (e.g. container labels)

Extract ALL numbered processing steps. Include sub-steps as part of their parent step's instruction_text."""


def extract_procedure(parsed_doc: ParsedDocument) -> list[ProcedureStep]:
    logger.info("Extracting procedure steps from %s", parsed_doc.file_name)

    page_texts = []
    for page in parsed_doc.pages:
        page_texts.append(f"--- PAGE {page.page_number} ---\n{page.text}")
    full_text = "\n\n".join(page_texts)

    result = chat_json(SYSTEM_PROMPT, full_text)

    steps = [ProcedureStep(**s) for s in result.get("steps", [])]
    logger.info("Extracted %d procedure steps from %s", len(steps), parsed_doc.file_name)
    return steps
