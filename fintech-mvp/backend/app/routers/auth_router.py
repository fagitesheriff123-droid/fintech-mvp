from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db
from ..deps import get_current_user
from ..rate_limit import rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])

MIN_PASSWORD_LENGTH = 8


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
    db.commit()
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
