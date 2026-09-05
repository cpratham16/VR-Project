import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class ScreeningInstrument(Base):
    __tablename__ = "screening_instruments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)  # e.g. "PHQ-9", "GAD-7"
    title = Column(String, nullable=False)
    instructions = Column(String, nullable=False)
    options = Column(JSON, nullable=False)  # list of option labels ["Not at all", ...]
    questions = Column(JSON, nullable=False)  # list of {"id": int, "text": str}
    scoring_bands = Column(JSON, nullable=False)  # list of {"max_score": int, "label": str}, ascending
    answer_min = Column(Integer, nullable=False, default=0)
    answer_max = Column(Integer, nullable=False, default=3)
    critical_items = Column(JSON, nullable=True)  # list of question ids that flag risk when > 0 (e.g. PHQ-9 item 9)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_questionnaire_definition(self):
        from app.schemas.screening import QuestionnaireDefinition
        return QuestionnaireDefinition(
            screening_type=self.code,
            title=self.title,
            instructions=self.instructions,
            options=self.options,
            questions=self.questions,
        )
