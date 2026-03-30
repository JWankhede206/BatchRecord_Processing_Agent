from ..models.document_models import DocumentSection
from ..models.extraction_models import BatchRecordExtraction
from ..models.finding_models import EvalResult
from ..utils.logger import get_logger

logger = get_logger(__name__)


def generate_summary(
    extraction: BatchRecordExtraction,
    eval_result: EvalResult,
    sections: list[DocumentSection],
) -> str:
    logger.info("Generating summary for %s", eval_result.file_name)

    meta = extraction.metadata
    lines = [
        f"# Batch Record Summary: {eval_result.file_name}",
        "",
        "## Document Identity",
        f"- **Title:** {meta.title or 'N/A'}",
        f"- **Version:** {meta.version or 'N/A'}",
        f"- **Lot Number:** {meta.lot_number or 'N/A'}",
        f"- **Part Number:** {meta.part_number or 'N/A'}",
        f"- **Batch Size:** {meta.batch_size or 'N/A'}",
        f"- **Storage Conditions:** {meta.storage_conditions or 'N/A'}",
        "",
        "## Sections Found",
    ]

    if sections:
        for sec in sections:
            lines.append(f"- **{sec.name}** (pages {sec.start_page}-{sec.end_page}, confidence: {sec.confidence:.0%})")
    else:
        lines.append("- No sections identified")

    lines.extend([
        "",
        "## Extraction Summary",
        f"- **Materials:** {len(extraction.materials)} rows",
        f"- **Equipment:** {len(extraction.equipment)} rows",
        f"- **Procedure Steps:** {len(extraction.procedure_steps)}",
    ])

    lines.extend(["", "## Findings"])

    if eval_result.findings:
        critical = [f for f in eval_result.findings if f.severity == "critical"]
        warnings = [f for f in eval_result.findings if f.severity == "warning"]
        infos = [f for f in eval_result.findings if f.severity == "info"]

        lines.append(f"- **Critical:** {len(critical)}")
        lines.append(f"- **Warning:** {len(warnings)}")
        lines.append(f"- **Info:** {len(infos)}")
        lines.append("")

        if critical:
            lines.append("### Critical")
            for f in critical:
                lines.append(f"- [{f.finding_type}] {f.message}")
            lines.append("")

        if warnings:
            lines.append("### Warnings")
            for f in warnings:
                lines.append(f"- [{f.finding_type}] {f.message}")
            lines.append("")

        if infos:
            lines.append("### Info")
            for f in infos:
                lines.append(f"- [{f.finding_type}] {f.message}")
            lines.append("")
    else:
        lines.append("No findings.")
        lines.append("")

    is_template = any(f.finding_type == "likely_template_document" for f in eval_result.findings)
    lines.extend([
        "## Document Assessment",
        f"- **Status:** {'Likely a blank template' if is_template else 'Appears to be a completed or partially completed record'}",
    ])

    return "\n".join(lines) + "\n"
