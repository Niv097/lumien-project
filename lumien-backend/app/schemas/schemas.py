from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from ..models.models import CaseStatus

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class Role(RoleBase):
    id: int
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    roles: List[Role] = []
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    roles: List[str]
    user: str

class TokenData(BaseModel):
    username: Optional[str] = None
    roles: List[str] = []
    bank_id: Optional[int] = None
    branch_id: Optional[int] = None

class BankBase(BaseModel):
    name: str
    code: str
    ifsc_prefix: str
    integration_model: str
    sla_hours: int

class Bank(BankBase):
    id: int
    is_active: bool
    class Config:
        from_attributes = True

class ComplaintBase(BaseModel):
    complaint_id: str
    victim_name: str
    victim_mobile: Optional[str] = None
    incident_date: datetime
    fraud_type: str
    amount: float

class Complaint(ComplaintBase):
    id: int
    status: CaseStatus
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
