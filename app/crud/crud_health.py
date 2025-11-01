from sqlmodel import Session, select
from uuid import UUID
from app.models.health_input import HealthInput
from app.models.spirometry import Spirometry
from app.models.spectrogram import Spectrogram
from app.models.prediction_result import PredictionResult
from typing import List, Dict, Any

def create_health_input(session: Session, user_id: UUID) -> HealthInput:
    """Tạo health_input mới"""
    db_input = HealthInput(user_id=user_id)
    session.add(db_input)
    session.commit()
    session.refresh(db_input)
    return db_input

def create_spirometry(session: Session, input_id: UUID, fev1: float, fvc: float) -> Spirometry:
    """Tạo spirometry record"""
    db_spirometry = Spirometry(input_id=input_id, fev1=fev1, fvc=fvc)
    session.add(db_spirometry)
    session.commit()
    session.refresh(db_spirometry)
    return db_spirometry

def create_spectrogram(
    session: Session, 
    input_id: UUID, 
    url: str, 
    dims: Dict[str, Any], 
    size: int
) -> Spectrogram:
    """Lưu metadata của spectrogram (URL từ Storage)"""
    db_spectrogram = Spectrogram(
        input_id=input_id,
        spectrogram_url=url,
        dimensions=dims,
        file_size=size,
        file_format="png"
    )
    session.add(db_spectrogram)
    session.commit()
    session.refresh(db_spectrogram)
    return db_spectrogram

def create_prediction(
    session: Session, 
    input_id: UUID, 
    risk_score: float
) -> PredictionResult:
    """Lưu kết quả dự đoán"""
    db_prediction = PredictionResult(input_id=input_id, risk_score=risk_score)
    session.add(db_prediction)
    session.commit()
    session.refresh(db_prediction)
    return db_prediction

def get_health_inputs_by_user(session: Session, user_id: UUID) -> List[HealthInput]:
    """Lấy lịch sử của user, load kèm các data liên quan"""
    statement = select(HealthInput).where(HealthInput.user_id == user_id)
    results = session.exec(statement).all()
    # results sẽ tự động lazy-load hoặc eager-load (tùy config)
    # Để đảm bảo data có đủ, ta truy cập thủ công (hơi xấu nhưng hiệu quả)
    for res in results:
        _ = res.spirometry
        _ = res.spectrogram
        _ = res.prediction_result
    return results

def get_health_input_details(
    session: Session, 
    input_id: UUID, 
    user_id: UUID
) -> HealthInput | None:
    """Lấy chi tiết 1 record, đảm bảo đúng user"""
    statement = select(HealthInput).where(
        HealthInput.input_id == input_id,
        HealthInput.user_id == user_id
    )
    result = session.exec(statement).first()
    if result:
        _ = result.spirometry
        _ = result.spectrogram
        _ = result.prediction_result
    return result
