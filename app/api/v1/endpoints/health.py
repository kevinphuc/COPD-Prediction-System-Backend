from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Form, status
)
from sqlmodel import Session
from app.dependencies.database import get_session
from app.dependencies.auth import get_current_user_id
from app.models.base import HealthInputCreateSchema, SpirometrySchema, HealthInputDetailSchema
from app.services.health_service import health_service
from app.crud import crud_health
from uuid import UUID
import json
from typing import List

router = APIRouter()

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_health_data(
    # Dependencies
    session: Session = Depends(get_session),
    current_user_id: UUID = Depends(get_current_user_id),
    
    # Form data
    # spirometry_data_str: str = Form(..., description='Dữ liệu spirometry (JSON string)'),
    audio_file: UploadFile = File(..., description="File âm thanh (wav, mp3, ...)")
):
    """
    Endpoint chính: Nhận file âm thanh + dữ liệu spirometry.
    Sử dụng SQLModel Session và HealthService.
    """
    # try:
    #     spirometry_json = json.loads(spirometry_data_str)
    #     spirometry_data = SpirometrySchema.model_validate(spirometry_json)
    # except Exception:
    #     raise HTTPException(status_code=400, detail="Định dạng spirometry_data JSON không hợp lệ")

    audio_bytes = await audio_file.read()
    
    result = health_service.upload_new_health_data(
        session=session,
        user_id=current_user_id,    
        audio_bytes=audio_bytes,
        audio_filename=audio_file.filename
    )
    return result

@router.get("/history", response_model=List[HealthInputDetailSchema])
async def get_user_health_history(
    session: Session = Depends(get_session),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Lấy lịch sử các lần upload của user hiện tại (từ SQLModel)."""
    db_results = crud_health.get_health_inputs_by_user(
        session, user_id=current_user_id
    )
    return db_results

@router.get("/details/{input_id}", response_model=HealthInputDetailSchema)
async def get_health_data_details(
    input_id: UUID,
    session: Session = Depends(get_session),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Lấy chi tiết một lần upload (từ SQLModel)."""
    db_result = crud_health.get_health_input_details(
        session, input_id=input_id, user_id=current_user_id
    )
    if not db_result:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu hoặc không có quyền truy cập")
    return db_result
