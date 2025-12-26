"""
Phase 1 (Refined) — Fetch Structured Eligibility via ClinicalTrials.gov API

Input:
  ctg-studies.csv   (must contain nct_number column)

Output:
  t2d_trials_api_structured.csv
"""

import requests
import pandas as pd
from pathlib import Path
from time import sleep

# ---------------- CONFIG ---------------- #

BASE_DIR = Path(__file__).resolve().parent.parent 
INPUT_PATH = BASE_DIR / "data" / "ctg-studies.csv"
OUTPUT_PATH = BASE_DIR / "data" / "t2d_trials_api_structured.csv"

API_URL = "https://clinicaltrials.gov/api/v2/studies"
REQUEST_DELAY = 0.5  # seconds (polite usage)

# -------------------------------------- #


def fetch_trial_structured(nct_id: str) -> dict | None:
    params = {
        "query.id": nct_id,
        "pageSize": 1
    }

    response = requests.get(API_URL, params=params, timeout=20)
    response.raise_for_status()

    studies = response.json().get("studies", [])
    if not studies:
        return None

    study = studies[0]
    protocol = study.get("protocolSection", {})

    eligibility = protocol.get("eligibilityModule", {})
    conditions = protocol.get("conditionsModule", {})

    return {
        "nct_number": nct_id,
        "minimum_age": eligibility.get("minimumAge"),
        "maximum_age": eligibility.get("maximumAge"),
        "sex": eligibility.get("sex"),
        "accepts_healthy_volunteers": eligibility.get("acceptsHealthyVolunteers"),
        "eligibility_criteria": eligibility.get("eligibilityCriteria"),
        "conditions": "; ".join(conditions.get("conditions", []))
    }


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH)

    # normalize column names
    df.columns = (
        df.columns
        .str.lower()
        .str.strip()
        .str.replace(" ", "_")
    )

    if "nct_number" not in df.columns:
        raise ValueError("Column 'nct_number' not found in input file")

    nct_ids = df["nct_number"].dropna().unique().tolist()

    print(f"Fetching structured data for {len(nct_ids)} trials...")

    records = []

    for i, nct in enumerate(nct_ids, start=1):
        try:
            data = fetch_trial_structured(nct)
            if data:
                records.append(data)
        except Exception as e:
            print(f"[WARN] Failed for {nct}: {e}")

        if i % 20 == 0:
            sleep(REQUEST_DELAY)

    out_df = pd.DataFrame(records)
    out_df.to_csv(OUTPUT_PATH, index=False)

    print("\n API fetch completed successfully")
    print(f" Saved to: {OUTPUT_PATH}")
    print("\nSample rows:")
    print(out_df.head())


if __name__ == "__main__":
    main()
