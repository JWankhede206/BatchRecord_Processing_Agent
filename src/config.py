import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_DIR = PROJECT_ROOT / "data"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"

TARGET_SECTIONS = [
    "approvals",
    "product_details",
    "training_log",
    "reference_docs",
    "bill_of_materials",
    "processing_equipment",
    "area_clearance",
    "production_procedure",
    "post_production_sampling",
    "yield_calculations",
    "production_comment_log",
    "exception_log",
    "post_production_review",
    "qa_disposition",
]
