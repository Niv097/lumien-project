from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models import models
from ..models.models import get_db
from ..services.workflow import workflow_service
from ..core.security import get_current_user, RoleChecker
from ..core.i4c_encryption import get_i4c_encryption
from datetime import datetime
import uuid
import requests

router = APIRouter()

# Accessible by Bank users and Admins
bank_checker = RoleChecker(["Lumien Super Admin", "Bank HQ Integration User", "Lumien Operations Manager"])


def generate_job_id() -> str:
    """Generate unique job ID for I4C"""
    return f"BANKS-{uuid.uuid4().hex[:12].upper()}"


def call_i4c_fraud_report_status_update(
    case: models.Complaint,
    status_code: str,
    remarks: str,
    hold_amount: float = 0.0,
    db: Session = None
) -> dict:
    """
    Call I4C FraudReportStatusUpdate API to report bank action back to I4C.
    This is the backend callback - NOT a UI redirect.
    """
    try:
        encryption = get_i4c_encryption()
        
        # Build payload per I4C MHA specs
        payload_data = {
            "acknowledgement_no": case.complaint_id,  # Signal ID from I4C
            "job_id": generate_job_id(),
            "txn_type": "Transaction Put on Hold" if status_code in ["HOLD", "HOLD_CONFIRMED", "HOLD_INITIATED"] else "Status Update",
            "rrn_transaction_id": f"RRN-{uuid.uuid4().hex[:8].upper()}",  # Generate RRN
            "amount": hold_amount if hold_amount > 0 else (case.amount or 0),
            "root_account_number": f"ACCT-{uuid.uuid4().hex[:6].upper()}",  # Masked account
            "root_ifsc_code": case.ifsc_signal or "UNKNOWN",
            "root_effective_balance": str(case.amount or 0),
            "status_code": status_code,  # HOLD, NOT_RELATED, RELATED_CONFIRMED
            "remarks": remarks or f"Bank action: {status_code}"
        }
        
        # Encrypt payload
        encrypted_payload = encryption.encrypt_payload(payload_data)
        
        # Prepare API request
        api_payload = {
            "requestId": str(uuid.uuid4()),
            "payload": encrypted_payload
        }
        
        # TODO: In production, use actual I4C endpoint from config
        # For now, simulate the API call
        i4c_endpoint = "https://api.i4c.gov.in/banking/FraudReportStatusUpdate"
        
        # Simulate API call (replace with actual HTTP call in production)
        # response = requests.post(i4c_endpoint, json=api_payload, timeout=30)
        
        # Simulate response for now
        simulated_response = {
            "responseId": str(uuid.uuid4()),
            "status": "SUCCESS",
            "responseCode": "00",
            "responseMessage": "Status update received successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "job_id": payload_data["job_id"],
            "i4c_response": simulated_response,
            "payload_sent": payload_data
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "job_id": generate_job_id()
        }


@router.post("/{case_id}/respond")
def bank_respond(
    case_id: int, 
    response_data: dict, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(bank_checker)
):
    """
    Bank responds to a case with I4C callback integration.
    
    Actions:
    - RELATED: Mark case as RELATED_CONFIRMED (no I4C call yet)
    - ACTION_INITIATED: Mark as HOLD_INITIATED, then call I4C API
    - NOT_RELATED: Mark as NOT_RELATED, call I4C API
    """
    case = db.query(models.Complaint).filter(models.Complaint.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # If user is a bank user, ensure they belong to the bank this case is routed to
    user_roles = [r.name for r in current_user.roles]
    if "Bank HQ Integration User" in user_roles:
        if not case.enrichment or case.enrichment.target_bank_id != current_user.bank_id:
            raise HTTPException(status_code=403, detail="Unauthorized: This case is not routed to your bank.")

    code = response_data.get("code")  # RELATED, NOT_RELATED, ACTION_INITIATED, etc.
    remarks = response_data.get("remarks", "")
    hold_amount = response_data.get("hold_amount", 0.0)
    
    # Map action code to status and determine I4C callback behavior
    new_status = None
    i4c_status_code = None
    requires_i4c_callback = False
    
    if code == "RELATED":
        # A. CONFIRM RELATED - Marks case as RELATED_CONFIRMED
        new_status = models.CaseStatus.RELATED_CONFIRMED
        i4c_status_code = "RELATED_CONFIRMED"
        requires_i4c_callback = False  # No I4C call for just confirming related
        
    elif code == "ACTION_INITIATED":
        # B. INITIATE HOLD / FREEZE
        # Workflow: Save hold → Update status → Call I4C API
        new_status = models.CaseStatus.HOLD_INITIATED
        i4c_status_code = "HOLD"
        requires_i4c_callback = True
        
    elif code == "NOT_RELATED":
        # C. MARK NOT RELATED
        new_status = models.CaseStatus.NOT_RELATED
        i4c_status_code = "NOT_RELATED"
        requires_i4c_callback = True
        
    elif code == "ALREADY_FROZEN":
        new_status = models.CaseStatus.ALREADY_FROZEN
        i4c_status_code = "ALREADY_FROZEN"
        requires_i4c_callback = True
        
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action code: {code}")
    
    # Validate transition
    workflow_service.validate_transition(case.status, new_status)

    # Record bank response with I4C sync tracking
    resp = models.BankResponse(
        complaint_id=case.id,
        bank_id=case.enrichment.target_bank_id if case.enrichment else current_user.bank_id,
        branch_id=current_user.branch_id,
        response_code=code,
        action_taken=response_data.get("action_taken", code),
        hold_amount=hold_amount,
        remarks=remarks,
        responded_at=datetime.utcnow(),
        responded_by=current_user.id,
        i4c_sync_status="PENDING" if requires_i4c_callback else "NOT_REQUIRED",
        i4c_job_id=generate_job_id() if requires_i4c_callback else None
    )
    db.add(resp)
    db.flush()  # Get resp.id before I4C call
    
    # Call I4C API if required
    i4c_result = None
    if requires_i4c_callback:
        i4c_result = call_i4c_fraud_report_status_update(
            case=case,
            status_code=i4c_status_code,
            remarks=remarks,
            hold_amount=hold_amount,
            db=db
        )
        
        # Update response with I4C sync result
        resp.i4c_sync_attempted_at = datetime.utcnow()
        if i4c_result["success"]:
            resp.i4c_sync_status = "SYNCED"
            resp.i4c_sync_response_code = i4c_result.get("i4c_response", {}).get("responseCode", "00")
            resp.i4c_sync_message = i4c_result.get("i4c_response", {}).get("responseMessage", "Success")
        else:
            resp.i4c_sync_status = "FAILED"
            resp.i4c_sync_response_code = "ERROR"
            resp.i4c_sync_message = i4c_result.get("error", "Unknown error")
    
    # Audit log
    audit = models.AuditLog(
        user_id=current_user.id,
        action=f"BANK_{code}",
        resource="complaint",
        resource_id=str(case.id),
        old_value=str(case.status.value) if case.status else None,
        new_value=str(new_status.value)
    )
    db.add(audit)

    # Update SLA Tracking
    sla = db.query(models.SLATracking).filter(models.SLATracking.complaint_id == case.id).first()
    if sla:
        sla.completion_time = datetime.utcnow()
        if sla.completion_time > sla.deadline:
            sla.is_breached = True

    case.status = new_status
    db.commit()

    return {
        "message": "Response recorded", 
        "new_status": new_status.value,
        "i4c_sync": {
            "status": resp.i4c_sync_status,
            "job_id": resp.i4c_job_id,
            "synced_at": resp.i4c_sync_attempted_at.isoformat() if resp.i4c_sync_attempted_at else None,
            "response_code": resp.i4c_sync_response_code,
            "message": resp.i4c_sync_message
        } if requires_i4c_callback else None
    }

@router.get("/reconciliation")
def get_reconciliation(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(bank_checker)
):
    # Only show cases for the user's bank that are in hold statuses
    query = db.query(models.Complaint).join(models.EnrichmentResult).filter(
        models.EnrichmentResult.target_bank_id == current_user.bank_id,
        models.Complaint.status.in_([
            models.CaseStatus.HOLD_INITIATED, 
            models.CaseStatus.HOLD_CONFIRMED,
            models.CaseStatus.PARTIAL_HOLD
        ])
    )
    return query.all()

@router.post("/{case_id}/reconcile")
def reconcile_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(bank_checker)
):
    case = db.query(models.Complaint).filter(models.Complaint.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # Security check
    if case.enrichment.target_bank_id != current_user.bank_id:
         raise HTTPException(status_code=403, detail="Unauthorized")

    workflow_service.validate_transition(case.status, models.CaseStatus.RECONCILED)
    
    case.status = models.CaseStatus.RECONCILED
    
    audit = models.AuditLog(
        user_id=current_user.id,
        action="BANK_RECONCILE",
        resource="complaint",
        resource_id=str(case.id),
        old_value="HOLD_ACTIVE",
        new_value=models.CaseStatus.RECONCILED
    )
    db.add(audit)
    db.commit()
    return {"message": "Case reconciled successfully"}
