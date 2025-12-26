from pydantic import BaseModel
from typing import Optional

class PatientInput(BaseModel):
    age: int
    bmi: float
    hba1c: Optional[float] = None
    pregnant: bool
    gender: str
    clinical_context: str
