# COPD-Prediction-System-Backend
## Đồ án Tốt nghiệp: Health Prediction API (FastAPI + Supabase)

Đây là dự án backend FastAPI được thiết kế để hoạt động với cơ sở dữ liệu Supabase, sử dụng sqlmodel cho CSDL và supabase-py cho Auth/Storage.

Cấu trúc dự án

```
/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── api.py           # Tổng hợp router v1
│   │       └── endpoints/
│   │           ├── auth.py      # Endpoints cho login/register
│   │           └── health.py    # Endpoints cho upload, xem lịch sử
│   ├── core/
│   │   └── config.py        # Quản lý biến môi trường (Settings)
│   ├── crud/
│   │   ├── base.py          # CRUD Base (chưa dùng)
│   │   └── crud_health.py   # CRUD cho các models sức khỏe
│   ├── db/
│   │   └── supabase.py      # Khởi tạo Supabase clients và SQLModel engine
│   ├── dependencies/
│   │   ├── database.py      # Dependency get_session (SQLModel)
│   │   └── auth.py          # Dependency get_current_user
│   ├── models/
│   │   ├── base.py          # Base model cho Pydantic (schemas)
│   │   ├── health_input.py  # SQLModel cho health_input
│   │   ├── prediction_result.py # SQLModel cho prediction_result
│   │   ├── spectrogram.py   # SQLModel cho spectrogram
│   │   ├── spirometry.py    # SQLModel cho spirometry
│   │   └── users.py         # SQLModel cho users (public.users)
│   ├── services/
│   │   ├── health_service.py # Logic nghiệp vụ (tạo spectrogram, chạy model)
│   │   └── auth_service.py   # Logic nghiệp vụ (tác vụ auth)
│   ├── main.py                # File FastAPI chính
│   └── __init__.py
├── .env                       # File biến môi trường
└── requirements.txt           # Các thư viện Python
```

## Hướng dẫn cài đặt

1. Clone dự án

2. Tạo môi trường ảo và cài đặt thư viện

```python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. Tạo file `.env` và điền các thông tin sau:
```
# Từ Supabase Project > Settings > API
SUPABASE_URL="https"//your-project-id.supabase.co
SUPABASE_ANON_KEY="your-anon-public-key"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# Từ Supabase Project > Settings > Database > Connection string (URI)
# LƯU Ý: Thay [YOUR-PASSWORD] bằng mật khẩu CSDL của bạn
DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.your-project-id.supabase.co:5432/postgres"
```

4. Chạy server FastAPI
```
uvicorn app.main:app --reload
```

Server sẽ chạy tại `http://127.0.0.1:8000`. Bạn có thể xem tài liệu API tại `http://127.0.0.1:8000/docs`.

## LƯU Ý QUAN TRỌNG VỀ SCHEMA (NHẮC LẠI)

Mã này được viết dựa trên giả định bạn đã làm theo các khuyến nghị sau:

Bảng users: Đã XÓA cột password khỏi public.users và đã tạo Trigger handle_new_user (xem README cũ) để đồng bộ user từ auth.users sang public.users.

Bảng spectrogram: Đã THAY ĐỔI cột spectrogram_data bytea thành spectrogram_url text. Chúng ta sẽ lưu ảnh PNG vào Supabase Storage và lưu URL vào cột này.