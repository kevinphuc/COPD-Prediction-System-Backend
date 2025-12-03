import gc  # <--- [QUAN TRỌNG] Thư viện dọn rác bộ nhớ
import io
import traceback

import librosa

# Matplotlib Backend configuration
import matplotlib
import numpy as np
import tensorflow as tf  # Vẫn import tf nhưng sẽ dùng bản Lite

matplotlib.use("Agg")
from typing import Any, Dict, List, Tuple
from uuid import UUID

from fastapi import HTTPException
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlmodel import Session

from app.crud import crud_health
from app.db.supabase import supabase_service_client

# --- CẤU HÌNH LOAD MODEL TFLITE (SIÊU NHẸ) ---
INTERPRETER = None
INPUT_DETAILS = None
OUTPUT_DETAILS = None

try:
    # Lưu ý: Bạn cần push file .tflite lên Render
    tflite_path = "copd_model.tflite"

    # Chỉ load Interpreter thay vì toàn bộ Keras
    INTERPRETER = tf.lite.Interpreter(model_path=tflite_path)
    INTERPRETER.allocate_tensors()

    INPUT_DETAILS = INTERPRETER.get_input_details()
    OUTPUT_DETAILS = INTERPRETER.get_output_details()

    print("HealthService: Đã tải TFLite Model thành công (RAM Optimized).")

except Exception as e:
    print(f"HealthService Warning: Lỗi tải TFLite Model. {e}")
    print("Hãy chắc chắn bạn đã chạy script convert và upload file .tflite")


class HealthService:
    def __init__(self):
        self.storage = supabase_service_client.storage
        self.CLASSES = ["Both", "Crackles", "Normal", "Wheezes"]
        self.MAX_PAD_LEN = 862

    def _preprocess_audio_segment(
        self, audio_segment: np.ndarray, sr: int | float
    ) -> np.ndarray:
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
        # Dùng Figure() object để an toàn Thread-safe
        try:
            with io.BytesIO(audio_file_bytes) as f:
                y, sr = librosa.load(f, sr=16000)

            S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
            S_db = librosa.power_to_db(S, ref=np.max)

            # Tạo Figure, set dpi thấp chút để tiết kiệm RAM vẽ ảnh
            fig = Figure(figsize=(5, 4), dpi=100)
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)

            img = librosa.display.specshow(
                S_db, sr=sr, x_axis="time", y_axis="mel", ax=ax
            )
            ax.axis("off")

            img_buffer = io.BytesIO()
            canvas.print_png(img_buffer)

            # Đóng figure ngay lập tức để giải phóng RAM Matplotlib
            plt_data = img_buffer.getvalue()
            img_buffer.close()
            fig.clf()  # Clear figure

            # Force delete variables
            del S, S_db, y, img, canvas, ax, fig

            dimensions = {"width": 500, "height": 400}
            file_size = len(plt_data)

            return plt_data, dimensions, file_size

        except Exception as e:
            traceback.print_exc()
            raise Exception(f"Lỗi tạo Spectrogram: {str(e)}")

    def _run_prediction_model(self, audio_bytes: bytes) -> float:
        if INTERPRETER is None:
            print("Model TFLite chưa load, trả về random.")
            return float(np.random.rand())

        y = None
        try:
            with io.BytesIO(audio_bytes) as f:
                y, sr = librosa.load(f, sr=16000)

            cycle_duration = 5
            step = int(cycle_duration * sr)
            predictions = []

            for start in range(0, len(y), step):
                end = start + step
                segment = y[start:end]

                if len(segment) < sr:
                    continue

                input_tensor = self._preprocess_audio_segment(segment, sr)

                # --- LOGIC TFLITE THAY THẾ CHO KERAS ---
                # Set input tensor (Cần ép kiểu về float32)
                INTERPRETER.set_tensor(
                    INPUT_DETAILS[0]["index"], input_tensor.astype(np.float32)
                )

                # Chạy mô hình
                INTERPRETER.invoke()

                # Lấy kết quả
                pred_prob = INTERPRETER.get_tensor(OUTPUT_DETAILS[0]["index"])
                # ----------------------------------------

                pred_class_idx = np.argmax(pred_prob)
                pred_label = self.CLASSES[pred_class_idx]
                predictions.append(pred_label)

            print(f"Prediction segments: {predictions}")

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
            print(f"Lỗi dự đoán TFLite: {e}")
            traceback.print_exc()
            return 0.0
        finally:
            # Xóa biến y lớn
            if y is not None:
                del y

    def upload_new_health_data(
        self,
        session: Session,
        user_id: UUID,
        audio_bytes: bytes,
        audio_filename: str | None,
    ):
        db_input = None
        png_bytes = None

        try:
            # 1. Tạo record input
            db_input = crud_health.create_health_input(session, user_id=user_id)
            input_id = db_input.input_id

            # 2. Xử lý ảnh (Tách thành hàm riêng để biến cục bộ được giải phóng sau khi return)
            png_bytes, dims, size = self._generate_spectrogram_image(audio_bytes)

            # 3. Upload Storage
            storage_path = f"public/{user_id}/{input_id}.png"

            # Retry logic cho Storage
            try:
                self.storage.from_("spectrogram").upload(
                    path=storage_path,
                    file=png_bytes,
                    file_options={"content-type": "image/png", "upsert": "true"},
                )
            except Exception as upload_err:
                print("Upload failed, retrying once...", upload_err)
                self.storage.from_("spectrogram").upload(
                    path=storage_path,
                    file=png_bytes,
                    file_options={"content-type": "image/png", "upsert": "true"},
                )

            public_url = self.storage.from_("spectrogram").get_public_url(storage_path)

            # 4. Lưu DB Spectrogram
            crud_health.create_spectrogram(session, input_id, public_url, dims, size)

            # 5. Chạy Model (Dùng TFLite)
            risk_score = self._run_prediction_model(audio_bytes)

            # 6. Lưu kết quả
            crud_health.create_prediction(session, input_id, risk_score)

            return {
                "message": "Tải lên thành công",
                "input_id": input_id,
                "risk_score": risk_score,
            }

        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            traceback.print_exc()

            if db_input:
                try:
                    session.delete(db_input)
                    session.commit()
                except:
                    pass

            raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

        finally:
            # --- [QUAN TRỌNG] DỌN RÁC BỘ NHỚ ---
            # Xóa các biến chứa dữ liệu lớn
            try:
                del audio_bytes
                if png_bytes:
                    del png_bytes
            except:
                pass

            # Ép Python chạy Garbage Collector ngay lập tức
            # Giúp RAM giảm xuống ngay sau khi request kết thúc
            gc.collect()


health_service = HealthService()
