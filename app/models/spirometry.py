from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .health_input import HealthInput

class Spirometry(SQLModel, table=True):
    """Model cho bảng spirometry"""
    __tablename__ = 'spirometry'
    __table_args__ = {'schema': 'public'}

    input_id: UUID = Field(foreign_key="public.health_input.input_id", primary_key=True)
    fev1: float | None = Field(default=None)
    fvc: float | None = Field(default=None)
    
    # Relationship
    health_input: "HealthInput" = Relationship(back_populates="spirometry")
