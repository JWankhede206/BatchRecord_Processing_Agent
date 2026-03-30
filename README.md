# Batch Record Agent

A local Python pipeline that processes pharma batch record PDFs, extracts structured information using OpenAI, runs basic completeness checks, and writes JSON plus markdown summaries.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and set your OpenAI API key:

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

Place PDF batch records in the `data/` folder, then run:

```bash
python src/main.py
```

With custom paths:

```bash
python src/main.py --input data --output output
```

## Output Files

For each processed PDF, the pipeline writes:

| File | Location |
|------|----------|
| Parsed pages | `output/parsed/<file_name>.json` |
| Extracted sections | `output/extracted/<file_name>_sections.json` |
| Extracted fields | `output/extracted/<file_name>_fields.json` |
| Extracted procedures | `output/extracted/<file_name>_procedure.json` |
| Findings | `output/findings/<file_name>_findings.json` |
| Summary | `output/summaries/<file_name>_summary.md` |

## Testing

```bash
python -m pytest tests/
```

## Limitations

- Designed for local single-user use only
- No database, queue, or web interface
- No deep GMP/compliance validation
- No cross-document reconciliation
- Relies on OpenAI for extraction accuracy
- Works best with well-structured batch record PDFs
