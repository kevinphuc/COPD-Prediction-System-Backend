from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

class PostResponse(BaseModel):
    id: int
    title: str
    content: str

class PostListResponse(BaseModel):
    posts: list[PostResponse]

router = APIRouter()

@router.get("/", response_model=PostListResponse)
async def get_posts():
    return {
        "posts": [
            {"id": 1, "title": "First Post", "content": "Content here"},
            {"id": 2, "title": "Second Post", "content": "More content"}
        ]
    }

@router.post("/", response_model=PostResponse)
async def create_post():
    return {"id": 1, "title": "New Post", "content": "New content"}