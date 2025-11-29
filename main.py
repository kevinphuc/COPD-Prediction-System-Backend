from fastapi import FastAPI
from app.api.v1.api import api_router_v1
from fastapi.middleware.cors import CORSMiddleware

import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Connect to the database
try:
    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )
    print("Connection successful!")
    
    # Create a cursor to execute SQL queries
    cursor = connection.cursor()
    
    # Example query
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print("Current Time:", result)

    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("Connection closed.")

except Exception as e:
    print(f"Failed to connect: {e}")

# Khởi tạo FastAPI app
app = FastAPI(
    title="Health Prediction API - Đồ án tốt nghiệp (SQLModel)",
    description="API sử dụng FastAPI, SQLModel và Supabase (Auth/Storage).",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn router v1
app.include_router(api_router_v1, prefix="/api/v1")

@app.get("/")
async def root():
    """Endpoint gốc chào mừng"""
    return {
        "message": "Chào mừng bạn đến với Health Prediction API v2 (SQLModel).",
        "docs_url": "/docs",
    }

