import io
import traceback  # <--- Thêm cái này để debug lỗi

import librosa

# Matplotlib Backend configuration
import matplotlib
import numpy as np
import tensorflow as tf

matplotlib.use("Agg")
from typing import Any, Dict, List, Tuple
from uuid import UUID

from fastapi import HTTPException
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlmodel import Session

from app.crud import crud_health
from app.db.supabase import supabase_service_client

# --- LOAD MODEL ---
MODEL = None
try:
    # Đảm bảo đường dẫn file .keras chính xác
    MODEL = tf.keras.models.load_model("copd_spectrogram_model.keras")
    print("HealthService: Đã tải Model thành công.")
except Exception as e:
    print(
        f"HealthService Warning: Không tìm thấy model hoặc lỗi version. Chi tiết: {e}"
    )


class HealthService:
    def __init__(self):
        self.storage = supabase_service_client.storage
        self.CLASSES = ["Both", "Crackles", "Normal", "Wheezes"]
        self.MAX_PAD_LEN = 862

    def _preprocess_audio_segment(
        self, audio_segment: np.ndarray, sr: int | float
    ) -> np.ndarray:
        # ... (Giữ nguyên logic cũ của bạn) ...
        melspec = librosa.feature.melspectrogram(
            y=audio_segment, sr=sr, n_mels=128, fmax=8000
        )
        melspec_db = librosa.power_to_db(melspec, ref=np.max)

        if melspec_db.shape[1] > self.MAX_PAD_LEN:
            melspec_db = melspec_db[:, : self.MAX_PAD_LEN]
        else:
            pad_width = self.MAX_PAD_LEN - melspec_db.shape[1]
            melspec_db = np.pad(melspec_db, ((0, 0), (0, pad_width)), mode="constant")

        melspec_db = melspec_db[..., np.newaxis]
        return np.expand_dims(melspec_db, axis=0)

    def _generate_spectrogram_image(
        self, audio_file_bytes: bytes
    ) -> Tuple[bytes, Dict[str, Any], int]:
        """
        SỬA ĐỔI QUAN TRỌNG: Không dùng plt.subplots() (Global state)
        Dùng Figure() object để an toàn trong môi trường Web Server (Thread-safe).
        """
        try:
            with io.BytesIO(audio_file_bytes) as f:
                y, sr = librosa.load(f, sr=16000)

            S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
            S_db = librosa.power_to_db(S, ref=np.max)

            # 1. Tạo Figure object trực tiếp
            fig = Figure(figsize=(5, 4), dpi=100)
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)

            # 2. Vẽ lên ax
            img = librosa.display.specshow(
                S_db, sr=sr, x_axis="time", y_axis="mel", ax=ax
            )
            ax.axis("off")  # Tắt trục tọa độ

            # 3. Lưu vào buffer
            img_buffer = io.BytesIO()
            canvas.print_png(img_buffer)  # Dùng canvas để in
            # Hoặc: fig.savefig(img_buffer, format="png", bbox_inches="tight", pad_inches=0)

            img_buffer.seek(0)
            png_bytes = img_buffer.read()

            # Kích thước
            dimensions = {"width": int(5 * 100), "height": int(4 * 100)}
            file_size = len(png_bytes)

            return png_bytes, dimensions, file_size

        except Exception as e:
            # In lỗi chi tiết ra terminal để debug
            traceback.print_exc()
            raise Exception(f"Lỗi tạo Spectrogram: {str(e)}")

    def _run_prediction_model(self, audio_bytes: bytes) -> float:
        if MODEL is None:
            print("Model is None. Returning random score.")
            return float(np.random.rand())

        try:
            with io.BytesIO(audio_bytes) as f:
                y, sr = librosa.load(f, sr=16000)

            cycle_duration = 5
            step = int(cycle_duration * sr)
            predictions = []

            for start in range(0, len(y), step):
                end = start + step
                segment = y[start:end]

                # Sửa logic: Nếu đoạn cuối < 1s thì bỏ qua, nhưng nếu < 5s mà > 1s thì vẫn nên pad để predict
                if len(segment) < sr:
                    continue

                # Quan trọng: Cần đảm bảo độ dài segment đủ để preprocessing không lỗi
                # (Hàm preprocessing của bạn đã có padding, nên đoạn này ổn)

                input_tensor = self._preprocess_audio_segment(segment, sr)

                # Check shape trước khi predict để tránh crash
                # print(f"Input shape: {input_tensor.shape}")

                pred_prob = MODEL.predict(input_tensor, verbose=0)
                pred_class_idx = np.argmax(pred_prob)
                pred_label = self.CLASSES[pred_class_idx]
                predictions.append(pred_label)

            print(f"Prediction results segments: {predictions}")

            # Logic tính điểm rủi ro (Giữ nguyên)
            if not predictions:
                return 0.0

            has_wheezes = "Wheezes" in predictions
            has_both = "Both" in predictions
            has_crackles = "Crackles" in predictions

            if has_both:
                risk_score = 0.95
            elif has_wheezes:
                risk_score = 0.85
            elif has_crackles:
                risk_score = 0.50
            else:
                risk_score = 0.10

            return float(risk_score)

        except Exception as e:
            print(f"Lỗi dự đoán Model: {e}")
            traceback.print_exc()  # <--- Quan trọng để debug
            return 0.0

    def upload_new_health_data(
        self,
        session: Session,
        user_id: UUID,
        audio_bytes: bytes,
        audio_filename: str | None,
    ):
        db_input = None  # Khởi tạo biến để tránh lỗi UnboundLocalError
        try:
            # 1. Tạo record input
            db_input = crud_health.create_health_input(session, user_id=user_id)
            input_id = db_input.input_id

            # 2. Xử lý ảnh
            png_bytes, dims, size = self._generate_spectrogram_image(audio_bytes)

            # 3. Upload Storage
            storage_path = f"public/{user_id}/{input_id}.png"

            # --- FIX CHO LỖI 544: Retry logic (Optional) ---
            # Đôi khi mạng lag, thử upload lại 1 lần nếu thất bại
            try:
                self.storage.from_("spectrogram").upload(
                    path=storage_path,
                    file=png_bytes,
                    file_options={"content-type": "image/png", "upsert": "true"},
                )
            except Exception as upload_err:
                print("Upload failed, retrying once...", upload_err)
                # Thử lại lần 2
                self.storage.from_("spectrogram").upload(
                    path=storage_path,
                    file=png_bytes,
                    file_options={"content-type": "image/png", "upsert": "true"},
                )
            # -----------------------------------------------

            public_url = self.storage.from_("spectrogram").get_public_url(storage_path)

            # 4. Lưu DB
            crud_health.create_spectrogram(session, input_id, public_url, dims, size)
            risk_score = self._run_prediction_model(audio_bytes)
            crud_health.create_prediction(session, input_id, risk_score)

            return {
                "message": "Tải lên thành công",
                "input_id": input_id,
                "risk_score": risk_score,
            }

        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            traceback.print_exc()

            # Chỉ xóa nếu db_input đã được tạo
            if db_input:
                try:
                    session.delete(db_input)
                    session.commit()
                except:
                    pass  # Bỏ qua lỗi khi rollback

            raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


health_service = HealthService()
