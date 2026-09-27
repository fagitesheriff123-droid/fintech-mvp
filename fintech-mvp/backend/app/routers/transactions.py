from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..services.parser import parse_csv, parse_pdf
from ..deps import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB — a CSV statement has no business being bigger


@router.post("/upload", response_model=List[schemas.TransactionOut])
async def upload_statement(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    filename = file.filename.lower()
    if not (filename.endswith(".csv") or filename.endswith(".pdf")):
        raise HTTPException(status_code=400, detail="Only CSV or PDF statements are supported")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large — max 5MB")

    try:
        rows = parse_pdf(contents) if filename.endswith(".pdf") else parse_csv(contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    saved = []
    for row in rows:
        txn = models.Transaction(user_id=current_user.id, **row)
        db.add(txn)
        saved.append(txn)
    db.commit()
    for txn in saved:
        db.refresh(txn)
    return saved


@router.get("/", response_model=List[schemas.TransactionOut])
def list_transactions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == current_user.id)
        .order_by(models.Transaction.date.desc())
        .all()
    )


@router.get("/export")
def export_my_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """NDPR data portability: everything this account holds, in one JSON blob."""
    txns = (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == current_user.id)
        .all()
    )
    goals = db.query(models.Goal).filter(models.Goal.user_id == current_user.id).all()
    debts = db.query(models.Debt).filter(models.Debt.user_id == current_user.id).all()
    return {
        "user_email": current_user.email,
        "transactions": [schemas.TransactionOut.model_validate(t).model_dump() for t in txns],
        "goals": [schemas.GoalOut.model_validate(g).model_dump() for g in goals],
        "debts": [schemas.DebtOut.model_validate(d).model_dump() for d in debts],
    }
