from datetime import date
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class TransactionOut(BaseModel):
    id: int
    date: date
    description: str
    amount: float
    category: str | None

    class Config:
        from_attributes = True


class GoalCreate(BaseModel):
    name: str
    target_amount: float
    target_date: date


class GoalOut(GoalCreate):
    id: int

    class Config:
        from_attributes = True


class DebtCreate(BaseModel):
    name: str
    balance: float
    interest_rate: float
    min_payment: float


class DebtOut(DebtCreate):
    id: int

    class Config:
        from_attributes = True
