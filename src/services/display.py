from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..config import TARGET_SECTIONS
from ..models.document_models import DocumentSection
from ..models.extraction_models import BatchRecordExtraction
from ..models.finding_models import EvalResult

console = Console()

SEVERITY_STYLES = {
    "critical": ("bold red", "CRITICAL"),
    "warning": ("yellow", "WARNING"),
    "info": ("cyan", "INFO"),
}


def display_eval(
    extraction: BatchRecordExtraction,
    eval_result: EvalResult,
    sections: list[DocumentSection],
) -> None:
    console.print()

    # Header
    console.print(Panel(
        f"[bold white]Batch Record Eval:[/] [bold cyan]{eval_result.file_name}.pdf[/]",
        style="bold blue",
    ))

    # Document identity
    meta = extraction.metadata
    doc_info = Text()
    doc_info.append("  Title:   ", style="dim")
    doc_info.append(f"{meta.title or 'N/A'}\n", style="bold white")
    doc_info.append("  Version: ", style="dim")
    doc_info.append(f"{meta.version or 'N/A'}", style="white")
    doc_info.append("  |  Part: ", style="dim")
    doc_info.append(f"{meta.part_number or 'N/A'}", style="white")
    doc_info.append("  |  Lot: ", style="dim")
    doc_info.append(f"{meta.lot_number or 'N/A'}", style="white")
    doc_info.append("  |  Batch Size: ", style="dim")
    doc_info.append(f"{meta.batch_size or 'N/A'}", style="white")
    console.print(doc_info)
    console.print()

    # Findings summary counts
    critical = [f for f in eval_result.findings if f.severity == "critical"]
    warnings = [f for f in eval_result.findings if f.severity == "warning"]
    infos = [f for f in eval_result.findings if f.severity == "info"]

    counts = Text()
    counts.append("  ")
    counts.append(f" {len(critical)} Critical ", style="bold red on dark_red")
    counts.append("  ")
    counts.append(f" {len(warnings)} Warning ", style="bold yellow on yellow4")
    counts.append("  ")
    counts.append(f" {len(infos)} Info ", style="bold cyan on dark_cyan")
    console.print(Panel(counts, title="[bold]Findings Summary[/]", border_style="dim"))

    # Findings table
    if eval_result.findings:
        table = Table(show_header=True, header_style="bold", border_style="dim", expand=True)
        table.add_column("Severity", width=10, justify="center")
        table.add_column("Type", width=24)
        table.add_column("Section", width=20)
        table.add_column("Message", ratio=1)

        sorted_findings = sorted(
            eval_result.findings,
            key=lambda f: {"critical": 0, "warning": 1, "info": 2}.get(f.severity, 3),
        )

        for finding in sorted_findings:
            style, label = SEVERITY_STYLES.get(finding.severity, ("white", finding.severity.upper()))
            table.add_row(
                Text(label, style=style),
                finding.finding_type,
                finding.section_name or "-",
                finding.message,
            )

        console.print(table)
    else:
        console.print("  [bold green]No findings.[/]")

    console.print()

    # Sections overview
    found_names = {s.name for s in sections}
    section_parts = []
    for target in TARGET_SECTIONS:
        if target in found_names:
            section_parts.append(f"[bold green]\u2713[/bold green] {target}")
        else:
            section_parts.append(f"[bold red]\u2717[/bold red] {target}")
    section_text = "  " + "  ".join(section_parts)
    console.print(Panel(section_text, title="[bold]Sections[/bold]", border_style="dim"))

    # Extraction stats
    stats = Text()
    stats.append("  Sections: ", style="dim")
    stats.append(f"{len(sections)}/{len(TARGET_SECTIONS)}", style="bold white")
    stats.append("  |  Procedure Steps: ", style="dim")
    stats.append(str(len(extraction.procedure_steps)), style="bold white")
    stats.append("  |  Materials: ", style="dim")
    stats.append(str(len(extraction.materials)), style="bold white")
    stats.append("  |  Equipment: ", style="dim")
    stats.append(str(len(extraction.equipment)), style="bold white")
    console.print(stats)

    # Template assessment
    is_template = any(f.finding_type == "likely_template_document" for f in eval_result.findings)
    console.print()
    if is_template:
        console.print("  [bold red]Assessment:[/] This document appears to be a [bold]blank template[/], not a completed batch record.")
    else:
        console.print("  [bold green]Assessment:[/] This document appears to be a [bold]completed or partially completed[/] batch record.")

    console.print()
    console.print("[dim]\u2500" * 60 + "[/]")
    console.print()


def display_pipeline_start(file_count: int, input_dir: str) -> None:
    console.print()
    console.print(Panel(
        f"[bold white]Batch Record Agent[/]\n[dim]{file_count} PDF(s) in {input_dir}[/]",
        style="bold blue",
        expand=False,
    ))
    console.print()


def display_pipeline_done(total: int, failed: int) -> None:
    if failed == 0:
        console.print(f"[bold green]Done.[/] Processed {total} file(s) successfully.")
    else:
        console.print(f"[bold yellow]Done.[/] Processed {total} file(s), [red]{failed} failed[/].")
    console.print()
