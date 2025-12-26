from pathlib import Path
import faiss
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INCL_INDEX_PATH = BASE_DIR / "data" / "faiss_inclusion.index"
EXCL_INDEX_PATH = BASE_DIR / "data" / "faiss_exclusion.index"
META_PATH = BASE_DIR / "data" / "faiss_metadata.csv"

MODEL_NAME = "pritamdeka/S-BioBERT-snli-multinli-stsb"
EXCLUSION_THRESHOLD = 0.25

# -------- Neo4j Config --------
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "vansh23106"
NEO4J_DATABASE = "database"


def fetch_trial_constraints(nct_id: str) -> dict:
    """
    Returns all hard constraints for a given trial
    """

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )

    query = """
    MATCH (t:Trial {nct_id: $nct_id})

    OPTIONAL MATCH (t)-[:MIN_AGE]->(minAge:Value)
    OPTIONAL MATCH (t)-[:MAX_AGE]->(maxAge:Value)

    OPTIONAL MATCH (t)-[:BMI_MIN]->(minBMI:Value)
    OPTIONAL MATCH (t)-[:BMI_MAX]->(maxBMI:Value)

    OPTIONAL MATCH (t)-[:HBA1C_MIN]->(minHb:Value)
    OPTIONAL MATCH (t)-[:HBA1C_MAX]->(maxHb:Value)

    OPTIONAL MATCH (t)-[:PREGNANT_ALLOWED]->(preg:Value)

    RETURN
      minAge.value AS min_age,
      maxAge.value AS max_age,
      minBMI.value AS bmi_min,
      maxBMI.value AS bmi_max,
      minHb.value AS hba1c_min,
      maxHb.value AS hba1c_max,
      preg.value AS pregnant_allowed
    """

    with driver.session(database=NEO4J_DATABASE) as session:
        record = session.run(query, nct_id=nct_id).single()

    driver.close()

    if record is None:
        return {}

    return dict(record)


# --------------------------------------------------
# Explanation generator
# --------------------------------------------------

def explain_trial_recommendation(
    trial_id: str,
    patient: dict,
    inclusion_score: float,
    exclusion_score: float
) -> str:

    constraints = fetch_trial_constraints(trial_id)
    reasons = []

    # ---- AGE (assumed mandatory) ----
    if constraints.get("min_age") is not None or constraints.get("max_age") is not None:
        reasons.append(
            f"the patient’s age ({patient['age']}) satisfies the trial’s age criteria "
            f"({constraints.get('min_age', 'any')}–{constraints.get('max_age', 'any')})"
        )

    # ---- BMI (ONLY if patient provided BMI) ----
    if (
        patient.get("bmi") is not None
        and (
            constraints.get("bmi_min") is not None
            or constraints.get("bmi_max") is not None
        )
    ):
        reasons.append(
            f"BMI ({patient['bmi']}) lies within the allowed range "
            f"({constraints.get('bmi_min', 'any')}–{constraints.get('bmi_max', 'any')})"
        )

    # ---- HbA1c (ONLY if patient provided HbA1c) ----
    if (
        patient.get("hba1c") is not None
        and (
            constraints.get("hba1c_min") is not None
            or constraints.get("hba1c_max") is not None
        )
    ):
        reasons.append(
            f"HbA1c ({patient['hba1c']}) is compatible with the trial requirements "
            f"({constraints.get('hba1c_min', 'any')}–{constraints.get('hba1c_max', 'any')})"
        )

    # ---- Pregnancy (ONLY if patient pregnancy known) ----
    if (
        patient.get("pregnant") is not None
        and constraints.get("pregnant_allowed") is False
    ):
        reasons.append(
            "pregnancy is not allowed and the patient is not pregnant"
        )

    # ---- Semantic similarity (ALWAYS included) ----
    reasons.append(
        f"the inclusion criteria is semantically similar "
        f"(similarity score {inclusion_score:.2f})"
    )

    return (
        "This trial was recommended because "
        + ", ".join(reasons)
        + "."
    )
# ============================================================
# QUERY BUILDING
# ============================================================

def build_query(
    age: int,
    gender: str,
    condition: str,
    clinical_context: str = ""
) -> str:
    return (
        f"Patient with {condition}. "
        f"Age {age}. "
        f"Gender {gender}. "
        f"{clinical_context}"
    )

# ============================================================
# GRAPH HARD FILTER
# ============================================================

def get_eligible_trials_from_graph(
    age: int,
    bmi: float,
    hba1c: float,
    pregnant: bool
) -> set[str]:
    """
    HARD eligibility filtering using Neo4j constraints
    """

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )

    query = """
    MATCH (t:Trial)

    OPTIONAL MATCH (t)-[:MIN_AGE]->(minAge:Value)
    OPTIONAL MATCH (t)-[:MAX_AGE]->(maxAge:Value)

    OPTIONAL MATCH (t)-[:BMI_MIN]->(minBMI:Value)
    OPTIONAL MATCH (t)-[:BMI_MAX]->(maxBMI:Value)

    OPTIONAL MATCH (t)-[:HBA1C_MIN]->(minHb:Value)
    OPTIONAL MATCH (t)-[:HBA1C_MAX]->(maxHb:Value)

    OPTIONAL MATCH (t)-[:PREGNANT_ALLOWED]->(preg:Value)

    WHERE
      (minAge IS NULL OR $age >= minAge.value)
    AND
      (maxAge IS NULL OR $age <= maxAge.value)

    AND
      (minBMI IS NULL OR $bmi >= minBMI.value)
    AND
      (maxBMI IS NULL OR $bmi <= maxBMI.value)

    AND
      (minHb IS NULL OR $hba1c >= minHb.value)
    AND
      (maxHb IS NULL OR $hba1c <= maxHb.value)

    AND
      (preg IS NULL OR preg.value = true OR $pregnant = false)

    RETURN t.nct_id AS nct_id
    """

    with driver.session(database=NEO4J_DATABASE) as session:
        records = session.run(
            query,
            age=age,
            bmi=bmi,
            hba1c=hba1c,
            pregnant=pregnant
        )
        eligible_trials = {r["nct_id"] for r in records}

    driver.close()
    return eligible_trials

# ============================================================
# DUAL FAISS RETRIEVAL
# ============================================================

def retrieve_trials_dual(
    age: int,
    gender: str,
    bmi: float,
    hba1c: float,
    pregnant: bool,
    condition: str,
    clinical_context: str,
    top_k: int = 10,
    search_k: int = 100
):
    """
    Correct retrieval pipeline:
    1. HARD filter via Neo4j
    2. Rank by inclusion similarity
    3. Reject by exclusion similarity
    """

    # -------- Load models & indexes --------
    model = SentenceTransformer(MODEL_NAME)

    incl_index = faiss.read_index(str(INCL_INDEX_PATH))
    excl_index = faiss.read_index(str(EXCL_INDEX_PATH))
    meta = pd.read_csv(META_PATH)

    # -------- Graph hard filtering (ONCE) --------
    eligible_trials = get_eligible_trials_from_graph(
        age=age,
        bmi=bmi,
        hba1c=hba1c,
        pregnant=pregnant
    )

    # -------- Build query --------
    query = build_query(age, gender, condition, clinical_context)
    query_vec = model.encode(
        [query],
        normalize_embeddings=True
    ).astype("float32")

    # -------- Broad inclusion search --------
    incl_scores, incl_indices = incl_index.search(query_vec, search_k)

    results = []

    for idx, incl_score in zip(incl_indices[0], incl_scores[0]):

        trial_id = meta.iloc[idx]["nct_number"]

        # HARD FILTER
        if trial_id not in eligible_trials:
            continue

        # Exclusion similarity (same trial index)
        excl_vec = excl_index.reconstruct(int(idx)).reshape(1, -1)
        excl_score = float(np.dot(query_vec, excl_vec.T)[0][0])

        # HARD REJECTION
        if excl_score > EXCLUSION_THRESHOLD:
            continue

        results.append({
            "nct_id": trial_id,
            "inclusion_score": float(incl_score),
            "exclusion_score": excl_score
        })

        if len(results) == top_k:
            break

    return results


"""
# ============================================================
# TEST RUN
# ============================================================

if __name__ == "__main__":

    patient = {
        "age": 45,
        "bmi": 28.0,
        "hba1c": 7.1,
        "pregnant": False,
        "gender" = "Male",
        "clinical_context"=(
            "Newly diagnosed patient. "
            "No prior insulin therapy. "
            "Heart patient."
        )
    }

    print("===== OUTPUT DETAILS FOR PATIENT =====")

    results_A = retrieve_trials_dual(
        age=patient["age"],
        gender=patient["gender"],
        bmi=patient["bmi"],
        hba1c=patient["hba1c"],
        pregnant=patient["pregnant"],
        condition="Type 2 Diabetes",
        clinical_context= patient["clinical_context"],
        top_k=10
    )

    if not results_A:
        print("No eligible trials found.")
        exit()

    # --------------------------------------------------
    # EXPLAIN ONLY THE TOP RESULT
    # --------------------------------------------------
    top_trial = results_A[0]

    explanation = explain_trial_recommendation(
        trial_id=top_trial["nct_id"],
        patient=patient,
        inclusion_score=top_trial["inclusion_score"],
        exclusion_score=top_trial["exclusion_score"]
    )

    print("TOP RECOMMENDATION")
    print("NCT ID:", top_trial["nct_id"])
    print(f"Inclusion score: {top_trial['inclusion_score']:.3f}")
    print(f"Exclusion score: {top_trial['exclusion_score']:.3f}")
    print(explanation)
    print("\n" + "-" * 60 + "\n")

    # --------------------------------------------------
    # PRINT REST (NO EXPLANATION)
    # --------------------------------------------------
    print("OTHER MATCHING TRIALS")

    for r in results_A[1:]:
        print(
            f"{r['nct_id']} | "
            f"Incl: {r['inclusion_score']:.3f} | "
            f"Excl: {r['exclusion_score']:.3f}"
        )
"""