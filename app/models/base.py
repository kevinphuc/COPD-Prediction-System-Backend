from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Any

class BaseSchema(BaseModel):
    """Base Pydantic schema cho request/response. KHÔNG PHẢI SQLModel."""
    model_config: Any = ConfigDict(from_attributes=True)

class UserCreateSchema(BaseSchema):
    email: EmailStr
    password: str
    username: str
    phone_number: str | None = None

class UserLoginSchema(BaseSchema):
    email: EmailStr
    password: str

class TokenResponseSchema(BaseSchema):
    access_token: str
    token_type: str
    user_id: UUID

class SpirometrySchema(BaseSchema):
    fev1: float
    fvc: float

class HealthInputCreateSchema(BaseSchema):
    spirometry: SpirometrySchema

class PredictionResultSchema(BaseSchema):
    result_id: UUID
    input_id: UUID
    risk_score: float
    created_at: datetime

class SpectrogramSchema(BaseSchema):
    spectrogram_id: UUID
    input_id: UUID
    spectrogram_url: str
    file_format: str
    dimensions: dict[str, int]
    file_size: int
    created_at: datetime

class HealthInputDetailSchema(BaseSchema):
    """Schema trả về chi tiết 1 lần upload"""
    input_id: UUID
    user_id: UUID
    created_at: datetime
    spirometry: SpirometrySchema | None
    prediction_result: PredictionResultSchema | None
    spectrogram: SpectrogramSchema | None
