from ..models.document_models import DocumentSection, ParsedDocument
from ..models.extraction_models import (
    BatchRecordExtraction,
    BatchRecordMetadata,
    EquipmentRow,
    MaterialRow,
)
from ..openai_client import chat_json
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


def extract_fields(
    parsed_doc: ParsedDocument,
    sections: list[DocumentSection],
) -> BatchRecordExtraction:
    logger.info("Extracting fields from %s", parsed_doc.file_name)

    page_texts = []
    for page in parsed_doc.pages:
        page_texts.append(f"--- PAGE {page.page_number} ---\n{page.text}")
    full_text = "\n\n".join(page_texts)

    result = chat_json(SYSTEM_PROMPT, full_text)

    metadata = BatchRecordMetadata(**(result.get("metadata", {})))
    materials = [MaterialRow(**m) for m in result.get("materials", [])]
    equipment = [EquipmentRow(**e) for e in result.get("equipment", [])]

    extraction = BatchRecordExtraction(
        metadata=metadata,
        sections=sections,
        materials=materials,
        equipment=equipment,
        procedure_steps=[],
    )

    logger.info(
        "Extracted fields: %d materials, %d equipment rows",
        len(materials),
        len(equipment),
    )
    return extraction
