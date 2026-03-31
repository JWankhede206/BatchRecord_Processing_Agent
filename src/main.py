import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models.extraction_models import BatchRecordExtraction
from src.services.display import display_eval, display_pipeline_done, display_pipeline_start
from src.services.eval_runner import run_eval
from src.services.field_extractor import aextract_fields
from src.services.pdf_parser import parse_pdf
from src.services.procedure_extractor import aextract_procedure
from src.services.section_extractor import aextract_sections
from src.services.summary_generator import generate_summary
from src.utils.file_io import write_json, write_text
from src.utils.logger import get_logger

logger = get_logger("main")


async def process_file(pdf_path: Path, output_dir: Path) -> None:
    file_name = pdf_path.stem
    logger.info("Processing file: %s", pdf_path.name)

    # 1. Parse PDF (sync, fast)
    parsed_doc = parse_pdf(pdf_path)
    write_json(
        output_dir / "parsed" / f"{file_name}.json",
        parsed_doc.model_dump(),
    )
    logger.info("Parsed PDF: %s", pdf_path.name)

    # 2. Run sections + procedure in parallel
    sections_task = asyncio.create_task(aextract_sections(parsed_doc))
    procedure_task = asyncio.create_task(aextract_procedure(parsed_doc))

    # 3. Wait for sections, then start fields
    sections = await sections_task
    write_json(
        output_dir / "extracted" / f"{file_name}_sections.json",
        [s.model_dump() for s in sections],
    )
    logger.info("Extracted sections: %d", len(sections))

    fields_task = asyncio.create_task(aextract_fields(parsed_doc, sections))

    # 4. Wait for remaining tasks
    procedure_steps, extraction = await asyncio.gather(procedure_task, fields_task)

    # Write extraction outputs
    write_json(
        output_dir / "extracted" / f"{file_name}_fields.json",
        {
            "metadata": extraction.metadata.model_dump(),
            "materials": [m.model_dump() for m in extraction.materials],
            "equipment": [e.model_dump() for e in extraction.equipment],
        },
    )
    logger.info("Extracted fields")

    write_json(
        output_dir / "extracted" / f"{file_name}_procedure.json",
        [s.model_dump() for s in procedure_steps],
    )
    logger.info("Extracted procedure steps: %d", len(procedure_steps))

    # 5. Merge and finalize
    extraction = BatchRecordExtraction(
        metadata=extraction.metadata,
        sections=sections,
        materials=extraction.materials,
        equipment=extraction.equipment,
        procedure_steps=procedure_steps,
    )

    # 6. Run eval
    eval_result = run_eval(parsed_doc, extraction, sections)
    write_json(
        output_dir / "findings" / f"{file_name}_findings.json",
        eval_result.model_dump(),
    )
    logger.info("Ran findings checks: %d findings", len(eval_result.findings))

    # 7. Display eval results
    display_eval(extraction, eval_result, sections)

    # 8. Generate summary
    summary = generate_summary(extraction, eval_result, sections)
    write_text(
        output_dir / "summaries" / f"{file_name}_summary.md",
        summary,
    )
    logger.info("Wrote summary")


async def run() -> None:
    parser = argparse.ArgumentParser(description="Batch Record Agent - process pharma batch record PDFs")
    parser.add_argument("--input", default="data", help="Input directory containing PDF files")
    parser.add_argument("--output", default="output", help="Output directory for results")
    args = parser.parse_args()

    input_dir = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()

    if not input_dir.exists():
        logger.error("Input directory does not exist: %s", input_dir)
        sys.exit(1)

    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in %s", input_dir)
        sys.exit(0)

    logger.info("Found %d PDF file(s) in %s", len(pdf_files), input_dir)
    display_pipeline_start(len(pdf_files), str(input_dir))

    failed = 0
    for pdf_path in pdf_files:
        try:
            await process_file(pdf_path, output_dir)
        except Exception:
            logger.exception("Failed to process %s, skipping", pdf_path.name)
            failed += 1

    display_pipeline_done(len(pdf_files), failed)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
