from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ....core.database import get_db_manager
from ....models.domain.entities import User
from ....models.schemas.request_schemas import CreateUserRequest, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
    summary="Create user",
    description="Create a new user"
)
def create_user(request: CreateUserRequest):
    db_manager = get_db_manager()
    
    try:
        with db_manager.get_session() as db:
            # Check if username exists
            existing = db.query(User).filter(User.username == request.username).first()
            if existing:
                raise HTTPException(status_code=400, detail="Username already exists")
            
            # Check if email exists
            if request.email:
                existing_email = db.query(User).filter(User.email == request.email).first()
                if existing_email:
                    raise HTTPException(status_code=400, detail="Email already exists")
            
            # Create user
            user = User(
                username=request.username,
                email=request.email
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return UserResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.get(
    "",
    response_model=List[UserResponse],
    summary="List users",
    description="Get list of all users"
)
def list_users():
    db_manager = get_db_manager()
    
    try:
        with db_manager.get_session() as db:
            users = db.query(User).order_by(User.created_at.desc()).all()
            return [UserResponse.model_validate(user) for user in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user",
    description="Get user by ID"
)
def get_user(user_id: str):
    db_manager = get_db_manager()
    
    try:
        with db_manager.get_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return UserResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")

