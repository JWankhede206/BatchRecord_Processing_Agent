from ..models.document_models import ParsedDocument
from ..models.extraction_models import ProcedureStep
from ..openai_client import achat_json, achat_json_vision, chat_json
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


def _build_prompt(parsed_doc: ParsedDocument) -> tuple[str, list[str]]:
    page_texts = [
        f"--- PAGE {p.page_number} ---\n{p.enriched_text or p.text}"
        for p in parsed_doc.pages
    ]
    full_text = "\n\n".join(page_texts)
    images = [p.image_b64 for p in parsed_doc.pages if p.image_b64]
    return full_text, images


def _parse_result(result: dict, file_name: str) -> list[ProcedureStep]:
    steps = [ProcedureStep(**s) for s in result.get("steps", [])]
    logger.info("Extracted %d procedure steps from %s", len(steps), file_name)
    return steps


def extract_procedure(parsed_doc: ParsedDocument) -> list[ProcedureStep]:
    logger.info("Extracting procedure steps from %s", parsed_doc.file_name)
    full_text, _ = _build_prompt(parsed_doc)
    result = chat_json(SYSTEM_PROMPT, full_text)
    return _parse_result(result, parsed_doc.file_name)


async def aextract_procedure(parsed_doc: ParsedDocument) -> list[ProcedureStep]:
    logger.info("Extracting procedure steps from %s (async+vision)", parsed_doc.file_name)
    full_text, images = _build_prompt(parsed_doc)
    result = await achat_json_vision(SYSTEM_PROMPT, full_text, images)
    return _parse_result(result, parsed_doc.file_name)
