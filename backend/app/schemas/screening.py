from typing import List, Literal
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

ScreeningType = Literal["PHQ-9", "GAD-7"]

class QuestionItem(BaseModel):
    id: int
    text: str

class QuestionnaireDefinition(BaseModel):
    screening_type: ScreeningType
    title: str
    instructions: str
    options: List[str]
    questions: List[QuestionItem]

class ScreeningSubmission(BaseModel):
    screening_type: ScreeningType
    answers: List[int] = Field(..., description="Array of score integers (0-3) for each question")

class ScreeningResponse(BaseModel):
    id: UUID
    user_id: UUID
    screening_type: ScreeningType
    answers: List[int]
    total_score: int
    severity_band: str
    created_at: datetime

    class Config:
        from_attributes = True

def calculate_phq9_severity(score: int) -> str:
    if score <= 4:
        return "Minimal"
    elif score <= 9:
        return "Mild"
    elif score <= 14:
        return "Moderate"
    elif score <= 19:
        return "Moderately Severe"
    else:
        return "Severe"

def calculate_gad7_severity(score: int) -> str:
    if score <= 4:
        return "Minimal"
    elif score <= 9:
        return "Mild"
    elif score <= 14:
        return "Moderate"
    else:
        return "Severe"
