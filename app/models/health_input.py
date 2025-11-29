from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import TYPE_CHECKING

# Forward references để tránh lỗi import vòng
if TYPE_CHECKING:
    from .spirometry import Spirometry
    from .spectrogram import Spectrogram
    from .prediction_result import PredictionResult

class HealthInput(SQLModel, table=True):
    """Model cho bảng health_input"""
    __tablename__ = 'health_input'
    __table_args__ = {'schema': 'public'}

    input_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(index=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    
    # Định nghĩa relationships
    spirometry: "Spirometry" = Relationship(back_populates="health_input")
    spectrogram: "Spectrogram" = Relationship(back_populates="health_input")
    prediction_result: "PredictionResult" = Relationship(back_populates="health_input")
