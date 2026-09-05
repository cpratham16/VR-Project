from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.screening import ScreeningResult
from app.models.screening_instrument import ScreeningInstrument
from app.models.alert import RiskAlert
from app.api.deps import get_current_user
from app.schemas.screening import (
    QuestionnaireDefinition,
    ScreeningSubmission,
    ScreeningResponse,
    calculate_phq9_severity,
    calculate_gad7_severity
)
from app.services.screening_engine import screening_engine_service

router = APIRouter()

# Legacy fallbacks — used only when an instrument is not yet seeded in the DB.
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

_LEGACY_DEFINITIONS = {
    "PHQ-9": PHQ9_QUESTIONS,
    "GAD-7": GAD7_QUESTIONS,
}

def _normalize_code(screening_type: str) -> str:
    code = screening_type.upper().strip()
    aliases = {"PHQ9": "PHQ-9", "GAD7": "GAD-7"}
    return aliases.get(code, code)

async def _load_instrument(db: AsyncSession, code: str) -> ScreeningInstrument:
    result = await db.execute(
        select(ScreeningInstrument).where(
            ScreeningInstrument.code == code,
            ScreeningInstrument.is_active == True  # noqa: E712
        )
    )
    return result.scalars().first()

@router.get("/questions/{screening_type}", response_model=QuestionnaireDefinition)
async def get_questions(
    screening_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    code = _normalize_code(screening_type)
    instrument = await _load_instrument(db, code)
    if instrument:
        return instrument.to_questionnaire_definition()
    if code in _LEGACY_DEFINITIONS:
        return _LEGACY_DEFINITIONS[code]
    raise HTTPException(status_code=400, detail=f"Invalid screening type: {code}")

@router.post("/submit", response_model=ScreeningResponse)
async def submit_screening(
    submission: ScreeningSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    code = _normalize_code(submission.screening_type)
    instrument = await _load_instrument(db, code)
    answers = submission.answers

    if instrument:
        try:
            screening_engine_service.validate_answers(answers, instrument)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        total_score, severity = screening_engine_service.score(answers, instrument)
        critical_hit = screening_engine_service.check_critical_items(answers, instrument)
    else:
        # Legacy path (instrument not seeded): preserve original behavior exactly
        if code not in ("PHQ-9", "GAD-7"):
            raise HTTPException(status_code=400, detail="Invalid screening type. Choose PHQ-9 or GAD-7")
        expected_len = 9 if code == "PHQ-9" else 7
        if len(answers) != expected_len:
            raise HTTPException(status_code=400, detail=f"Expected {expected_len} answers for {code}")
        if any(ans < 0 or ans > 3 for ans in answers):
            raise HTTPException(status_code=400, detail="Answer scores must be between 0 and 3")
        total_score = sum(answers)
        severity = calculate_phq9_severity(total_score) if code == "PHQ-9" else calculate_gad7_severity(total_score)
        critical_hit = code == "PHQ-9" and len(answers) >= 9 and answers[8] > 0

    # Trend detection vs previous result of same type (D2b)
    prev_query = await db.execute(
        select(ScreeningResult)
        .where(ScreeningResult.user_id == current_user.id, ScreeningResult.screening_type == code)
        .order_by(ScreeningResult.created_at.desc())
    )
    previous = prev_query.scalars().first()
    trend = None
    if previous is not None:
        trend = screening_engine_service.detect_trend(previous.total_score, total_score)

    # Safety alerts: critical item hit OR worsening trend into Moderate+ territory
    elevated_bands = ("Moderate", "Moderately Severe", "Severe")
    critical_alert = None
    if critical_hit:
        critical_alert = RiskAlert(
            user_id=current_user.id,
            severity="CRITICAL",
            trigger_source="screening_high",
            details=f"{code} critical item flagged (self-harm item > 0), total={total_score}, band={severity}"
        )
        db.add(critical_alert)
    elif trend == "worsened" and severity in elevated_bands:
        db.add(RiskAlert(
            user_id=current_user.id,
            severity="HIGH",
            trigger_source="screening_high",
            details=f"{code} worsening trend: {previous.total_score} ({previous.severity_band}) -> {total_score} ({severity})"
        ))

    result = ScreeningResult(
        user_id=current_user.id,
        screening_type=code,
        answers=answers,
        total_score=total_score,
        severity_band=severity
    )
    db.add(result)
    await db.commit()
    await db.refresh(result)

    # CRITICAL screening signal: SLA window + parallel crisis notifications (G6)
    if critical_alert is not None:
        from app.services.notification_service import (
            resolve_assigned_doctor, attach_sla, dispatch_critical_notifications,
        )
        critical_alert.assigned_doctor_id = await resolve_assigned_doctor(db, current_user)
        attach_sla(critical_alert)
        await db.commit()
        await db.refresh(critical_alert)
        await dispatch_critical_notifications(db, critical_alert, current_user)

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

@router.get("/trends/{screening_type}")
async def get_screening_trend(
    screening_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Patient-facing longitudinal trend view for one instrument."""
    code = _normalize_code(screening_type)
    query = await db.execute(
        select(ScreeningResult)
        .where(ScreeningResult.user_id == current_user.id, ScreeningResult.screening_type == code)
        .order_by(ScreeningResult.created_at.desc())
    )
    results = query.scalars().all()
    if not results:
        return {"screening_type": code, "trend": "no_data", "points": []}
    view = screening_engine_service.build_trend_series(list(results))
    view["screening_type"] = code
    return view

@router.get("/reminder")
async def get_screening_reminder(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Usage-based smart reminder: nudge re-screening based on recency and last severity."""
    latest_query = await db.execute(
        select(ScreeningResult)
        .where(ScreeningResult.user_id == current_user.id)
        .order_by(ScreeningResult.created_at.desc())
    )
    latest = latest_query.scalars().first()
    return screening_engine_service.compute_reminder(
        latest.created_at if latest else None,
        latest.severity_band if latest else None
    )
