from collections import defaultdict

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree

from ..models.document_models import DocumentSection
from ..models.extraction_models import BatchRecordExtraction
from ..models.finding_models import EvalResult, Finding

console = Console()

# Logical groupings of the 14 target sections
SECTION_GROUPS: list[tuple[str, list[str]]] = [
    ("Approvals & Personnel", ["approvals", "training_log"]),
    ("Product & Reference Docs", ["product_details", "reference_docs"]),
    ("Materials", ["bill_of_materials"]),
    ("Equipment", ["processing_equipment"]),
    ("Production Procedures", [
        "area_clearance",
        "production_procedure",
        "post_production_sampling",
        "yield_calculations",
    ]),
    ("Logs", ["production_comment_log", "exception_log"]),
    ("Quality Review & Disposition", ["post_production_review", "qa_disposition"]),
]

SEVERITY_ICON = {
    "critical": "[bold red]●[/]",
    "warning":  "[bold yellow]▲[/]",
    "info":     "[bold cyan]○[/]",
}

SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


def _assessment_text(findings) -> tuple[str, str]:
    is_template = any(f.finding_type == "likely_template_document" for f in findings)
    if is_template:
        return "BLANK TEMPLATE", "bold red"
    if any(f.severity == "critical" for f in findings):
        return "CRITICAL ISSUES", "bold red"
    if any(f.severity == "warning" for f in findings):
        return "WARNINGS PRESENT", "bold yellow"
    return "LOOKS COMPLETE", "bold green"


def _summary_panel(
    extraction: BatchRecordExtraction,
    eval_result: EvalResult,
    sections: list[DocumentSection],
) -> Panel:
    meta = extraction.metadata
    findings = eval_result.findings
    critical = [f for f in findings if f.severity == "critical"]
    warnings = [f for f in findings if f.severity == "warning"]
    infos = [f for f in findings if f.severity == "info"]
    page_range = max((s.end_page for s in sections), default=0)
    assessment, assess_style = _assessment_text(findings)

    t = Text()
    t.append(f"  {meta.title or 'Unknown Title'}\n", style="bold white")
    t.append("  Version ", style="dim")
    t.append(f"{meta.version or 'N/A'}", style="white")
    t.append("  |  Part ", style="dim")
    t.append(f"{meta.part_number or 'N/A'}", style="white")
    t.append("  |  Lot ", style="dim")
    t.append(f"{meta.lot_number or 'N/A'}\n\n", style="white")
    t.append(f"  Pages: ~{page_range}", style="dim")
    t.append("  |  Sections: ", style="dim")
    t.append(f"{len(sections)}/14", style="bold white")
    t.append("  |  Steps: ", style="dim")
    t.append(f"{len(extraction.procedure_steps)}", style="bold white")
    t.append("  |  Materials: ", style="dim")
    t.append(f"{len(extraction.materials)}\n\n", style="bold white")
    t.append(f"  ● {len(critical)} Critical  ", style="bold red")
    t.append(f"▲ {len(warnings)} Warning  ", style="bold yellow")
    t.append(f"○ {len(infos)} Info\n\n", style="bold cyan")
    t.append("  Assessment: ", style="dim")
    t.append(assessment, style=assess_style)

    return Panel(t, title="[bold]Batch Record Summary[/]", border_style="blue", padding=(0, 1))


def _finding_label(f: Finding) -> str:
    icon = SEVERITY_ICON.get(f.severity, "?")
    msg = f.message[:80] + "…" if len(f.message) > 80 else f.message
    return f"{icon} [dim]{f.finding_type}[/] — {msg}"


def _build_section_tree(
    findings: list[Finding],
    sections: list[DocumentSection],
) -> Tree:
    found_names = {s.name for s in sections}

    # Index findings by section_name
    by_section: dict[str | None, list[Finding]] = defaultdict(list)
    for f in findings:
        by_section[f.section_name].append(f)

    root = Tree("[bold]Section Identification[/]", guide_style="dim")

    for group_label, section_keys in SECTION_GROUPS:
        # Collect all findings that belong to any section in this group
        group_findings: list[Finding] = []
        for key in section_keys:
            group_findings.extend(by_section.get(key, []))

        # Determine group header style
        if any(f.severity == "critical" for f in group_findings):
            badge = f"[bold red][{len(group_findings)} finding(s)][/]"
            label_style = "bold red"
        elif any(f.severity == "warning" for f in group_findings):
            badge = f"[bold yellow][{len(group_findings)} finding(s)][/]"
            label_style = "bold yellow"
        elif group_findings:
            badge = f"[bold cyan][{len(group_findings)} finding(s)][/]"
            label_style = "bold cyan"
        else:
            badge = ""
            label_style = "bold"

        group_node = root.add(f"[{label_style}]{group_label}[/]  {badge}")

        for key in section_keys:
            sec_findings = by_section.get(key, [])
            if key not in found_names:
                sec_node = group_node.add(f"[red]✗[/] [dim]{key}[/] [dim](not found)[/]")
            elif not sec_findings:
                group_node.add(f"[green]✓[/] [dim]{key}[/]")
                continue
            else:
                worst = min(SEVERITY_ORDER.get(f.severity, 9) for f in sec_findings)
                icon = "●" if worst == 0 else "▲"
                icon_style = "bold red" if worst == 0 else "bold yellow"
                sec_node = group_node.add(f"[{icon_style}]{icon}[/] [dim]{key}[/]")

            if sec_findings:
                for f in sorted(sec_findings, key=lambda x: SEVERITY_ORDER.get(x.severity, 9)):
                    sec_node.add(_finding_label(f))

    # Document-level findings (no section_name)
    doc_findings = by_section.get(None, [])
    if doc_findings:
        worst = min(SEVERITY_ORDER.get(f.severity, 9) for f in doc_findings)
        badge = f"[bold red][{len(doc_findings)}][/]" if worst == 0 else f"[bold yellow][{len(doc_findings)}][/]"
        doc_node = root.add(f"[bold]Document-level[/]  {badge}")
        for f in sorted(doc_findings, key=lambda x: SEVERITY_ORDER.get(x.severity, 9)):
            doc_node.add(_finding_label(f))

    return root


def display_eval(
    extraction: BatchRecordExtraction,
    eval_result: EvalResult,
    sections: list[DocumentSection],
) -> None:
    console.print()
    console.print(_summary_panel(extraction, eval_result, sections))
    console.print()

    tree = _build_section_tree(eval_result.findings, sections)
    console.print(Panel(tree, border_style="dim", padding=(0, 1)))

    console.print()
    console.print("[dim]" + "─" * 60 + "[/]")
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
