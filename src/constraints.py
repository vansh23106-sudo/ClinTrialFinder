"""
Phase 3 — Structured Eligibility Extraction (FULLY FIXED)

Uses structured API fields:
- min_age
- max_age
- gender

Extracts from eligibility text:
- bmi_min, bmi_max
- hba1c_min, hba1c_max
- pregnant_allowed

Input:
  data/t2d_trials_with_incl_excl.csv

Output:
  data/t2d_structured_eligibility.csv
"""

from pathlib import Path
import pandas as pd
import re
from typing import Optional, Tuple

# ---------------- PATHS ---------------- #

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "t2d_trials_api_structured.csv"
OUTPUT_PATH = BASE_DIR / "data" / "t2d_structured_eligibility.csv"

# --------------- REGEX ----------------- #

# BMI patterns - handle both ranges and single bounds
BMI_RANGE_PATTERN = r"bmi\s+(?:between\s+)?(\d+\.?\d*)\s*(?:kg/m2|kg/m²)?\s*(?:to|-|and)\s+(\d+\.?\d*)\s*(?:kg/m2|kg/m²)?"
BMI_MIN_PATTERN = r"bmi\s*(?:≥|>=|>)\s*(\d+\.?\d*)\s*(?:kg/m2|kg/m²)?"
BMI_MAX_PATTERN = r"bmi\s*(?:≤|<=|<)\s*(\d+\.?\d*)\s*(?:kg/m2|kg/m²)?"

# HbA1c patterns - handle multiple formats
HBA1C_RANGE_PATTERN = r"(?:hba1c|hemoglobin a1c|hb a 1c)(?:\s+level)?\s+(?:of\s+)?(\d+\.?\d*)\s*%?\s*(?:to|-|and)\s+(\d+\.?\d*)\s*%"
HBA1C_BETWEEN_PATTERN = r"(?:hba1c|hemoglobin a1c|hb a 1c)\s+between\s+(\d+\.?\d*)\s*(?:to|-|and)\s*(\d+\.?\d*)\s*%"
HBA1C_MIN_PATTERN = r"(?:hba1c|hemoglobin a1c|hb a 1c)\s*(?:≥|>=|>)\s*(\d+\.?\d*)\s*%?"
HBA1C_MAX_PATTERN = r"(?:hba1c|hemoglobin a1c|hb a 1c)\s*(?:≤|<=|<)\s*(\d+\.?\d*)\s*%?"

PREGNANCY_KEYWORDS = [
    "pregnant",
    "pregnancy",
    "lactating",
    "breastfeeding",
    "nursing women",
    "non-childbearing",
    "not allowed to become pregnant"
]

# ------------- HELPERS ---------------- #

def normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = text.lower()
    # Normalize line breaks
    text = text.replace("\r", " ").replace("\n", " ")

    # FIX common encoding artifacts
    text = (
        text
        .replace("Â²", "²")
        .replace("Â", "")
    )

    # UNESCAPE common operators
    text = (
        text
        .replace(r"\>", ">")
        .replace(r"\<", "<")
        .replace(r"\≥", "≥")
        .replace(r"\≤", "≤")
    )

    # Normalize BMI unit variants
    text = re.sub(r"kg\s*/\s*m\s*[²2]", "kg/m2", text, flags=re.IGNORECASE)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def parse_age(value) -> Optional[int]:
    """Converts '30 Years' → 30"""
    if pd.isna(value):
        return None
    m = re.search(r"\d{1,3}", str(value))
    return int(m.group()) if m else None


def normalize_gender(value: str) -> str:
    if not isinstance(value, str):
        return "All"
    v = value.strip().lower()
    if v in {"male", "m"}:
        return "Male"
    if v in {"female", "f"}:
        return "Female"
    return "All"


def extract_bmi(text: str) -> Tuple[Optional[float], Optional[float]]:
    # Try range pattern first
    m = re.search(BMI_RANGE_PATTERN, text, re.IGNORECASE)
    if m:
        return float(m.group(1)), float(m.group(2))
    
    # Try min/max separately
    bmi_min = None
    bmi_max = None
    
    m = re.search(BMI_MIN_PATTERN, text, re.IGNORECASE)
    if m:
        bmi_min = float(m.group(1))
    
    m = re.search(BMI_MAX_PATTERN, text, re.IGNORECASE)
    if m:
        bmi_max = float(m.group(1))
    
    return bmi_min, bmi_max


def extract_hba1c(text: str) -> Tuple[Optional[float], Optional[float]]:
    # Try "between X and Y" pattern
    m = re.search(HBA1C_BETWEEN_PATTERN, text, re.IGNORECASE)
    if m:
        return float(m.group(1)), float(m.group(2))
    
    # Try "of X - Y%" pattern
    m = re.search(HBA1C_RANGE_PATTERN, text, re.IGNORECASE)
    if m:
        return float(m.group(1)), float(m.group(2))
    
    # Try min/max separately
    h_min = None
    h_max = None
    
    m = re.search(HBA1C_MIN_PATTERN, text, re.IGNORECASE)
    if m:
        h_min = float(m.group(1))
    
    m = re.search(HBA1C_MAX_PATTERN, text, re.IGNORECASE)
    if m:
        h_max = float(m.group(1))
    
    return h_min, h_max


def extract_pregnancy_allowed(exclusion_text: str) -> bool:
    """
    If pregnancy-related term appears in EXCLUSION criteria,
    pregnant women are NOT allowed.
    """
    text = exclusion_text.lower()
    for kw in PREGNANCY_KEYWORDS:
        if kw in text:
            return False
    return True


# --------------- MAIN ------------------ #

def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(INPUT_PATH)

    df = pd.read_csv(INPUT_PATH)

    required = [
        "nct_number",
        "min_age",
        "max_age",
        "gender",
        "eligibility_criteria",
        "eligibility_criteria",
    ]

    for c in required:
        if c not in df.columns:
            raise ValueError(f"Missing column: {c}")

    records = []

    for _, row in df.iterrows():
        # Skip rows with missing NCT number
        if pd.isna(row["nct_number"]):
            continue
            
        incl_text = normalize(row["eligibility_criteria"])
        text = row["eligibility_criteria"]
        excl_text = normalize(row["eligibility_criteria"])
        
        records.append({
            "nct_number": row["nct_number"],
            "min_age": parse_age(row["min_age"]),
            "max_age": parse_age(row["max_age"]),
            "gender": normalize_gender(row["gender"]),
            "bmi_min": extract_bmi(incl_text)[0],
            "bmi_max": extract_bmi(incl_text)[1],
            "hba1c_min": extract_hba1c(incl_text)[0],
            "hba1c_max": extract_hba1c(incl_text)[1],
            "pregnant_allowed": extract_pregnancy_allowed(text),
        })

    out_df = pd.DataFrame(records)
    out_df.to_csv(OUTPUT_PATH, index=False)

    print(" Phase 3 extraction completed successfully")
    print(f" Saved to: {OUTPUT_PATH}")
    print(f" Processed {len(out_df)} trials")
    print("\nSample:")
    print(out_df.head())


if __name__ == "__main__":
    main()