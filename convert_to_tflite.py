import tensorflow as tf
import os

# Tên file model cũ và mới
KERAS_MODEL_PATH = "copd_spectrogram_model.keras"
TFLITE_MODEL_PATH = "copd_model.tflite"

def convert():
    if not os.path.exists(KERAS_MODEL_PATH):
        print(f"Lỗi: Không tìm thấy file {KERAS_MODEL_PATH}")
        return

    print("Đang load model Keras... (Sẽ tốn chút thời gian)")
    try:
        model = tf.keras.models.load_model(KERAS_MODEL_PATH)
        
        # Convert sang TFLite
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        
        # Tối ưu hóa: Giảm kích thước và RAM khi chạy
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        tflite_model = converter.convert()

        # Lưu file
        with open(TFLITE_MODEL_PATH, "wb") as f:
            f.write(tflite_model)
            
        print(f"✅ Đã convert thành công! File mới: {TFLITE_MODEL_PATH}")
        print("👉 Hãy upload file .tflite này lên GitHub thay vì file .keras")
        
    except Exception as e:
        print(f"❌ Lỗi khi convert: {e}")

if __name__ == "__main__":
    convert()