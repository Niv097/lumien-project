from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from ..models import models
from ..models.models import get_db
from ..core.security import RoleChecker

router = APIRouter()

admin_checker = RoleChecker(["Lumien Super Admin", "Audit & Compliance Officer"])

@router.get("/banks", dependencies=[Depends(admin_checker)])
def list_banks(db: Session = Depends(get_db)):
    return db.query(models.Bank).all()

@router.get("/audit-logs", dependencies=[Depends(admin_checker)])
def get_audit_logs(
    resource_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc())
    if resource_id:
        query = query.filter(models.AuditLog.resource_id == resource_id)
    return query.limit(100).all()

@router.get("/metrics", dependencies=[Depends(admin_checker)])
def get_metrics(db: Session = Depends(get_db)):
    total_cases = db.query(models.Complaint).count()
    routed_cases = db.query(models.Complaint).filter(models.Complaint.status == models.CaseStatus.ROUTED).count()
    confirmed_cases = db.query(models.Complaint).filter(models.Complaint.status == models.CaseStatus.BANK_CONFIRMED).count()
    sla_breaches = db.query(models.SLATracking).filter(models.SLATracking.is_breached == True).count()
    
    return {
        "total_cases": total_cases,
        "routed_cases": routed_cases,
        "confirmed_cases": confirmed_cases,
        "sla_breaches": sla_breaches,
        "efficiency": (confirmed_cases / routed_cases * 100) if routed_cases > 0 else 0
    }

@router.get("/sla-monitor", dependencies=[Depends(admin_checker)])
def get_sla_monitor(db: Session = Depends(get_db)):
    # Get cases approaching deadline or breached
    return db.query(models.SLATracking).join(models.Complaint).order_by(models.SLATracking.deadline).limit(50).all()

@router.get("/misroute-analytics", dependencies=[Depends(admin_checker)])
def get_misroute_analytics(db: Session = Depends(get_db)):
    # Identify cases marked NOT_RELATED by banks
    return db.query(models.BankResponse).filter(models.BankResponse.response_code == "NOT_RELATED").all()
