from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import PatientInput
from app.retrieve_id import retrieve_trials_dual, explain_trial_recommendation

app = FastAPI()

# CORS: allow the local frontend to call this API during development
origins = [
    "http://localhost:8001",
    "http://127.0.0.1:8001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/match-trials")
def match_trials(patient: PatientInput):

    results_A = retrieve_trials_dual(
        age=patient.age,
        gender=patient.gender,
        bmi=patient.bmi,
        hba1c=patient.hba1c,
        pregnant=patient.pregnant,
        condition="Type 2 Diabetes",
        clinical_context=patient.clinical_context,
        top_k=10
    )

    if not results_A:
        return {"message": "No eligible trials found"}

    top_trial = results_A[0]

    explanation = explain_trial_recommendation(
        trial_id=top_trial["nct_id"],
        patient=patient.dict(),
        inclusion_score=top_trial["inclusion_score"],
        exclusion_score=top_trial["exclusion_score"]
    )

    return {
        "top_trial": top_trial,
        "explanation": explanation,
        "other_trials": results_A[1:]
    }
