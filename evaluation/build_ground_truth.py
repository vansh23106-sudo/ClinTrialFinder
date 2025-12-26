import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "t2d_trials_with_incl_excl.csv"
OUT_PATH = BASE_DIR / "evaluation" / "weak_ground_truth.csv"

SIM_THRESHOLD = 0.3  # conservative


def main():
    df = pd.read_csv(DATA_PATH)

    required = ["nct_number", "inclusion_criteria", "exclusion_criteria"]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"Missing column: {c}")

    # Combine text
    df["text"] = (
        df["inclusion_criteria"].fillna("") + " " +
        df["exclusion_criteria"].fillna("")
    )

    # TF-IDF similarity (cheap & deterministic)
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf = vectorizer.fit_transform(df["text"])
    sim = cosine_similarity(tfidf)

    rows = []

    for i, row in df.iterrows():
        relevant_idx = [
            j for j, score in enumerate(sim[i])
            if score >= SIM_THRESHOLD and j != i
        ]

        relevant_trials = df.iloc[relevant_idx]["nct_number"].tolist()

        rows.append({
            "query_nct": row["nct_number"],
            "relevant_trials": relevant_trials
        })

    out = pd.DataFrame(rows)
    out.to_csv(OUT_PATH, index=False)
    print(f"Weak ground truth saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
