from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from ..deps import get_current_user
from ..services import analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _user_txns(db: Session, user_id: int) -> list[dict]:
    rows = (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == user_id)
        .all()
    )
    return [
        {
            "id": t.id,
            "date": t.date.isoformat(),
            "description": t.description,
            "amount": t.amount,
            "category": t.category,
        }
        for t in rows
    ]


@router.get("/forecast")
def forecast(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return analytics.forecast_next_month(_user_txns(db, user.id))


@router.get("/anomalies")
def anomalies(db: Session = Depends(get_db), user=Depends(get_current_user)):
    flags = analytics.detect_anomalies(_user_txns(db, user.id))
    # persist the flag so it shows up on the transaction itself too
    flagged_ids = {f["transaction_id"] for f in flags}
    if flagged_ids:
        db.query(models.Transaction).filter(
            models.Transaction.id.in_(flagged_ids)
        ).update({"is_anomaly": 1}, synchronize_session=False)
        db.commit()
    return flags


@router.get("/health-score")
def score(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return analytics.health_score(_user_txns(db, user.id))
