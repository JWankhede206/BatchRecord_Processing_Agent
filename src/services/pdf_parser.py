import base64
from pathlib import Path

import fitz  # PyMuPDF

from ..models.document_models import ParsedDocument, ParsedPage
from ..utils.logger import get_logger

logger = get_logger(__name__)


def _build_table_markdown(table) -> str:
    """Convert a PyMuPDF table to markdown with explicit [BLANK] markers."""
    rows = table.extract()
    if not rows:
        return ""

    md_rows = []
    for row in rows:
        cells = []
        for cell in row:
            val = cell.strip() if isinstance(cell, str) else ""
            cells.append(val if val else "[BLANK]")
        md_rows.append("| " + " | ".join(cells) + " |")

    # Add separator after header row
    if len(md_rows) >= 1:
        col_count = len(rows[0])
        separator = "| " + " | ".join(["---"] * col_count) + " |"
        md_rows.insert(1, separator)

    return "\n".join(md_rows)


def _enrich_page_text(page, plain_text: str) -> str:
    """
    Build enriched text by appending extracted markdown tables below the plain text.
    Empty cells are explicitly marked as [BLANK] so the LLM can distinguish
    unfilled fields from filled ones.
    """
    try:
        tables = page.find_tables()
    except Exception:
        return plain_text

    if not tables.tables:
        return plain_text

    table_blocks = []
    for i, table in enumerate(tables.tables, 1):
        md = _build_table_markdown(table)
        if md:
            table_blocks.append(f"[TABLE {i}]\n{md}")

    if not table_blocks:
        return plain_text

    return plain_text + "\n\n" + "\n\n".join(table_blocks)


def _render_page_b64(page) -> str:
    """Render page to PNG at 1.5x zoom and return as base64 string."""
    try:
        matrix = fitz.Matrix(1.5, 1.5)
        pixmap = page.get_pixmap(matrix=matrix)
        png_bytes = pixmap.tobytes("png")
        return base64.b64encode(png_bytes).decode("utf-8")
    except Exception:
        return ""


def parse_pdf(file_path: Path) -> ParsedDocument:
    logger.info("Parsing PDF: %s", file_path.name)
    doc = fitz.open(str(file_path))
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        plain_text = page.get_text("text")
        enriched_text = _enrich_page_text(page, plain_text)
        image_b64 = _render_page_b64(page)
        pages.append(ParsedPage(
            page_number=page_num + 1,
            text=plain_text,
            enriched_text=enriched_text,
            image_b64=image_b64,
        ))
    doc.close()
    logger.info("Parsed %d pages from %s (with tables + images)", len(pages), file_path.name)
    return ParsedDocument(
        file_name=file_path.stem,
        file_path=str(file_path),
        pages=pages,
    )
