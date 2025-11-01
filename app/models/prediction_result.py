from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .health_input import HealthInput

class PredictionResult(SQLModel, table=True):
    """Model cho bảng prediction_result"""
    __tablename__ = 'prediction_result'
    __table_args__ = {'schema': 'public'}

    result_id: UUID = Field(default_factory=uuid4, primary_key=True)
    input_id: UUID = Field(foreign_key="public.health_input.input_id", unique=True, nullable=False)
    risk_score: float = Field(nullable=False) # Cần thêm CHECK constraint trong CSDL
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    
    # Relationship
    health_input: "HealthInput" = Relationship(back_populates="prediction_result")
