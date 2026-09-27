"""
Phase 5 — mounted separately from the core app on purpose (see main.py).
Every response is self-labeled as sandbox/experimental so nothing here
can be mistaken for a real balance, a real prediction, or real advice.
"""
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from ..deps import get_current_user
from ..services import experimental

router = APIRouter(prefix="/experimental", tags=["experimental — Phase 5"])


class AskRequest(BaseModel):
    question: str


@router.get("/sandbox-link")
def sandbox_link(user=Depends(get_current_user)):
    return experimental.sandbox_linked_accounts()


@router.get("/market-trend")
def market_trend(symbol: str = "DEMO", user=Depends(get_current_user)):
    return experimental.experimental_market_trend(symbol)


@router.post("/ask")
def ask(
    body: AskRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    rows = db.query(models.Transaction).filter(models.Transaction.user_id == user.id).all()
    txns = [{"amount": t.amount, "category": t.category} for t in rows]
    return experimental.ask_about_spending(txns, body.question)
