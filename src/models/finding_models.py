from pydantic import BaseModel

from .extraction_models import EvidenceRef


class Finding(BaseModel):
    finding_type: str
    severity: str
    section_name: str | None = None
    page_number: int | None = None
    message: str
    evidence: list[EvidenceRef] = []


class EvalResult(BaseModel):
    file_name: str
    findings: list[Finding]
    summary_stats: dict
