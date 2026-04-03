from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models import models
from ..models.models import get_db
from ..core.security import get_current_user, RoleChecker
import uuid

router = APIRouter()

# Restricted to Lumien Ops and Admins
ops_checker = RoleChecker(["Lumien Super Admin", "Lumien Operations Manager"])

@router.get("")
def get_cases(
    db: Session = Depends(get_db),
    status: str = None,
    current_user: models.User = Depends(get_current_user)
):
    # If bank node, filter by their bank_id
    query = db.query(models.Complaint)
    
    user_roles = [r.name for r in current_user.roles]
    if "Bank HQ Integration User" in user_roles and current_user.bank_id:
        # Only show cases routed to their bank OR where their bank is the target
        query = query.join(models.EnrichmentResult).filter(models.EnrichmentResult.target_bank_id == current_user.bank_id)
        
    if status:
        query = query.filter(models.Complaint.status == status)
    return query.all()

@router.get("/{case_id}")
def get_case_detail(
    case_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    case = db.query(models.Complaint).filter(models.Complaint.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Audit access
    audit = models.AuditLog(
        user_id=current_user.id,
        action="VIEW_DETAIL",
        resource="complaint",
        resource_id=str(case_id)
    )
    db.add(audit)
    db.commit()

    # Prepare enrichment with bank details
    enrichment_data = None
    if case.enrichment:
        enrichment_data = {
            "id": case.enrichment.id,
            "complaint_id": case.enrichment.complaint_id,
            "target_bank_id": case.enrichment.target_bank_id,
            "confidence_score": case.enrichment.confidence_score,
            "signals": case.enrichment.signals,
            "ifsc": case.ifsc_signal,
            "validation_method": case.enrichment.validation_method,
            "bank": {
                "id": case.enrichment.bank.id,
                "name": case.enrichment.bank.name,
                "code": case.enrichment.bank.code
            } if case.enrichment.bank else None
        }

    return {
        "complaint": case,
        "enrichment": enrichment_data,
        "routing": case.routing_logs,
        "bank_responses": case.responses,
        "sla": case.sla
    }

@router.post("/{case_id}/route")
def route_case(
    case_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(ops_checker)
):
    case = db.query(models.Complaint).filter(models.Complaint.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if not case.enrichment or not case.enrichment.target_bank_id:
        raise HTTPException(status_code=400, detail="Cannot route: target bank not identified")

    # Mock routing logic
    log = models.RoutingLog(
        complaint_id=case.id,
        bank_id=case.enrichment.target_bank_id,
        status="SUCCESS",
        request_id=f"FID-{uuid.uuid4().hex[:12].upper()}"
    )
    db.add(log)
    
    case.status = models.CaseStatus.ROUTED
    
    # Audit route
    audit = models.AuditLog(
        user_id=current_user.id,
        action="ROUTE_TO_BANK",
        resource="complaint",
        resource_id=str(case_id),
        new_value=models.CaseStatus.ROUTED
    )
    db.add(audit)
    
    db.commit()
    
    return {"message": "Case routed successfully", "log_id": log.id}
