from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from sqlalchemy import func
from datetime import datetime, timedelta
import json
import uuid

from ..core import security
from ..core.config import settings
from ..models import models
from ..schemas import schemas
from ..models.models import get_db

router = APIRouter()


def _ensure_demo_operations_data(db: Session, user: models.User):
    if not user or not user.bank_id or not user.branch_id:
        return

    branch = db.query(models.Branch).filter(models.Branch.id == user.branch_id).first()
    if not branch or not branch.demo_access:
        return

    demo_cases = (
        db.query(models.Case)
        .filter(models.Case.source_type == models.SourceType.DEMO)
        .order_by(models.Case.created_at.desc())
        .limit(50)
        .all()
    )
    if not demo_cases:
        return

    now = datetime.utcnow()

    kyc_count = db.query(models.KYCPack).filter(models.KYCPack.bank_id == user.bank_id).count()
    lea_count = db.query(models.LEAResponse).filter(models.LEAResponse.bank_id == user.bank_id).count()
    grv_count = db.query(models.Grievance).filter(models.Grievance.bank_id == user.bank_id).count()
    rst_count = db.query(models.RestorationOrder).filter(models.RestorationOrder.bank_id == user.bank_id).count()
    rec_count = db.query(models.ReconciliationItem).filter(models.ReconciliationItem.bank_id == user.bank_id).count()

    target_kyc = 15
    target_lea = 20
    target_grv = 25
    target_rst = 10
    target_rec = 30

    # B2 behavior: derive many rows from the demo cases, but only generate once per bank
    if kyc_count < target_kyc:
        needed = min(target_kyc - kyc_count, len(demo_cases))
        for c in demo_cases[:needed]:
            db.add(
                models.KYCPack(
                    pack_id=f"KYC-{uuid.uuid4().hex[:8].upper()}",
                    case_id=c.case_id,
                    complaint_id=None,
                    bank_id=user.bank_id,
                    branch_id=user.branch_id,
                    version=1,
                    status="DRAFT" if (c.status and c.status.value != "CLOSED") else "SUBMITTED",
                    mandatory_fields=json.dumps({"case_id": c.case_id, "amount": c.amount, "source": "excel_demo"}),
                    attachments=json.dumps([]),
                    created_by=user.id,
                    created_at=now,
                    remarks="Derived from Excel demo case",
                )
            )

    if lea_count < target_lea:
        needed = min(target_lea - lea_count, len(demo_cases))
        for c in demo_cases[:needed]:
            # Use amount heuristic to mimic LEA involvement
            status_val = (c.status.value if c.status else "NEW")
            if c.amount is None:
                continue
            if c.amount < 500 and status_val != "CLOSED":
                continue
            db.add(
                models.LEAResponse(
                    request_id=f"LEA-{uuid.uuid4().hex[:8].upper()}",
                    case_id=c.case_id,
                    complaint_id=None,
                    bank_id=user.bank_id,
                    branch_id=user.branch_id,
                    io_name="IO Demo",
                    police_station=f"PS-{c.state or 'NA'}",
                    request_received_at=c.created_at or now,
                    request_attachment=None,
                    status="REGISTERED" if status_val != "CLOSED" else "ACKNOWLEDGED",
                    created_by=user.id,
                    created_at=now,
                    remarks="Derived from Excel demo case",
                )
            )

    if grv_count < target_grv:
        needed = min(target_grv - grv_count, len(demo_cases))
        for idx, c in enumerate(demo_cases[:needed]):
            # Create a spread of grievance types
            grv_type = "HOLD_REMOVAL" if idx % 3 == 0 else ("DELAY" if idx % 3 == 1 else "OTHER")
            db.add(
                models.Grievance(
                    grievance_id=f"GRV-{uuid.uuid4().hex[:8].upper()}",
                    case_id=c.case_id,
                    complaint_id=None,
                    bank_id=user.bank_id,
                    branch_id=user.branch_id,
                    grievance_type=grv_type,
                    escalation_stage=1 + (idx % 3),
                    info_furnished_note="Derived from Excel demo case",
                    status="OPEN" if idx % 4 != 0 else "ESCALATED",
                    opened_at=c.created_at or now,
                    created_by=user.id,
                    remarks="Derived from Excel demo case",
                )
            )

    if rst_count < target_rst:
        needed = min(target_rst - rst_count, len(demo_cases))
        for c in demo_cases[:needed]:
            # Restoration orders are usually later lifecycle; derive from any case for demo
            db.add(
                models.RestorationOrder(
                    order_id=f"RST-{uuid.uuid4().hex[:8].upper()}",
                    case_id=c.case_id,
                    complaint_id=None,
                    bank_id=user.bank_id,
                    branch_id=user.branch_id,
                    order_reference=f"ORDER-{c.case_id}",
                    court_authority="Demo Authority",
                    order_date=None,
                    order_document=None,
                    destination_account="XXXX-XXXX-1234",
                    beneficiary_name="Demo Beneficiary",
                    verification_details=json.dumps({"state": c.state, "district": c.district}),
                    amount=float(c.amount or 0.0),
                    status="REGISTERED",
                    created_at=now,
                    created_by=user.id,
                    remarks="Derived from Excel demo case",
                )
            )

    if rec_count < target_rec:
        needed = min(target_rec - rec_count, len(demo_cases))
        for idx, c in enumerate(demo_cases[:needed]):
            platform_val = float(c.amount or 0.0)
            # Deterministic mismatch for demo: +/- 5% or -100
            if platform_val <= 0:
                continue
            cbs_val = platform_val * (0.95 if idx % 2 == 0 else 1.05)
            mismatch = "AMOUNT_MISMATCH" if abs(platform_val - cbs_val) > 0.01 else "STATUS_MISMATCH"
            db.add(
                models.ReconciliationItem(
                    item_id=f"REC-{uuid.uuid4().hex[:8].upper()}",
                    case_id=c.case_id,
                    complaint_id=None,
                    bank_id=user.bank_id,
                    branch_id=user.branch_id,
                    mismatch_type=mismatch,
                    platform_value=str(round(platform_val, 2)),
                    cbs_value=str(round(cbs_val, 2)),
                    status="DETECTED",
                    detected_at=c.created_at or now,
                    created_at=now,
                    remarks="Derived from Excel demo case",
                )
            )

    db.commit()

# Pydantic models for registration
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "branch_user"  # admin, branch_user
    bank_id: Optional[int] = None
    branch_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    bank_id: Optional[int]
    branch_id: Optional[int]
    
    class Config:
        from_attributes = True

# Dependency to get DB session
def get_db():
    from ..main import engine
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.
    - Admin users can register users for any bank/branch
    - Bank users can only register for their own bank
    """
    # Check if username already exists
    existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate bank and branch exist
    if user_data.bank_id:
        bank = db.query(models.Bank).filter(models.Bank.id == user_data.bank_id).first()
        if not bank:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bank not found"
            )
    
    if user_data.branch_id:
        branch = db.query(models.Branch).filter(models.Branch.id == user_data.branch_id).first()
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Branch not found"
            )
        # Ensure branch belongs to the selected bank
        if user_data.bank_id and branch.bank_id != user_data.bank_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Branch does not belong to the selected bank"
            )
    
    # Create new user
    hashed_password = security.get_password_hash(user_data.password)
    
    # Get or create role
    role_name = user_data.role if user_data.role in ["admin", "branch_user"] else "branch_user"
    role = db.query(models.Role).filter(models.Role.name == role_name).first()
    if not role:
        role = models.Role(name=role_name, description=f"{role_name} role")
        db.add(role)
        db.flush()
    
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        bank_id=user_data.bank_id,
        branch_id=user_data.branch_id,
        roles=[role]
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "role": role_name,
        "bank_id": new_user.bank_id,
        "branch_id": new_user.branch_id
    }

@router.post("/login")
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    raw_username = (form_data.username or "").strip()
    user = db.query(models.User).filter(models.User.username == raw_username).first()

    # Handle bank-specific user pattern: {bank}_user (e.g., hdfc_user, sbi_user)
    if raw_username.endswith("_user"):
        bank_code = raw_username.replace("_user", "").upper()
        if bank_code:
            # Ensure bank exists
            bank = db.query(models.Bank).filter(models.Bank.code == bank_code).first()
            if not bank:
                # Check if bank already exists by name to avoid duplicates
                bank = db.query(models.Bank).filter(models.Bank.name == f"{bank_code} Bank").first()
            if not bank:
                try:
                    bank = models.Bank(
                        name=f"{bank_code} Bank",
                        code=bank_code,
                        ifsc_prefix=bank_code,
                        is_active=True,
                    )
                    db.add(bank)
                    db.flush()
                except Exception:
                    db.rollback()
                    # Try to find existing bank again
                    bank = db.query(models.Bank).filter(models.Bank.name == f"{bank_code} Bank").first()
                    if not bank:
                        bank = db.query(models.Bank).filter(models.Bank.code == bank_code).first()

            # Ensure a demo-enabled branch exists
            branch = (
                db.query(models.Branch)
                .filter(models.Branch.bank_id == bank.id)
                .order_by(models.Branch.id.asc())
                .first()
            )
            if not branch:
                branch = models.Branch(
                    bank_id=bank.id,
                    branch_code=f"{bank_code}001",
                    branch_name=f"{bank_code} Demo Branch",
                    ifsc_code=f"{bank_code}0000001",
                    demo_access=True,
                    is_active=True,
                )
                db.add(branch)
                db.flush()
            elif not branch.demo_access:
                branch.demo_access = True
                db.add(branch)

            # Ensure role exists
            bank_role = (
                db.query(models.Role)
                .filter(models.Role.name == "Bank HQ Integration User")
                .first()
            )
            if not bank_role:
                bank_role = models.Role(name="Bank HQ Integration User", description="Bank User")
                db.add(bank_role)
                db.flush()

            expected_hash = security.get_password_hash(f"{bank_code.lower()}123")

            # Create or heal existing user
            if not user:
                user = models.User(
                    username=raw_username,
                    email=f"{raw_username}@lumien.local",
                    hashed_password=expected_hash,
                    role="branch_user",
                    bank_id=bank.id,
                    branch_id=branch.id,
                    is_active=True,
                    roles=[bank_role],
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                changed = False
                if user.bank_id != bank.id:
                    user.bank_id = bank.id
                    changed = True
                if user.branch_id != branch.id:
                    user.branch_id = branch.id
                    changed = True
                if user.hashed_password != expected_hash:
                    user.hashed_password = expected_hash
                    changed = True

                if not user.role:
                    user.role = "branch_user"
                    changed = True

                if bank_role and bank_role not in (user.roles or []):
                    user.roles = list(user.roles or []) + [bank_role]
                    changed = True

                if changed:
                    db.add(user)
                    db.commit()
                    db.refresh(user)

    if not user:
        bank = (
            db.query(models.Bank)
            .filter(func.lower(models.Bank.name) == raw_username.lower())
            .first()
        )
        if bank:
            bank_login_username = f"bank_{bank.id}_login"
            user = db.query(models.User).filter(models.User.username == bank_login_username).first()
            if not user:
                bank_role = db.query(models.Role).filter(models.Role.name == "Bank HQ Integration User").first()
                if not bank_role:
                    bank_role = models.Role(name="Bank HQ Integration User", description="Bank User")
                    db.add(bank_role)
                    db.flush()

                branch = (
                    db.query(models.Branch)
                    .filter(models.Branch.bank_id == bank.id)
                    .order_by(models.Branch.id.asc())
                    .first()
                )

                user = models.User(
                    username=bank_login_username,
                    email=f"{bank_login_username}@lumien.local",
                    hashed_password=security.get_password_hash("password123"),
                    is_active=True,
                    bank_id=bank.id,
                    branch_id=branch.id if branch else None,
                    roles=[bank_role],
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                # Ensure deterministic password for bank-name login
                expected_hash = security.get_password_hash("password123")
                if user.hashed_password != expected_hash:
                    user.hashed_password = expected_hash
                    db.add(user)
                    db.commit()

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _ensure_demo_operations_data(db, user)

    roles = [role.name for role in user.roles]
    access_token = security.create_access_token(
        subject=user.username, 
        roles=roles,
        bank_id=user.bank_id,
        branch_id=user.branch_id
    )
    
    # Create login audit record
    audit_id = str(uuid.uuid4())
    login_audit = models.LoginAudit(
        audit_id=audit_id,
        user_id=user.id,
        username=user.username,
        email=user.email,
        bank_id=user.bank_id,
        bank_name=user.bank.name if user.bank else None,
        bank_code=user.bank.code if user.bank else None,
        roles=json.dumps(roles),
        status="active"
    )
    db.add(login_audit)
    db.commit()
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "roles": roles, 
        "user": user.username,
        "bank_id": user.bank_id,
        "branch_id": user.branch_id,
        "bank_name": user.bank.name if user.bank else None,
        "bank_code": user.bank.code if user.bank else None,
        "branch_name": user.branch.branch_name if user.branch else None,
        "audit_id": audit_id
    }


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Record user logout"""
    # Find active login audit record
    audit_record = db.query(models.LoginAudit).filter(
        models.LoginAudit.user_id == current_user.id,
        models.LoginAudit.status == "active"
    ).order_by(models.LoginAudit.login_time.desc()).first()
    
    if audit_record:
        audit_record.logout_time = datetime.utcnow()
        audit_record.status = "logged_out"
        
        # Calculate session duration
        if audit_record.login_time:
            duration = audit_record.logout_time - audit_record.login_time
            audit_record.session_duration_minutes = int(duration.total_seconds() / 60)
        
        db.commit()
    
    return {"message": "Logged out successfully"}


@router.get("/login-audit", response_model=dict)
def get_login_audit(
    bank_id: Optional[int] = None,
    bank_code: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Get login audit records for admin/CEO.
    Admin can filter by bank, date range, and status.
    """
    # Check if user is admin or CEO
    user_roles = [role.name for role in current_user.roles]
    if not any(role in user_roles for role in ["CEO", "CTO", "admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view login audit records"
        )
    
    # Build query
    query = db.query(models.LoginAudit).join(
        models.User, models.LoginAudit.user_id == models.User.id
    )
    
    # Apply filters
    if bank_id:
        query = query.filter(models.LoginAudit.bank_id == bank_id)
    if bank_code:
        query = query.filter(models.LoginAudit.bank_code.ilike(f"%{bank_code}%"))
    if start_date:
        query = query.filter(models.LoginAudit.login_time >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(models.LoginAudit.login_time <= datetime.fromisoformat(end_date))
    if status:
        query = query.filter(models.LoginAudit.status == status)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    records = query.order_by(models.LoginAudit.login_time.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "audit_id": r.audit_id,
                "username": r.username,
                "email": r.email,
                "bank_name": r.bank_name,
                "bank_code": r.bank_code,
                "roles": json.loads(r.roles) if r.roles else [],
                "login_time": r.login_time.isoformat() if r.login_time else None,
                "logout_time": r.logout_time.isoformat() if r.logout_time else None,
                "session_duration_minutes": r.session_duration_minutes,
                "status": r.status
            }
            for r in records
        ]
    }


@router.get("/login-audit/summary", response_model=dict)
def get_login_audit_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Get login audit summary by bank for admin/CEO.
    Shows login counts per bank with active sessions.
    """
    # Check if user is admin or CEO
    user_roles = [role.name for role in current_user.roles]
    if not any(role in user_roles for role in ["CEO", "CTO", "admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view login audit summary"
        )
    
    # Build base query
    query = db.query(models.LoginAudit)
    if start_date:
        query = query.filter(models.LoginAudit.login_time >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(models.LoginAudit.login_time <= datetime.fromisoformat(end_date))
    
    # Summary by bank
    bank_summary = db.query(
        models.LoginAudit.bank_name,
        models.LoginAudit.bank_code,
        func.count(models.LoginAudit.id).label("total_logins"),
        func.sum(func.case([(models.LoginAudit.status == "active", 1)], else_=0)).label("active_sessions"),
        func.count(func.distinct(models.LoginAudit.user_id)).label("unique_users")
    ).group_by(
        models.LoginAudit.bank_name,
        models.LoginAudit.bank_code
    ).all()
    
    return {
        "total_records": query.count(),
        "banks": [
            {
                "bank_name": b.bank_name or "Unknown",
                "bank_code": b.bank_code or "N/A",
                "total_logins": b.total_logins,
                "active_sessions": b.active_sessions or 0,
                "unique_users": b.unique_users
            }
            for b in bank_summary
        ]
    }


@router.get("/my-login-history", response_model=dict)
def get_my_login_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Get current user's own login history"""
    records = db.query(models.LoginAudit).filter(
        models.LoginAudit.user_id == current_user.id
    ).order_by(models.LoginAudit.login_time.desc()).limit(limit).all()
    
    return {
        "items": [
            {
                "audit_id": r.audit_id,
                "login_time": r.login_time.isoformat() if r.login_time else None,
                "logout_time": r.logout_time.isoformat() if r.logout_time else None,
                "session_duration_minutes": r.session_duration_minutes,
                "status": r.status
            }
            for r in records
        ]
    }
