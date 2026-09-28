from datetime import datetime, timezone
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db
from ..deps import get_current_user
from ..rate_limit import rate_limit
from ..services.email import send_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])

MIN_PASSWORD_LENGTH = 8
# Used to build the link the user clicks in the reset email; the deployed
# frontend URL by default, overridable via env for other environments.
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://ayo-fintech-mvp-frontend.onrender.com")


@router.post("/signup", response_model=schemas.UserOut, dependencies=[Depends(rate_limit("signup", 5, 60))])
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if len(user.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = models.User(
        email=user.email, hashed_password=auth.hash_password(user.password)
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        # Two signups for the same email landed at once (e.g. a double-click) and
        # both passed the check above before either committed. Treat it the same
        # as the normal "already registered" case instead of a 500.
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=schemas.Token, dependencies=[Depends(rate_limit("login", 10, 60))])
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_access_token({"sub": str(db_user.id)})
    return {"access_token": token}


@router.delete("/me", status_code=204)
def delete_my_account(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """NDPR right-to-erasure: deletes the user and all their transactions/goals/debts."""
    db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id).delete()
    db.query(models.Goal).filter(models.Goal.user_id == current_user.id).delete()
    db.query(models.Debt).filter(models.Debt.user_id == current_user.id).delete()
    db.delete(current_user)
    db.commit()


@router.post("/forgot-password", status_code=202, dependencies=[Depends(rate_limit("forgot_password", 5, 300))])
def forgot_password(req: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Always returns the same generic response whether or not the email is
    registered — replying differently would let someone probe which emails
    have accounts (user enumeration).
    """
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if user:
        token, token_hash, expires = auth.generate_reset_token()
        user.reset_token_hash = token_hash
        user.reset_token_expires = expires
        db.commit()
        reset_link = f"{FRONTEND_URL}/#/reset-password?token={token}"
        send_reset_email(user.email, reset_link)
    return {"detail": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(req: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    if len(req.new_password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters")

    token_hash = auth.hash_reset_token(req.token)
    user = db.query(models.User).filter(models.User.reset_token_hash == token_hash).first()

    now = datetime.now(timezone.utc)
    expired = user and (
        user.reset_token_expires.replace(tzinfo=timezone.utc)
        if user.reset_token_expires.tzinfo is None
        else user.reset_token_expires
    ) < now
    if not user or expired:
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired")

    user.hashed_password = auth.hash_password(req.new_password)
    user.reset_token_hash = None
    user.reset_token_expires = None
    db.commit()
    return {"detail": "Password has been reset. You can now log in."}
