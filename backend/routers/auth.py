import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.models.password_reset import PasswordResetToken
from backend.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from backend.services.auth_service import hash_password, verify_password, create_access_token
from backend.services.email_service import send_password_reset_email
from backend.dependencies import get_current_user

router = APIRouter()


@router.get("/csrf-token")
def get_csrf_token():
    """Issue a CSRF token via cookie + JSON body (Double Submit Cookie pattern)."""
    token = secrets.token_urlsafe(32)
    response = JSONResponse(content={"csrf_token": token})
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,   # Must be readable by JS so axios can put it in the header
        samesite="strict",
        secure=False,     # Set to True in production (HTTPS only)
        max_age=3600,
    )
    return response


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password", status_code=200)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    # Always return 200 — never reveal whether the email exists
    if not user:
        return {"detail": "If that email is registered, a reset link has been sent."}

    # Invalidate any existing unused tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False,
    ).delete()
    db.commit()

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db.add(PasswordResetToken(user_id=user.id, token=token, expires_at=expires_at))
    db.commit()

    try:
        send_password_reset_email(user.email, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")

    return {"detail": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", status_code=200)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == body.token,
        PasswordResetToken.used == False,
    ).first()

    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset link has expired.")

    user = db.query(User).filter(User.id == record.user_id).first()
    user.hashed_password = hash_password(body.new_password)
    record.used = True
    db.commit()

    return {"detail": "Password updated. You can now sign in."}
