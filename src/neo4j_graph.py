from pathlib import Path
import pandas as pd
from neo4j import GraphDatabase
from typing import Optional

# ============================================================
# PATH CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "t2d_structured_eligibility.csv"


# ============================================================
# NEO4J CONFIG  (CHANGE PASSWORD ONLY)
# ============================================================

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "vansh23106"     
NEO4J_DATABASE = "database"      


# ============================================================
# CONSTRAINT ENFORCEMENT
# ============================================================

def normalize_range(min_val: Optional[float], max_val: Optional[float]):
    if min_val is None and max_val is None:
        return None, None
    if min_val is not None and max_val is not None and min_val > max_val:
        min_val, max_val = max_val, min_val
    return min_val, max_val

def clean_nan(row: dict) -> dict:
    """
    Convert pandas NaN values to Python None
    (Neo4j cannot handle NaN)
    """
    for k, v in row.items():
        if pd.isna(v):
            row[k] = None
    return row

def enforce_constraints(row: pd.Series) -> pd.Series:
    # -------- AGE --------
    row["min_age"], row["max_age"] = normalize_range(
        row.get("min_age"), row.get("max_age")
    )

    if row["min_age"] is not None and row["min_age"] < 0:
        row["min_age"] = None
    if row["max_age"] is not None and row["max_age"] > 120:
        row["max_age"] = None

    # -------- BMI --------
    row["bmi_min"], row["bmi_max"] = normalize_range(
        row.get("bmi_min"), row.get("bmi_max")
    )

    # -------- HbA1c --------
    row["hba1c_min"], row["hba1c_max"] = normalize_range(
        row.get("hba1c_min"), row.get("hba1c_max")
    )

    # -------- Pregnancy --------
    if row.get("pregnant_allowed") not in [True, False]:
        row["pregnant_allowed"] = None

    return row


# ============================================================
# NEO4J INGESTOR
# ============================================================

class Neo4jIngestor:
    def __init__(self, uri, user, password, database):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    

    def ingest_trial(self, row: dict):

        # mandatory check
        if "nct_id" not in row or row["nct_id"] is None:
            return

        row = clean_nan(row)

        with self.driver.session(database=self.database) as session:
            session.run(
                """
                MERGE (t:Trial {nct_id: $nct_id})

                // ---------- AGE ----------
                FOREACH (_ IN CASE WHEN $min_age IS NOT NULL THEN [1] ELSE [] END |
                    CREATE (v:Value {value: $min_age})
                    CREATE (t)-[:MIN_AGE]->(v)
                )

                FOREACH (_ IN CASE WHEN $max_age IS NOT NULL THEN [1] ELSE [] END |
                    CREATE (v:Value {value: $max_age})
                    CREATE (t)-[:MAX_AGE]->(v)
                )

                // ---------- BMI ----------
                FOREACH (_ IN CASE WHEN $bmi_min IS NOT NULL THEN [1] ELSE [] END |
                    CREATE (v:Value {value: $bmi_min})
                    CREATE (t)-[:BMI_MIN]->(v)
                )

                FOREACH (_ IN CASE WHEN $bmi_max IS NOT NULL THEN [1] ELSE [] END |
                    CREATE (v:Value {value: $bmi_max})
                    CREATE (t)-[:BMI_MAX]->(v)
                )

                // ---------- HBA1C ----------
                FOREACH (_ IN CASE WHEN $hba1c_min IS NOT NULL THEN [1] ELSE [] END |
                    CREATE (v:Value {value: $hba1c_min})
                    CREATE (t)-[:HBA1C_MIN]->(v)
                )

                FOREACH (_ IN CASE WHEN $hba1c_max IS NOT NULL THEN [1] ELSE [] END |
                    CREATE (v:Value {value: $hba1c_max})
                    CREATE (t)-[:HBA1C_MAX]->(v)
                )

                // ---------- PREGNANCY ----------
                FOREACH (_ IN CASE WHEN $pregnant_allowed IS NOT NULL THEN [1] ELSE [] END |
                    CREATE (v:Value {value: $pregnant_allowed})
                    CREATE (t)-[:PREGNANT_ALLOWED]->(v)
                )
                """,
                **row
            )



# ============================================================
# MAIN
# ============================================================

def main():
    # -------- Load CSV --------
    df = pd.read_csv(INPUT_PATH)

    # 🔥 CRITICAL FIX 🔥
    # Standardize trial identifier column
    df = df.rename(columns={"nct_number": "nct_id"})

    # -------- Apply constraints --------
    df = df.apply(enforce_constraints, axis=1)

    # -------- Neo4j ingestion --------
    ingestor = Neo4jIngestor(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE
    )

    for _, row in df.iterrows():
        ingestor.ingest_trial(row.to_dict())

    ingestor.close()
    print("✅ Phase 4 completed: Neo4j graph built successfully")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
