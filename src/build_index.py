"""
Phase 5 — Dual Semantic Index (Inclusion vs Exclusion)

Builds:
- Inclusion FAISS index  (positive eligibility)
- Exclusion FAISS index  (negative eligibility)

NOTE:
- These are SEMANTIC filters
- Graph constraints are HARD filters handled separately

Input:
  t2d_trials_with_incl_excl.csv

Output:
  faiss_inclusion.index
  faiss_exclusion.index
  faiss_metadata.csv
"""

from pathlib import Path
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


# ---------------- CONFIG ---------------- #

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "t2d_trials_with_incl_excl.csv"

INCL_INDEX_PATH = BASE_DIR / "data" / "faiss_inclusion.index"
EXCL_INDEX_PATH = BASE_DIR / "data" / "faiss_exclusion.index"
META_PATH = BASE_DIR / "data" / "faiss_metadata.csv"

MODEL_NAME = "pritamdeka/S-BioBERT-snli-multinli-stsb"
EMBED_DIM = 768

# ---------------------------------------- #


def clean_text(x: str) -> str:
    """
    Minimal, safe cleaning.
    DO NOT normalize medically meaningful words.
    """
    if not isinstance(x, str):
        return ""
    return " ".join(x.split())


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(DATA_PATH)

    df = pd.read_csv(DATA_PATH)

    required_cols = [
        "nct_number",
        "inclusion_criteria",
        "exclusion_criteria"
    ]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    print(f"Loaded {len(df)} trials")

    # -------- Clean text safely -------- #
    df["inclusion_clean"] = df["inclusion_criteria"].apply(clean_text)
    df["exclusion_clean"] = df["exclusion_criteria"].apply(clean_text)

    # -------- Load model -------- #
    model = SentenceTransformer(MODEL_NAME)

    # -------- Encode Inclusion -------- #
    print("Encoding inclusion criteria...")
    incl_embeddings = model.encode(
        df["inclusion_clean"].tolist(),
        normalize_embeddings=True,
        show_progress_bar=True
    )

    # -------- Encode Exclusion -------- #
    print("Encoding exclusion criteria...")
    excl_embeddings = model.encode(
        df["exclusion_clean"].tolist(),
        normalize_embeddings=True,
        show_progress_bar=True
    )

    incl_embeddings = np.asarray(incl_embeddings, dtype="float32")
    excl_embeddings = np.asarray(excl_embeddings, dtype="float32")

    # -------- Build FAISS Indexes -------- #
    incl_index = faiss.IndexFlatIP(EMBED_DIM)
    excl_index = faiss.IndexFlatIP(EMBED_DIM)

    incl_index.add(incl_embeddings)
    excl_index.add(excl_embeddings)

    # -------- Save -------- #
    faiss.write_index(incl_index, str(INCL_INDEX_PATH))
    faiss.write_index(excl_index, str(EXCL_INDEX_PATH))

    df[["nct_number"]].to_csv(META_PATH, index=False)

    print(" Phase 5 completed successfully")
    print(f" Inclusion index → {INCL_INDEX_PATH}")
    print(f" Exclusion index → {EXCL_INDEX_PATH}")
    print(f" Metadata → {META_PATH}")


if __name__ == "__main__":
    main()
