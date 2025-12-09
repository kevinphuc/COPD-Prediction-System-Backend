import gc
import io
import traceback

import librosa
import matplotlib
import numpy as np
import tensorflow as tf

matplotlib.use("Agg")
from typing import Any, Dict, Tuple
from uuid import UUID

from fastapi import HTTPException

# Dùng backend Agg để không phụ thuộc vào GUI server
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from sqlmodel import Session

from app.crud import crud_health
from app.db.supabase import supabase_service_client

try:
    MODEL = tf.keras.models.load_model("copd_spectrogram_model.keras")
    print("HealthService: Đã tải Model thành công.")
except Exception as e:
    print(f"HealthService Warning: Lỗi tải TFLite Model. {e}")


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
        return np.expand_dims(melspec_db[..., np.newaxis], axis=0)

    def _generate_spectrogram_image(
        self, audio_file_bytes: bytes
    ) -> Tuple[bytes, Dict[str, Any], int]:
        try:
            with io.BytesIO(audio_file_bytes) as f:
                y, sr = librosa.load(f, sr=16000)

            S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
            S_db = librosa.power_to_db(S, ref=np.max)

            fig = Figure(figsize=(5, 4), dpi=100)
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)

            librosa.display.specshow(S_db, sr=sr, x_axis="time", y_axis="mel", ax=ax)
            ax.axis("off")

            img_buffer = io.BytesIO()
            canvas.print_png(img_buffer)

            plt_data = img_buffer.getvalue()
            # png_bytes = img_buffer.read()
            img_buffer.close()
            # fig.clf()  # Xóa figure

            # Xóa biến ngay lập tức
            # del S, S_db, y, fig, canvas, ax
            #
            # # Kích thước
            dimensions = {"width": 500, "height": 400}
            file_size = len(plt_data)

            return plt_data, dimensions, file_size

        except Exception as e:
            traceback.print_exc()
            raise Exception(f"Lỗi tạo Spectrogram: {str(e)}")

    def _run_prediction_model(self, audio_bytes: bytes) -> float:
        if MODEL is None:
            print("Model is None. Returning random score.")
            return 0.0
        # y = None
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

                # INTERPRETER.set_tensor(
                #     INPUT_DETAILS[0]["index"], input_tensor.astype(np.float32)
                # )
                # INTERPRETER.invoke()
                # pred_prob = INTERPRETER.get_tensor(OUTPUT_DETAILS[0]["index"])
                #
                pred_prob = MODEL.predict(input_tensor, verbose=0)
                pred_class_idx = np.argmax(pred_prob)
                pred_label = self.CLASSES[pred_class_idx]
                predictions.append(pred_label)

                predictions.append(self.CLASSES[np.argmax(pred_prob)])

            print(f"Prediction segments: {predictions}")
            if not predictions:
                return 0.0

            if "Both" in predictions:
                return 0.95
            elif "Wheezes" in predictions:
                return 0.85
            elif "Crackles" in predictions:
                return 0.50
            return 0.10

        except Exception as e:
            print(f"Lỗi dự đoán: {e}")
            traceback.print_exc()
            return 0.0

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
            db_input = crud_health.create_health_input(session, user_id=user_id)
            input_id = db_input.input_id

            # Tạo ảnh (Chỉ dùng 15s đầu)
            png_bytes, dims, size = self._generate_spectrogram_image(audio_bytes)

            storage_path = f"public/{user_id}/{input_id}.png"

            # Upload (Có retry)
            try:
                self.storage.from_("spectrogram").upload(
                    path=storage_path,
                    file=png_bytes,
                    file_options={"content-type": "image/png", "upsert": "true"},
                )
            except Exception:
                self.storage.from_("spectrogram").upload(
                    path=storage_path,
                    file=png_bytes,
                    file_options={"content-type": "image/png", "upsert": "true"},
                )
            # Kiểm tra xem res có trả về lỗi object không (Supabase py trả về dict hoặc raise)

            public_url = self.storage.from_("spectrogram").get_public_url(storage_path)
            # Bước 3: Update DB Spectrogram
            crud_health.create_spectrogram(session, input_id, public_url, dims, size)

            # Chạy model
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
            if db_input:
                try:
                    session.delete(db_input)
                    session.commit()
                except:
                    pass
            raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

        finally:
            # Dọn dẹp triệt để
            try:
                del audio_bytes
                if png_bytes:
                    del png_bytes
            except:
                pass
            gc.collect()  # Ép giải phóng RAM


health_service = HealthService()
