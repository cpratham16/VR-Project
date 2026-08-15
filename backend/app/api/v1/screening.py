from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.screening import ScreeningResult
from app.api.deps import get_current_user
from app.schemas.screening import (
    ScreeningType,
    QuestionnaireDefinition,
    ScreeningSubmission,
    ScreeningResponse,
    calculate_phq9_severity,
    calculate_gad7_severity
)

router = APIRouter()

PHQ9_QUESTIONS = QuestionnaireDefinition(
    screening_type="PHQ-9",
    title="PHQ-9 (Patient Health Questionnaire-9)",
    instructions="Over the last 2 weeks, how often have you been bothered by any of the following problems?",
    options=["Not at all", "Several days", "More than half the days", "Nearly every day"],
    questions=[
        {"id": 1, "text": "Little interest or pleasure in doing things"},
        {"id": 2, "text": "Feeling down, depressed, or hopeless"},
        {"id": 3, "text": "Trouble falling or staying asleep, or sleeping too much"},
        {"id": 4, "text": "Feeling tired or having little energy"},
        {"id": 5, "text": "Poor appetite or overeating"},
        {"id": 6, "text": "Feeling bad about yourself — or that you are a failure or have let yourself or your family down"},
        {"id": 7, "text": "Trouble concentrating on things, such as reading the newspaper or watching television"},
        {"id": 8, "text": "Moving or speaking so slowly that other people could have noticed? Or being fidgety/restless"},
        {"id": 9, "text": "Thoughts that you would be better off dead, or of hurting yourself in some way"}
    ]
)

GAD7_QUESTIONS = QuestionnaireDefinition(
    screening_type="GAD-7",
    title="GAD-7 (Generalized Anxiety Disorder-7)",
    instructions="Over the last 2 weeks, how often have you been bothered by the following problems?",
    options=["Not at all", "Several days", "More than half the days", "Nearly every day"],
    questions=[
        {"id": 1, "text": "Feeling nervous, anxious, or on edge"},
        {"id": 2, "text": "Not being able to stop or control worrying"},
        {"id": 3, "text": "Worrying too much about different things"},
        {"id": 4, "text": "Trouble relaxing"},
        {"id": 5, "text": "Being so restless that it is hard to sit still"},
        {"id": 6, "text": "Becoming easily annoyed or irritable"},
        {"id": 7, "text": "Feeling afraid as if something awful might happen"}
    ]
)

@router.get("/questions/{screening_type}", response_model=QuestionnaireDefinition)
async def get_questions(screening_type: str, current_user: User = Depends(get_current_user)):
    stype = screening_type.upper()
    if stype == "PHQ-9" or stype == "PHQ9":
        return PHQ9_QUESTIONS
    elif stype == "GAD-7" or stype == "GAD7":
        return GAD7_QUESTIONS
    else:
        raise HTTPException(status_code=400, detail="Invalid screening type. Choose PHQ-9 or GAD-7")

@router.post("/submit", response_model=ScreeningResponse)
async def submit_screening(
    submission: ScreeningSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expected_len = 9 if submission.screening_type == "PHQ-9" else 7
    if len(submission.answers) != expected_len:
        raise HTTPException(status_code=400, detail=f"Expected {expected_len} answers for {submission.screening_type}")
    
    if any(ans < 0 or ans > 3 for ans in submission.answers):
        raise HTTPException(status_code=400, detail="Answer scores must be between 0 and 3")

    total_score = sum(submission.answers)
    if submission.screening_type == "PHQ-9":
        severity = calculate_phq9_severity(total_score)
    else:
        severity = calculate_gad7_severity(total_score)

    result = ScreeningResult(
        user_id=current_user.id,
        screening_type=submission.screening_type,
        answers=submission.answers,
        total_score=total_score,
        severity_band=severity
    )
    db.add(result)
    await db.commit()
    await db.refresh(result)
    return result

@router.get("/history", response_model=List[ScreeningResponse])
async def get_screening_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = await db.execute(
        select(ScreeningResult)
        .where(ScreeningResult.user_id == current_user.id)
        .order_by(ScreeningResult.created_at.desc())
    )
    return query.scalars().all()
