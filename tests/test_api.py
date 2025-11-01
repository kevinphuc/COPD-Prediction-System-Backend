from fastapi.testclient import TestClient
from main import app # Import app FastAPI chính của bạn

# Tạo một "client" giả lập để gọi API
client = TestClient(app)

def test_read_root():
    """Test xem trang chủ có hoạt động không"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Chào mừng bạn đến với Health Prediction API v2 (SQLModel).",
        "docs_url": "/docs",
    }

def test_register_invalid_email():
    """Test trường hợp đăng ký với email không hợp lệ (giống lỗi của bạn)"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com", # Email bị Supabase chặn
            "password": "password123",
            "username": "testuser"
        }
    )
    # Kiểm tra xem API có trả về lỗi 400 (Bad Request) không
    assert response.status_code == 400 
    # Kiểm tra xem nội dung lỗi có đúng không
    assert "is invalid" in response.json()["detail"]
    
def test_login_invalid_email():
     response = client.post(
         "/api/v1/auth/login",
         json={
             "email": "user@example.com", # Email bị Supabase chặn
             "password": "password123"
         }
     )
     
     # Kiểm tra xem API có trả về lỗi 400 (Bad Request) không
     assert response.status_code == 401 
     # Kiểm tra xem nội dung lỗi có đúng không
     assert "Email hoặc mật khẩu không đúng" in response.json()["detail"]