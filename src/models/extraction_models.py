from pydantic import BaseModel

from .document_models import DocumentSection


class EvidenceRef(BaseModel):
    page_number: int
    quote: str


class BatchRecordMetadata(BaseModel):
    title: str | None = None
    version: str | None = None
    lot_number: str | None = None
    part_number: str | None = None
    batch_size: str | None = None
    storage_conditions: str | None = None


class MaterialRow(BaseModel):
    description: str | None = None
    part_number: str | None = None
    quantity_required: str | None = None
    lot_number: str | None = None
    qty_staged: str | None = None
    exp_or_retest: str | None = None


class EquipmentRow(BaseModel):
    equipment_description: str | None = None
    equipment_id: str | None = None
    previous_calibration: str | None = None
    calibration_required: str | None = None


class ProcedureStep(BaseModel):
    step_number: int
    title: str
    instruction_text: str
    page_number: int
    expected_entries: list[str] = []
    limits_or_targets: list[str] = []
    notes: list[str] = []
    labels: list[str] = []


class BatchRecordExtraction(BaseModel):
    metadata: BatchRecordMetadata
    sections: list[DocumentSection]
    materials: list[MaterialRow]
    equipment: list[EquipmentRow]
    procedure_steps: list[ProcedureStep]
