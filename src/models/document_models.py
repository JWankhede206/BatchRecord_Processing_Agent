from pydantic import BaseModel


class ParsedPage(BaseModel):
    page_number: int
    text: str


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
