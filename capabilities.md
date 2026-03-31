# Batch Record Agent — Capabilities

## Overview

Batch Record Agent is a local Python pipeline that ingests pharmaceutical batch record PDFs, extracts structured data using OpenAI GPT-4o, runs rule-based completeness checks, and surfaces findings through a terminal dashboard and a web UI. It is designed for single-user local use with no database or external infrastructure.

---

## How It Works

### Pipeline Steps

When a PDF is submitted (via CLI or web upload), the agent runs the following steps in order:

```
1. PDF Parsing        — extract raw text per page (PyMuPDF)
2. Section Detection  — identify document sections via LLM  ─┐ parallel
3. Procedure Extraction — extract numbered procedure steps   ─┘
4. Field Extraction   — extract metadata, materials, equipment (starts after sections)
5. Eval Runner        — rule-based completeness checks (no LLM)
6. Summary Generation — build markdown summary report
```

Steps 2 and 3 run concurrently using `asyncio`. Step 4 starts as soon as Step 2 finishes, overlapping with Step 3. This reduces total wall time by ~40% compared to sequential execution.

---

## Extraction Capabilities

### 1. PDF Parsing
- Reads any PDF from disk using PyMuPDF (`fitz`)
- Extracts plain text per page with page numbers preserved
- Handles multi-page documents (tested up to 17 pages)

### 2. Section Detection
The LLM identifies up to **14 target sections** within the document:

| Section Key | Description |
|---|---|
| `approvals` | Master batch record approval signatures |
| `product_details` | Product description, part number, batch quantity, storage conditions |
| `training_log` | Signature and training log for all personnel |
| `reference_docs` | Referenced SOPs and documentation |
| `bill_of_materials` | Materials list with lot numbers and quantities |
| `processing_equipment` | Equipment list with calibration records |
| `area_clearance` | GMP area clearance steps |
| `production_procedure` | Numbered manufacturing procedure steps |
| `post_production_sampling` | Post-production sampling instructions |
| `yield_calculations` | Granulation yield formula and recorded values |
| `production_comment_log` | Operator observations and comments |
| `exception_log` | Deviations, planned deviations, nonconformances |
| `post_production_review` | Review signatures for production and QA |
| `qa_disposition` | Final QA release/reject disposition |

For each section found, the agent records:
- Page range (start and end page)
- Raw text excerpt (up to ~500 characters)
- Confidence score (0.0–1.0)

### 3. Field Extraction
Structured metadata extracted from the document:

| Field | Description |
|---|---|
| `title` | Full document title |
| `version` | Version number |
| `lot_number` | Production lot number |
| `part_number` | Product part/item number |
| `batch_size` | Total batch quantity with units |
| `storage_conditions` | Storage requirements |

**Bill of Materials rows** — per material:
- Description
- Part number
- Quantity required
- Lot number
- Quantity staged
- Expiry / retest date

**Processing Equipment rows** — per piece of equipment:
- Equipment description
- Equipment ID
- Previous calibration date
- Calibration required status

### 4. Procedure Extraction
Each numbered production procedure step is extracted with:
- Step number (integer)
- Title (brief label)
- Full instruction text
- Page number
- Expected entries (weights, times, signatures to be filled in)
- Limits or targets (tolerances, ranges, target values)
- Notes and cautions
- Container or sample labels to be applied

---

## Eval Checks

The eval runner performs **9 distinct completeness checks** using rule-based logic (no LLM):

### Finding Types

| Finding Type | Severity | How It Is Detected |
|---|---|---|
| `missing_section` | Warning | One or more of the 14 target sections not identified in the document |
| `missing_field` | Warning / Info | Metadata field (title, version, lot number, etc.) could not be extracted — lot_number is Warning, others are Info |
| `blank_signature` | Warning | Signature fields (`___`) detected in the Approvals or Training Log sections |
| `blank_verification` | Warning | Blank "Performed By / Date" or "Verified By / Date" fields detected in any section |
| `blank_recorded_value` | Warning | More than 10 blank fill-in fields (`___`) found across the full document |
| `empty_comment_log` | Info | Production Comment Log section exists but contains no numbered entries |
| `empty_exception_log` | Info | Exception Log section exists but contains no substantive entries |
| `empty_disposition` | Critical | QA Disposition section found but no selection (Released / Conditional / Research / Rejected) is checked or marked |
| `likely_template_document` | Critical | Document flagged as a blank template based on 2+ indicators: missing lot number, more than 20 blank fill-in fields, and no detected signatures |

### Severity Levels

| Level | Meaning |
|---|---|
| **Critical** | Core completeness failure — disposition not made or document is unfilled template |
| **Warning** | Required fields or signatures are blank or sections are missing |
| **Info** | Logs are empty — may be expected for clean runs with no exceptions |

---

## Outputs

For each processed PDF, the agent writes six files:

| File | Location | Format |
|---|---|---|
| Parsed pages | `output/parsed/<file>.json` | JSON — full page text per page number |
| Extracted sections | `output/extracted/<file>_sections.json` | JSON — section list with page ranges and confidence |
| Extracted fields | `output/extracted/<file>_fields.json` | JSON — metadata, materials, equipment |
| Procedure steps | `output/extracted/<file>_procedure.json` | JSON — ordered step list with limits and entries |
| Findings | `output/findings/<file>_findings.json` | JSON — full finding list with severity and stats |
| Summary | `output/summaries/<file>_summary.md` | Markdown — human-readable report |

---

## Interfaces


### CLI
```bash
python src/main.py                          # process all PDFs in data/
python src/main.py --input data --output output
```
Displays a Rich terminal dashboard after each file with findings table, sections checklist, and extraction stats.

### Web UI
```bash
python src/app.py                           # starts on http://localhost:8000
```
Single-page interface for manual PDF upload with live results display:
- Document identity card
- Critical / Warning / Info count badges
- Findings table sorted by severity
- Sections checklist (14 targets)
- Extraction stats (sections, steps, materials, equipment)
- Template vs. completed assessment

---

## Tech Stack

| Component | Technology |
|---|---|
| PDF parsing | PyMuPDF (`fitz`) |
| LLM extraction | OpenAI GPT-4o via `AsyncOpenAI` |
| Data validation | Pydantic v2 |
| Web backend | FastAPI + uvicorn |
| Terminal display | Rich |
| Async execution | Python `asyncio` |
| Config | python-dotenv |
