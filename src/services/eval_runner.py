import re

from ..config import TARGET_SECTIONS
from ..models.document_models import DocumentSection, ParsedDocument
from ..models.extraction_models import BatchRecordExtraction
from ..models.finding_models import EvalResult, Finding
from ..utils.logger import get_logger

logger = get_logger(__name__)

BLANK_PATTERN = re.compile(r"_{3,}|__+")


def run_eval(
    parsed_doc: ParsedDocument,
    extraction: BatchRecordExtraction,
    sections: list[DocumentSection],
) -> EvalResult:
    logger.info("Running eval checks on %s", parsed_doc.file_name)
    findings: list[Finding] = []

    found_section_names = {s.name for s in sections}
    for target in TARGET_SECTIONS:
        if target not in found_section_names:
            findings.append(Finding(
                finding_type="missing_section",
                severity="warning",
                section_name=target,
                message=f"Section '{target}' was not found in the document.",
            ))

    meta = extraction.metadata
    for field_name in ["title", "version", "lot_number", "part_number", "batch_size", "storage_conditions"]:
        if getattr(meta, field_name) is None:
            findings.append(Finding(
                finding_type="missing_field",
                severity="warning" if field_name in ("lot_number",) else "info",
                message=f"Metadata field '{field_name}' is missing or could not be extracted.",
            ))

    full_text = "\n".join(p.text for p in parsed_doc.pages)

    _check_blank_signatures(findings, sections, full_text, parsed_doc)
    _check_blank_verifications(findings, sections, full_text, parsed_doc)
    _check_blank_recorded_values(findings, parsed_doc)
    _check_empty_comment_log(findings, sections)
    _check_empty_exception_log(findings, sections)
    _check_empty_disposition(findings, sections)
    _check_template_document(findings, extraction, parsed_doc)

    stats = {}
    for f in findings:
        stats[f.finding_type] = stats.get(f.finding_type, 0) + 1

    logger.info("Eval complete: %d findings for %s", len(findings), parsed_doc.file_name)
    return EvalResult(
        file_name=parsed_doc.file_name,
        findings=findings,
        summary_stats=stats,
    )


def _check_blank_signatures(
    findings: list[Finding],
    sections: list[DocumentSection],
    full_text: str,
    parsed_doc: ParsedDocument,
) -> None:
    sig_sections = [s for s in sections if s.name in ("approvals", "training_log")]
    for sec in sig_sections:
        pages_text = _get_section_text(parsed_doc, sec)
        if "Signature" in pages_text and BLANK_PATTERN.search(pages_text):
            findings.append(Finding(
                finding_type="blank_signature",
                severity="warning",
                section_name=sec.name,
                page_number=sec.start_page,
                message=f"Blank signature field(s) detected in '{sec.name}' section.",
            ))


def _check_blank_verifications(
    findings: list[Finding],
    sections: list[DocumentSection],
    full_text: str,
    parsed_doc: ParsedDocument,
) -> None:
    for sec in sections:
        pages_text = _get_section_text(parsed_doc, sec)
        if ("Performed By" in pages_text or "Verified By" in pages_text or "QA Verified" in pages_text):
            if BLANK_PATTERN.search(pages_text):
                findings.append(Finding(
                    finding_type="blank_verification",
                    severity="warning",
                    section_name=sec.name,
                    page_number=sec.start_page,
                    message=f"Blank verification/performed-by field(s) in '{sec.name}' section.",
                ))


def _check_blank_recorded_values(findings: list[Finding], parsed_doc: ParsedDocument) -> None:
    blank_count = 0
    for page in parsed_doc.pages:
        blanks = BLANK_PATTERN.findall(page.text)
        blank_count += len(blanks)
    if blank_count > 10:
        findings.append(Finding(
            finding_type="blank_recorded_value",
            severity="warning",
            message=f"Document contains {blank_count} blank fill-in fields across all pages.",
        ))


def _check_empty_comment_log(findings: list[Finding], sections: list[DocumentSection]) -> None:
    for sec in sections:
        if sec.name == "production_comment_log":
            text = sec.raw_text.strip()
            has_entries = bool(re.search(r"\d+\.\s*\S+", text))
            if not has_entries:
                findings.append(Finding(
                    finding_type="empty_comment_log",
                    severity="info",
                    section_name=sec.name,
                    page_number=sec.start_page,
                    message="Production comment log appears to have no entries.",
                ))


def _check_empty_exception_log(findings: list[Finding], sections: list[DocumentSection]) -> None:
    for sec in sections:
        if sec.name == "exception_log":
            text = sec.raw_text.strip()
            has_entries = bool(re.search(r"\d+\.\s*\S{3,}", text))
            if not has_entries:
                findings.append(Finding(
                    finding_type="empty_exception_log",
                    severity="info",
                    section_name=sec.name,
                    page_number=sec.start_page,
                    message="Exception log appears to have no entries.",
                ))


def _check_empty_disposition(findings: list[Finding], sections: list[DocumentSection]) -> None:
    for sec in sections:
        if sec.name == "qa_disposition":
            text = sec.raw_text.strip()
            keywords = ["RELEASED", "CONDITIONAL", "RESEARCH", "REJECTED"]
            has_selection = any(
                re.search(rf"\[?[xX✓]\]?\s*{kw}", text) for kw in keywords
            )
            if not has_selection:
                findings.append(Finding(
                    finding_type="empty_disposition",
                    severity="critical",
                    section_name=sec.name,
                    page_number=sec.start_page,
                    message="QA disposition does not appear to have a selection made.",
                ))


def _check_template_document(
    findings: list[Finding],
    extraction: BatchRecordExtraction,
    parsed_doc: ParsedDocument,
) -> None:
    blank_indicators = 0
    meta = extraction.metadata
    if meta.lot_number is None:
        blank_indicators += 1

    full_text = "\n".join(p.text for p in parsed_doc.pages)
    blank_fields = len(BLANK_PATTERN.findall(full_text))
    if blank_fields > 20:
        blank_indicators += 1

    has_any_signature = bool(re.search(r"(?:signed|signature.*\S{5,})", full_text, re.IGNORECASE))
    if not has_any_signature:
        blank_indicators += 1

    if blank_indicators >= 2:
        findings.append(Finding(
            finding_type="likely_template_document",
            severity="critical",
            message="This document appears to be a blank template rather than a completed batch record.",
        ))


def _get_section_text(parsed_doc: ParsedDocument, section: DocumentSection) -> str:
    texts = []
    for page in parsed_doc.pages:
        if section.start_page <= page.page_number <= section.end_page:
            texts.append(page.text)
    return "\n".join(texts)
