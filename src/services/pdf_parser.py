from pathlib import Path

import fitz  # PyMuPDF

from ..models.document_models import ParsedDocument, ParsedPage
from ..utils.logger import get_logger

logger = get_logger(__name__)


def parse_pdf(file_path: Path) -> ParsedDocument:
    logger.info("Parsing PDF: %s", file_path.name)
    doc = fitz.open(str(file_path))
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        pages.append(ParsedPage(page_number=page_num + 1, text=text))
    doc.close()
    logger.info("Parsed %d pages from %s", len(pages), file_path.name)
    return ParsedDocument(
        file_name=file_path.stem,
        file_path=str(file_path),
        pages=pages,
    )
