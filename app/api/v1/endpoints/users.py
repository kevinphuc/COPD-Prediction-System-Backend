from typing import List
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status, Query

import uuid

from app.models.users import Users
from app.services.users import UserService

app = FastAPI()
router = APIRouter()

@app.get("/", response_model=List[Users])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_service: UserService = Depends()
):
    return await user_service.get_all(skip=skip, limit=limit)

@router.get("/{user_id}", response_model=Users)
async def get_user(
    user_id: uuid.UUID,
    user_service: UserService = Depends()
):
    return await user_service.get_by_id(user_id)

@router.post("/", response_model=Users, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: Users,
    user_service: UserService = Depends()
):
    return await user_service.create(user)

@router.put("/{user_id}", response_model=Users)
async def update_user(
    user_id: uuid.UUID,
    user: Users,
    user_service: UserService = Depends()
):
    return await user_service.update(user_id, user)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    user_service: UserService = Depends()
):
    success = await user_service.delete(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )