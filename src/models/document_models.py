from pydantic import BaseModel


class ParsedPage(BaseModel):
    page_number: int
    text: str
    enriched_text: str = ""   # plain text + injected markdown tables with [BLANK] markers
    image_b64: str = ""       # base64 PNG of the rendered page (1.5x zoom)


class ParsedDocument(BaseModel):
    file_name: str
    file_path: str
    pages: list[ParsedPage]


class DocumentSection(BaseModel):
    name: str
    start_page: int
    end_page: int
    raw_text: str
    confidence: float
