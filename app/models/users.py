from sqlmodel import SQLModel, Field, Column
from pydantic import EmailStr
from uuid import UUID, uuid4
from datetime import datetime, timezone

class Users(SQLModel, table=True):
    """
    Model cho bảng public.users
    LƯU Ý: KHÔNG có cột password
    """
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(sa_column=Column("username", unique=True, nullable=False))
    email: EmailStr = Field(sa_column=Column("email", unique=True, nullable=False))
    phone_number: str | None = Field(default=None)
    inserted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
