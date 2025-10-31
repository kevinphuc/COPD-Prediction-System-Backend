from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .health_input import HealthInput

class Spectrogram(SQLModel, table=True):
    """
    Model cho bảng spectrogram
    GIẢ ĐỊNH: cột spectrogram_data đã được đổi thành spectrogram_url (text)
    """
    __tablename__ = 'spectrogram'
    __table_args__ = {'schema': 'public'}

    spectrogram_id: UUID = Field(default_factory=uuid4, primary_key=True)
    input_id: UUID = Field(foreign_key="public.health_input.input_id", unique=True, nullable=False)
    
    # Đổi tên cột này từ spectrogram_data -> spectrogram_url
    spectrogram_url: str = Field(nullable=False) 
    
    file_format: str = Field(default="png", nullable=False)
    dimensions: Dict[str, Any] | None = Field(default={}, sa_column=Column(JSON))
    file_size: int = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    
    # Relationship
    health_input: "HealthInput" = Relationship(back_populates="spectrogram")
