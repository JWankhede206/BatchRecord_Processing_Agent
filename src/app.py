import asyncio
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, File, UploadFile
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from src.config import TARGET_SECTIONS
from src.models.extraction_models import BatchRecordExtraction
from src.services.eval_runner import run_eval
from src.services.field_extractor import aextract_fields
from src.services.pdf_parser import parse_pdf
from src.services.procedure_extractor import aextract_procedure
from src.services.section_extractor import aextract_sections
from src.services.summary_generator import generate_summary
from src.utils.logger import get_logger

logger = get_logger("app")

app = FastAPI(title="Batch Record Agent")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/process")
async def process_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return JSONResponse(
            status_code=400,
            content={"error": "Please upload a PDF file."},
        )

    tmp_path = None
    try:
        # Save upload to temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            content = await file.read()
            tmp.write(content)

        logger.info("Processing uploaded file: %s", file.filename)

        # 1. Parse PDF (sync, fast)
        parsed_doc = parse_pdf(tmp_path)
        parsed_doc.file_name = Path(file.filename).stem

        # 2. Run sections + procedure in parallel (both only need parsed_doc)
        sections_task = asyncio.create_task(aextract_sections(parsed_doc))
        procedure_task = asyncio.create_task(aextract_procedure(parsed_doc))

        # 3. Wait for sections, then start fields (while procedure may still run)
        sections = await sections_task
        fields_task = asyncio.create_task(aextract_fields(parsed_doc, sections))

        # 4. Wait for both remaining tasks
        procedure_steps, extraction = await asyncio.gather(procedure_task, fields_task)

        # 5. Merge procedure into extraction
        extraction = BatchRecordExtraction(
            metadata=extraction.metadata,
            sections=sections,
            materials=extraction.materials,
            equipment=extraction.equipment,
            procedure_steps=procedure_steps,
        )

        # 6. Eval + summary (sync, fast)
        eval_result = run_eval(parsed_doc, extraction, sections)
        summary = generate_summary(extraction, eval_result, sections)

        # Build response
        meta = extraction.metadata
        critical = sum(1 for f in eval_result.findings if f.severity == "critical")
        warnings = sum(1 for f in eval_result.findings if f.severity == "warning")
        infos = sum(1 for f in eval_result.findings if f.severity == "info")

        return {
            "file_name": parsed_doc.file_name,
            "metadata": meta.model_dump(),
            "sections_found": [s.name for s in sections],
            "sections_detail": [s.model_dump() for s in sections],
            "target_sections": TARGET_SECTIONS,
            "findings": [f.model_dump() for f in eval_result.findings],
            "summary_counts": {
                "critical": critical,
                "warning": warnings,
                "info": infos,
                "total": len(eval_result.findings),
            },
            "extraction_stats": {
                "sections": len(sections),
                "target_sections": len(TARGET_SECTIONS),
                "procedure_steps": len(procedure_steps),
                "materials": len(extraction.materials),
                "equipment": len(extraction.equipment),
            },
            "is_template": any(
                f.finding_type == "likely_template_document"
                for f in eval_result.findings
            ),
            "summary_markdown": summary,
        }

    except Exception as e:
        logger.exception("Pipeline failed for %s", file.filename)
        return JSONResponse(
            status_code=500,
            content={"error": f"Processing failed: {str(e)}"},
        )
    finally:
        if tmp_path and tmp_path.exists():
            os.unlink(tmp_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True)
