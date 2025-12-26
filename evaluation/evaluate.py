# ============================================================
# PHASE 7 — Evaluation Framework
# ============================================================

import pandas as pd
from pathlib import Path

# Baselines
from evaluation.baselines import tfidf_retrieve, jaccard_retrieve

# Main system
from retrieval.retrieve_id import retrieve_trials_dual


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = BASE_DIR / "data" / "t2d_trials_with_incl_excl.csv"
GT_PATH = BASE_DIR / "evaluation" / "weak_ground_truth.csv"


# ============================================================
# METRIC
# ============================================================

def precision_at_k(predicted_ids, relevant_ids, k=10):
    """
    predicted_ids: List[str]
    relevant_ids: List[str]
    """
    if not predicted_ids:
        return 0.0
    return len(set(predicted_ids[:k]) & set(relevant_ids)) / k


# ============================================================
# MAIN EVALUATION
# ============================================================

def main():

    # ---------- Load data ----------
    df = pd.read_csv(DATA_PATH)
    gt = pd.read_csv(GT_PATH)

    # Combine text for baselines
    df["text"] = (
        df["inclusion_criteria"].fillna("") + " " +
        df["exclusion_criteria"].fillna("")
    )

    # Map nct_number → row
    df_index = {row["nct_number"]: row for _, row in df.iterrows()}

    results = {
        "TF-IDF": [],
        "Jaccard": [],
        "ClinicalBERT": []
    }

    # ---------- Evaluate on subset (start small) ----------
    eval_samples = gt.sample(50, random_state=42)

    for _, row in eval_samples.iterrows():

        query_nct = row["query_nct"]
        relevant = eval(row["relevant_trials"])

        # Safety check
        if query_nct not in df_index:
            continue

        query_text = df_index[query_nct]["text"]

        # ==============================
        # TF-IDF
        # ==============================
        tfidf_ids = tfidf_retrieve(
            df=df,
            query_text=query_text,
            top_k=10
        )

        results["TF-IDF"].append(
            precision_at_k(tfidf_ids, relevant)
        )

        # ==============================
        # Jaccard
        # ==============================
        jaccard_ids = jaccard_retrieve(
            df=df,
            query_text=query_text,
            top_k=10
        )

        results["Jaccard"].append(
            precision_at_k(jaccard_ids, relevant)
        )

        # ==============================
        # ClinicalBERT (YOUR SYSTEM)
        # ==============================
        bert_results = retrieve_trials_dual(
            age=45,
            gender="Male",
            bmi=None,
            hba1c=None,
            pregnant=False,
            condition="Type 2 Diabetes",
            clinical_context=query_text,
            top_k=10
        )

        bert_ids = [r["nct_id"] for r in bert_results]

        results["ClinicalBERT"].append(
            precision_at_k(bert_ids, relevant)
        )

    # ---------- Print results ----------
    print("\n===== PHASE 7 RESULTS (Precision@10) =====\n")

    for method, scores in results.items():
        if scores:
            print(f"{method}: {sum(scores) / len(scores):.4f}")
        else:
            print(f"{method}: No valid samples")


if __name__ == "__main__":
    main()
