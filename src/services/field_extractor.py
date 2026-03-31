from ..models.document_models import DocumentSection, ParsedDocument
from ..models.extraction_models import (
    BatchRecordExtraction,
    BatchRecordMetadata,
    EquipmentRow,
    MaterialRow,
)
from ..openai_client import achat_json, achat_json_vision, chat_json
from ..utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a pharmaceutical batch record analyst.
Given the text of a batch record, extract the following structured data.

Return a JSON object with these keys:

"metadata": {
  "title": document title or null,
  "version": version number or null,
  "lot_number": lot number or null,
  "part_number": part number or null,
  "batch_size": batch size or null,
  "storage_conditions": storage conditions or null
}

"materials": array of objects, each with:
  "description", "part_number", "quantity_required", "lot_number", "qty_staged", "exp_or_retest"
  (use null for missing values)

"equipment": array of objects, each with:
  "equipment_description", "equipment_id", "previous_calibration", "calibration_required"
  (use null for missing values)

Extract all rows you can find. Use null for any value not present in the document."""


def _build_prompt(parsed_doc: ParsedDocument) -> tuple[str, list[str]]:
    page_texts = [
        f"--- PAGE {p.page_number} ---\n{p.enriched_text or p.text}"
        for p in parsed_doc.pages
    ]
    full_text = "\n\n".join(page_texts)
    images = [p.image_b64 for p in parsed_doc.pages if p.image_b64]
    return full_text, images


def _parse_result(
    result: dict,
    sections: list[DocumentSection],
    file_name: str,
) -> BatchRecordExtraction:
    metadata = BatchRecordMetadata(**(result.get("metadata", {})))
    materials = [MaterialRow(**m) for m in result.get("materials", [])]
    equipment = [EquipmentRow(**e) for e in result.get("equipment", [])]
    logger.info("Extracted fields: %d materials, %d equipment rows", len(materials), len(equipment))
    return BatchRecordExtraction(
        metadata=metadata,
        sections=sections,
        materials=materials,
        equipment=equipment,
        procedure_steps=[],
    )


def extract_fields(
    parsed_doc: ParsedDocument,
    sections: list[DocumentSection],
) -> BatchRecordExtraction:
    logger.info("Extracting fields from %s", parsed_doc.file_name)
    full_text, _ = _build_prompt(parsed_doc)
    result = chat_json(SYSTEM_PROMPT, full_text)
    return _parse_result(result, sections, parsed_doc.file_name)


async def aextract_fields(
    parsed_doc: ParsedDocument,
    sections: list[DocumentSection],
) -> BatchRecordExtraction:
    logger.info("Extracting fields from %s (async+vision)", parsed_doc.file_name)
    full_text, images = _build_prompt(parsed_doc)
    result = await achat_json_vision(SYSTEM_PROMPT, full_text, images)
    return _parse_result(result, sections, parsed_doc.file_name)
