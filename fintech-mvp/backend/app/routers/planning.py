from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..services import simulator

router = APIRouter(prefix="/planning", tags=["planning"])


def _user_txns(db: Session, user_id: int) -> list[dict]:
    rows = (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == user_id)
        .all()
    )
    return [
        {"date": t.date.isoformat(), "amount": t.amount, "category": t.category}
        for t in rows
    ]


# ---- Scenario simulator ----
@router.get("/simulate")
def simulate(
    extra_savings: float = 0,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return simulator.simulate_scenario(_user_txns(db, user.id), extra_savings)


# ---- Goals ----
@router.post("/goals", response_model=schemas.GoalOut)
def create_goal(goal: schemas.GoalCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    new_goal = models.Goal(user_id=user.id, **goal.dict())
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return new_goal


@router.get("/goals", response_model=list[schemas.GoalOut])
def get_goals(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Goal).filter(models.Goal.user_id == user.id).all()


@router.get("/goals/{goal_id}/projection")
def goal_projection(goal_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id, models.Goal.user_id == user.id
    ).first()
    if not goal:
        return {"error": "Goal not found"}
    return simulator.goal_projection(_user_txns(db, user.id), goal.target_amount, goal.target_date)


# ---- Debts ----
@router.post("/debts", response_model=schemas.DebtOut)
def create_debt(debt: schemas.DebtCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    new_debt = models.Debt(user_id=user.id, **debt.dict())
    db.add(new_debt)
    db.commit()
    db.refresh(new_debt)
    return new_debt


@router.get("/debts", response_model=list[schemas.DebtOut])
def get_debts(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Debt).filter(models.Debt.user_id == user.id).all()


@router.get("/debts/payoff-order")
def debt_payoff(strategy: str = "avalanche", db: Session = Depends(get_db), user=Depends(get_current_user)):
    debts = db.query(models.Debt).filter(models.Debt.user_id == user.id).all()
    debt_dicts = [
        {"name": d.name, "balance": d.balance, "interest_rate": d.interest_rate, "min_payment": d.min_payment}
        for d in debts
    ]
    return simulator.debt_payoff_order(debt_dicts, strategy)
