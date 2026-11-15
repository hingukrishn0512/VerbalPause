from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.db.database import get_db
from backend.app.db.models import User
from backend.app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    current_streak: int
    longest_streak: int
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: UserResponse


@router.post("/register", response_model=AuthResponse)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Registers a new candidate account with hashed password and issuance of JWT token."""
    clean_email = payload.email.lower().strip()
    if len(payload.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )

    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    today_str = date.today().isoformat()
    new_user = User(
        email=clean_email,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        current_streak=1,
        longest_streak=1,
        last_active_date=today_str,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.email, "id": new_user.id})
    return {
        "token": token,
        "token_type": "bearer",
        "user": new_user
    }


@router.post("/login", response_model=AuthResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates credentials and returns a JWT access token."""
    clean_email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    # Check and update daily practice streak
    today_str = date.today().isoformat()
    if user.last_active_date != today_str:
        if user.last_active_date:
            try:
                last_date = datetime.strptime(user.last_active_date, "%Y-%m-%d").date()
                delta_days = (date.today() - last_date).days
                if delta_days == 1:
                    user.current_streak += 1
                elif delta_days > 1:
                    user.current_streak = 1
            except Exception:
                user.current_streak = 1
        else:
            user.current_streak = 1

        if user.current_streak > user.longest_streak:
            user.longest_streak = user.current_streak
        user.last_active_date = today_str
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": user.email, "id": user.id})
    return {
        "token": token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Fetches the authenticated user profile and streak metrics."""
    return current_user
