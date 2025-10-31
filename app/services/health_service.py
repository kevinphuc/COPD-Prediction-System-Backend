import numpy as np
import librosa
import io
import matplotlib
matplotlib.use('Agg') # Dùng backend không cần GUI
import matplotlib.pyplot as plt
from typing import Tuple, Dict, Any
from app.db.supabase import supabase_service_client # Dùng service client để upload
from sqlmodel import Session
from uuid import UUID
from app.crud import crud_health
from fastapi import HTTPException

class HealthService:
    
    def __init__(self):
        self.storage = supabase_service_client.storage

    def _run_prediction_model(
        self, 
        spirometry_data: Dict[str, Any], 
        spectrogram_data: np.ndarray
    ) -> float:
        """
        HÀM PLACEHOLDER (CHỜ THAY THẾ)
        Bạn cần thay thế logic này bằng model ML thật của mình.
        """
        print(f"Đang chạy model dự đoán với FEV1: {spirometry_data.get('fev1')}")
        print(f"Dữ liệu spectrogram shape: {spectrogram_data.shape}")
        
        # === LOGIC MODEL THẬT CỦA BẠN SẼ Ở ĐÂY ===
        risk_score = np.random.rand() # Trả về một số ngẫu nhiên từ 0 đến 1
        
        return float(risk_score)

    def _generate_spectrogram_image(
        self, 
        audio_file_bytes: bytes
    ) -> Tuple[bytes, Dict[str, Any], int, np.ndarray]:
        """Tạo ảnh spectrogram từ file âm thanh."""
        try:
            with io.BytesIO(audio_file_bytes) as f:
                y, sr = librosa.load(f, sr=None)
            
            S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
            S_db = librosa.power_to_db(S, ref=np.max)
            
            fig, ax = plt.subplots()
            librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='mel', ax=ax)
            ax.axis('off')
            fig.set_size_inches(5, 4)
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', pad_inches=0)
            plt.close(fig)
            
            img_buffer.seek(0)
            png_bytes = img_buffer.read()
            
            dimensions = {"width": int(5 * fig.dpi), "height": int(4 * fig.dpi)}
            file_size = len(png_bytes)
            
            return png_bytes, dimensions, file_size, S_db
            
        except Exception as e:
            print(f"Lỗi khi tạo spectrogram: {e}")
            raise HTTPException(status_code=500, detail=f"Lỗi xử lý audio: {e}")

    def upload_new_health_data(
        self,
        session: Session,
        user_id: UUID,
        spirometry_data: Dict[str, Any],
        audio_bytes: bytes,
        audio_filename: str # Tên file gốc
    ):
        """
        Logic chính cho việc upload:
        1. Tạo spectrogram
        2. Tạo entry trong DB
        3. Upload ảnh lên Storage
        4. Chạy model
        5. Cập nhật DB
        """
        
        # 1. Tạo health_input rỗng
        db_input = crud_health.create_health_input(session, user_id=user_id)
        input_id = db_input.input_id
        
        try:
            # 2. Tạo spectrogram
            png_bytes, dims, size, raw_spectrogram_data = self._generate_spectrogram_image(
                audio_bytes
            )
            
            # 3. Lưu spirometry
            fev1 = spirometry_data.get("fev1")
            fvc = spirometry_data.get("fvc")
            crud_health.create_spirometry(session, input_id, fev1, fvc)
            
            # 4. Upload ảnh lên Supabase Storage
            storage_path = f"public/{user_id}/{input_id}.png"
            
            self.storage.from_("spectrograms").upload( # Tên bucket
                path=storage_path,
                file=png_bytes,
                file_options={"content-type": "image/png", "upsert": "true"}
            )
            
            public_url = self.storage.from_("spectrograms").get_public_url(storage_path)
            
            # 5. Lưu metadata (URL) vào CSDL
            crud_health.create_spectrogram(session, input_id, public_url, dims, size)
            
            # 6. Chạy model dự đoán
            risk_score = self._run_prediction_model(spirometry_data, raw_spectrogram_data)
            
            # 7. Lưu kết quả dự đoán vào CSDL
            crud_health.create_prediction(session, input_id, risk_score)
            
            return {"message": "Tải lên thành công", "input_id": input_id, "risk_score": risk_score}

        except Exception as e:
            # Xử lý lỗi: Nếu có lỗi, xóa bản ghi health_input đã tạo
            # SQLModel sẽ tự rollback session khi có lỗi NẾU session được
            # quản lý bởi dependency, nhưng vì ta commit thủ công, ta nên rollback
            # Tuy nhiên, cách đơn giản là để FastAPI exception handler xử lý
            # và session tự rollback
            print(f"Lỗi trong quá trình upload: {e}")
            # Xóa entry rỗng đã tạo
            session.delete(db_input)
            session.commit()
            raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý file: {e}")

health_service = HealthService()
