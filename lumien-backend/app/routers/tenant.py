"""
Multi-Tenant API Router for LUMIEN

This module provides dynamic filtering endpoints that support:
- Bank-wise filtering
- Branch-wise filtering
- Case/workflow linking with proper foreign keys
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from ..models import models
from ..models.models import get_db
from ..core.security import get_current_user, RoleChecker, get_current_user_with_tenant

router = APIRouter()

# Role checkers
admin_checker = RoleChecker(["Lumien Super Admin", "Audit & Compliance Officer"])
bank_checker = RoleChecker(["Lumien Super Admin", "Bank HQ Integration User"])
ops_checker = RoleChecker(["Lumien Super Admin", "Lumien Operations Manager"])


@router.get("/banks")
def get_banks(
    db: Session = Depends(get_db)
):
    """
    Get all banks (public endpoint for Gateway).
    Returns all active banks for bank selection before login.
    """
    banks = db.query(models.Bank).filter(models.Bank.is_active == True).all()
    
    return [
        {
            "id": b.id,
            "name": b.name,
            "code": b.code,
            "ifsc_prefix": b.ifsc_prefix,
            "integration_model": b.integration_model,
            "sla_hours": b.sla_hours,
            "is_active": b.is_active,
            "branch_count": len(b.branches) if b.branches else 0
        }
        for b in banks
    ]


@router.get("/branches")
def get_branches(
    bank_id: Optional[int] = Query(None, description="Filter by bank ID"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get branches with optional bank filtering.
    - If bank_id provided, returns branches for that bank
    - If no bank_id, returns all branches (admins only) or user's bank branches
    """
    query = db.query(models.Branch)
    
    user_roles = [r.name for r in current_user.roles]
    is_admin = "Lumien Super Admin" in user_roles or "Audit & Compliance Officer" in user_roles
    
    print(f"DEBUG get_branches: bank_id={bank_id}, user.bank_id={current_user.bank_id}, user.branch_id={current_user.branch_id}, is_admin={is_admin}")
    
    # Apply bank filter
    if bank_id:
        query = query.filter(models.Branch.bank_id == bank_id)
        print(f"DEBUG: Filtering by provided bank_id={bank_id}")
    elif not is_admin:
        # Non-admin users only see their bank's branches
        if current_user.bank_id:
            query = query.filter(models.Branch.bank_id == current_user.bank_id)
            print(f"DEBUG: Filtering by user.bank_id={current_user.bank_id}")
        # If user has a specific branch, only show that branch
        if current_user.branch_id:
            query = query.filter(models.Branch.id == current_user.branch_id)
            print(f"DEBUG: Filtering by user.branch_id={current_user.branch_id}")
    
    branches = query.all()
    print(f"DEBUG: Returning {len(branches)} branches")
    
    return [
        {
            "id": b.id,
            "bank_id": b.bank_id,
            "bank_name": b.bank.name if b.bank else None,
            "bank_code": b.bank.code if b.bank else None,
            "branch_code": b.branch_code,
            "branch_name": b.branch_name,
            "ifsc_code": b.ifsc_code,
            "address": b.address,
            "city": b.city,
            "state": b.state,
            "is_active": b.is_active
        }
        for b in branches
    ]


@router.get("/demo/readme")
def get_demo_readme(
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    q = db.query(models.DemoReadme)
    total = q.count()
    items = q.order_by(models.DemoReadme.id.asc()).offset(skip).limit(limit).all()
    return {
        "items": [{"id": r.id, "line": r.line} for r in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/demo/i4c-inbound-fraud-reports")
def get_demo_i4c_inbound_fraud_reports(
    acknowledgement_no: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    q = db.query(models.DemoI4CInboundFraudReport)
    if acknowledgement_no:
        q = q.filter(models.DemoI4CInboundFraudReport.acknowledgement_no == acknowledgement_no)
    total = q.count()
    items = q.order_by(models.DemoI4CInboundFraudReport.id.desc()).offset(skip).limit(limit).all()
    return {
        "items": [
            {
                "id": r.id,
                "acknowledgement_no": r.acknowledgement_no,
                "sub_category": r.sub_category,
                "requestor": r.requestor,
                "payer_bank": r.payer_bank,
                "payer_bank_code": r.payer_bank_code,
                "mode_of_payment": r.mode_of_payment,
                "payer_mobile_number": r.payer_mobile_number,
                "payer_account_number": r.payer_account_number,
                "state": r.state,
                "district": r.district,
                "transaction_type": r.transaction_type,
                "wallet": r.wallet,
                "received_at": r.received_at.isoformat() if r.received_at else None,
                "incident_count": r.incident_count,
                "total_disputed_amount": r.total_disputed_amount,
                "bank_ack_response_code": r.bank_ack_response_code,
                "bank_job_id": r.bank_job_id,
                "calc_total_disputed_amount": r.calc_total_disputed_amount,
                "amount_match_flag": r.amount_match_flag,
            }
            for r in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/demo/i4c-incidents")
def get_demo_i4c_incidents(
    acknowledgement_no: Optional[str] = Query(None),
    incident_id: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    q = db.query(models.DemoI4CIncident)
    if acknowledgement_no:
        q = q.filter(models.DemoI4CIncident.acknowledgement_no == acknowledgement_no)
    if incident_id:
        q = q.filter(models.DemoI4CIncident.incident_id == incident_id)
    total = q.count()
    items = q.order_by(models.DemoI4CIncident.id.desc()).offset(skip).limit(limit).all()
    return {
        "items": [
            {
                "id": r.id,
                "acknowledgement_no": r.acknowledgement_no,
                "incident_id": r.incident_id,
                "sub_category": r.sub_category,
                "amount": r.amount,
                "rrn": r.rrn,
                "transaction_date": r.transaction_date.isoformat() if r.transaction_date else None,
                "transaction_time": r.transaction_time,
                "disputed_amount": r.disputed_amount,
                "layer": r.layer,
                "payee_bank": r.payee_bank,
                "payee_bank_code": r.payee_bank_code,
                "payee_ifsc_code": r.payee_ifsc_code,
                "payee_account_number": r.payee_account_number,
            }
            for r in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/demo/bank-case-workflow")
def get_demo_bank_case_workflow(
    case_id: Optional[str] = Query(None),
    acknowledgement_no: Optional[str] = Query(None),
    job_id: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    q = db.query(models.DemoBankCaseWorkflow)
    if case_id:
        q = q.filter(models.DemoBankCaseWorkflow.case_id == case_id)
    if acknowledgement_no:
        q = q.filter(models.DemoBankCaseWorkflow.acknowledgement_no == acknowledgement_no)
    if job_id:
        q = q.filter(models.DemoBankCaseWorkflow.job_id == job_id)
    total = q.count()
    items = q.order_by(models.DemoBankCaseWorkflow.id.desc()).offset(skip).limit(limit).all()
    return {
        "items": [
            {
                "id": r.id,
                "case_id": r.case_id,
                "acknowledgement_no": r.acknowledgement_no,
                "job_id": r.job_id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "assigned_queue": r.assigned_queue,
                "assigned_branch_id": r.assigned_branch_id,
                "priority": r.priority,
                "current_state": r.current_state,
                "scenario": r.scenario,
            }
            for r in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/demo/bank-hold-actions")
def get_demo_bank_hold_actions(
    case_id: Optional[str] = Query(None),
    acknowledgement_no: Optional[str] = Query(None),
    incident_id: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    q = db.query(models.DemoBankHoldAction)
    if case_id:
        q = q.filter(models.DemoBankHoldAction.case_id == case_id)
    if acknowledgement_no:
        q = q.filter(models.DemoBankHoldAction.acknowledgement_no == acknowledgement_no)
    if incident_id:
        q = q.filter(models.DemoBankHoldAction.incident_id == incident_id)
    total = q.count()
    items = q.order_by(models.DemoBankHoldAction.id.desc()).offset(skip).limit(limit).all()
    return {
        "items": [
            {
                "id": r.id,
                "action_id": r.action_id,
                "case_id": r.case_id,
                "acknowledgement_no": r.acknowledgement_no,
                "incident_id": r.incident_id,
                "action_type": r.action_type,
                "action_time": r.action_time.isoformat() if r.action_time else None,
                "requested_amount": r.requested_amount,
                "action_amount": r.action_amount,
                "held_amount": r.held_amount,
                "hold_reference": r.hold_reference,
                "negative_lien_flag": r.negative_lien_flag,
                "outcome": r.outcome,
                "remarks": r.remarks,
            }
            for r in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/demo/bank-statusupdate-requests")
def get_demo_bank_statusupdate_requests(
    request_id: Optional[str] = Query(None),
    acknowledgement_no: Optional[str] = Query(None),
    job_id: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    q = db.query(models.DemoBankStatusUpdateRequest)
    if request_id:
        q = q.filter(models.DemoBankStatusUpdateRequest.request_id == request_id)
    if acknowledgement_no:
        q = q.filter(models.DemoBankStatusUpdateRequest.acknowledgement_no == acknowledgement_no)
    if job_id:
        q = q.filter(models.DemoBankStatusUpdateRequest.job_id == job_id)
    total = q.count()
    items = q.order_by(models.DemoBankStatusUpdateRequest.id.desc()).offset(skip).limit(limit).all()
    return {
        "items": [
            {
                "id": r.id,
                "request_id": r.request_id,
                "acknowledgement_no": r.acknowledgement_no,
                "job_id": r.job_id,
                "sent_at": r.sent_at.isoformat() if r.sent_at else None,
                "content_type": r.content_type,
                "authorization_type": r.authorization_type,
                "payload_encrypted": r.payload_encrypted,
                "transaction_count": r.transaction_count,
            }
            for r in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/demo/bank-statusupdate-txn-details")
def get_demo_bank_statusupdate_txn_details(
    request_id: Optional[str] = Query(None),
    acknowledgement_no: Optional[str] = Query(None),
    incident_id: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    q = db.query(models.DemoBankStatusUpdateTxnDetail)
    if request_id:
        q = q.filter(models.DemoBankStatusUpdateTxnDetail.request_id == request_id)
    if acknowledgement_no:
        q = q.filter(models.DemoBankStatusUpdateTxnDetail.acknowledgement_no == acknowledgement_no)
    if incident_id:
        q = q.filter(models.DemoBankStatusUpdateTxnDetail.incident_id == incident_id)
    total = q.count()
    items = q.order_by(models.DemoBankStatusUpdateTxnDetail.id.desc()).offset(skip).limit(limit).all()
    return {
        "items": [
            {
                "id": r.id,
                "request_id": r.request_id,
                "acknowledgement_no": r.acknowledgement_no,
                "job_id": r.job_id,
                "incident_id": r.incident_id,
                "root_rrn_transaction_id": r.root_rrn_transaction_id,
                "root_bankid": r.root_bankid,
                "root_account_number": r.root_account_number,
                "amount": r.amount,
                "transaction_datetime": r.transaction_datetime.isoformat() if r.transaction_datetime else None,
                "disputed_amount": r.disputed_amount,
                "status_code": r.status_code,
                "remarks": r.remarks,
                "phone_number": r.phone_number,
                "pan_number": r.pan_number,
                "email": r.email,
                "root_ifsc_code": r.root_ifsc_code,
                "root_effective_balance": r.root_effective_balance,
                "negative_lien_flag": r.negative_lien_flag,
                "hold_reference": r.hold_reference,
                "held_amount": r.held_amount,
            }
            for r in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/demo/i4c-statusupdate-responses")
def get_demo_i4c_statusupdate_responses(
    request_id: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    q = db.query(models.DemoI4CStatusUpdateResponse)
    if request_id:
        q = q.filter(models.DemoI4CStatusUpdateResponse.request_id == request_id)
    total = q.count()
    items = q.order_by(models.DemoI4CStatusUpdateResponse.id.desc()).offset(skip).limit(limit).all()
    return {
        "items": [
            {
                "id": r.id,
                "request_id": r.request_id,
                "i4c_response_code": r.i4c_response_code,
                "i4c_message": r.i4c_message,
                "received_at": r.received_at.isoformat() if r.received_at else None,
                "error_flag": r.error_flag,
            }
            for r in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/demo/workflow-timeline")
def get_demo_workflow_timeline(
    case_id: Optional[str] = Query(None),
    acknowledgement_no: Optional[str] = Query(None),
    job_id: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    q = db.query(models.DemoWorkflowTimeline)
    if case_id:
        q = q.filter(models.DemoWorkflowTimeline.case_id == case_id)
    if acknowledgement_no:
        q = q.filter(models.DemoWorkflowTimeline.acknowledgement_no == acknowledgement_no)
    if job_id:
        q = q.filter(models.DemoWorkflowTimeline.job_id == job_id)
    total = q.count()
    items = q.order_by(models.DemoWorkflowTimeline.id.desc()).offset(skip).limit(limit).all()
    return {
        "items": [
            {
                "id": r.id,
                "case_id": r.case_id,
                "acknowledgement_no": r.acknowledgement_no,
                "job_id": r.job_id,
                "step_no": r.step_no,
                "step_name": r.step_name,
                "actor": r.actor,
                "start_time": r.start_time.isoformat() if r.start_time else None,
                "end_time": r.end_time.isoformat() if r.end_time else None,
                "step_status": r.step_status,
                "sla_target_minutes": r.sla_target_minutes,
                "actual_minutes": r.actual_minutes,
                "sla_breached": r.sla_breached,
            }
            for r in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/demo/meta-status-codes")
def get_meta_status_codes(
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    q = db.query(models.MetaStatusCode)
    total = q.count()
    items = q.order_by(models.MetaStatusCode.status_code.asc()).offset(skip).limit(limit).all()
    return {
        "items": [
            {
                "id": r.id,
                "status_code": r.status_code,
                "status_label": r.status_label,
                "meaning": r.meaning,
                "owner": r.owner,
                "demo_example_usage": r.demo_example_usage,
            }
            for r in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/demo/scenarios")
def get_demo_scenarios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    q = db.query(models.DemoScenario)
    total = q.count()
    items = q.order_by(models.DemoScenario.scenario.asc()).offset(skip).limit(limit).all()
    return {
        "items": [{"id": r.id, "scenario": r.scenario, "description": r.description} for r in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/cases")
def get_cases(
    bank_id: Optional[int] = Query(None, description="Filter by bank ID"),
    branch_id: Optional[int] = Query(None, description="Filter by branch ID"),
    status: Optional[str] = Query(None, description="Filter by case status"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get cases with optional bank and branch filtering.
    - bank_id: Filter cases for specific bank
    - branch_id: Filter cases for specific branch
    - status: Filter by case status
    """
    query = db.query(models.Complaint)
    
    user_roles = [r.name for r in current_user.roles]
    is_admin = "Lumien Super Admin" in user_roles or "Lumien Operations Manager" in user_roles
    
    # Apply filters
    if bank_id:
        query = query.filter(models.Complaint.bank_id == bank_id)
    
    if branch_id:
        query = query.filter(models.Complaint.branch_id == branch_id)
    
    if status:
        try:
            status_enum = models.CaseStatus[status.upper()]
            query = query.filter(models.Complaint.status == status_enum)
        except KeyError:
            pass  # Invalid status, ignore filter
    
    # Non-admin users only see cases for their bank/branch
    if not is_admin:
        if current_user.bank_id:
            query = query.filter(models.Complaint.bank_id == current_user.bank_id)
        if current_user.branch_id:
            query = query.filter(models.Complaint.branch_id == current_user.branch_id)
    
    complaints = query.all()
    
    return [
        {
            "id": c.id,
            "complaint_id": c.complaint_id,
            "victim_name": c.victim_name,
            "victim_mobile": c.victim_mobile,
            "incident_date": c.incident_date.isoformat() if c.incident_date else None,
            "fraud_type": c.fraud_type,
            "amount": c.amount,
            "currency": c.currency,
            "status": c.status.value if c.status else None,
            "bank_id": c.bank_id,
            "bank_name": c.bank.name if c.bank else None,
            "bank_code": c.bank.code if c.bank else None,
            "branch_id": c.branch_id,
            "branch_name": c.branch.branch_name if c.branch else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        }
        for c in complaints
    ]


@router.get("/cases/{case_id}")
def get_case_detail(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get detailed case information including related data"""
    case = db.query(models.Complaint).filter(models.Complaint.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Check authorization
    user_roles = [r.name for r in current_user.roles]
    is_admin = "Lumien Super Admin" in user_roles or "Lumien Operations Manager" in user_roles
    
    if not is_admin:
        if current_user.bank_id and case.bank_id != current_user.bank_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this case")
        if current_user.branch_id and case.branch_id != current_user.branch_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this case")
    
    # Audit access
    audit = models.AuditLog(
        user_id=current_user.id,
        bank_id=current_user.bank_id,
        branch_id=current_user.branch_id,
        action="VIEW_CASE_DETAIL",
        resource="complaint",
        resource_id=str(case_id)
    )
    db.add(audit)
    db.commit()
    
    return {
        "complaint": {
            "id": case.id,
            "complaint_id": case.complaint_id,
            "victim_name": case.victim_name,
            "victim_mobile": case.victim_mobile,
            "incident_date": case.incident_date.isoformat() if case.incident_date else None,
            "fraud_type": case.fraud_type,
            "amount": case.amount,
            "currency": case.currency,
            "ifsc_signal": case.ifsc_signal,
            "status": case.status.value if case.status else None,
            "bank": {
                "id": case.bank.id,
                "name": case.bank.name,
                "code": case.bank.code
            } if case.bank else None,
            "branch": {
                "id": case.branch.id,
                "branch_code": case.branch.branch_code,
                "branch_name": case.branch.branch_name,
                "ifsc_code": case.branch.ifsc_code
            } if case.branch else None,
        },
        "enrichment": {
            "target_bank_id": case.enrichment.target_bank_id if case.enrichment else None,
            "target_branch_id": case.enrichment.target_branch_id if case.enrichment else None,
            "confidence_score": case.enrichment.confidence_score if case.enrichment else None,
            "signals": case.enrichment.signals if case.enrichment else None,
            "validation_method": case.enrichment.validation_method if case.enrichment else None,
            "bank": {
                "name": case.bank.name if case.bank else None
            } if case.bank else None,
            "ifsc": case.ifsc_signal
        } if case.enrichment else {
            "confidence_score": 0,
            "bank": {"name": case.bank.name if case.bank else None},
            "ifsc": case.ifsc_signal
        },
        "routing": case.routing_logs,
        "routing_logs": [
            {
                "id": r.id,
                "bank_id": r.bank_id,
                "branch_id": r.branch_id,
                "routed_at": r.routed_at.isoformat() if r.routed_at else None,
                "request_id": r.request_id,
                "status": r.status
            }
            for r in case.routing_logs
        ],
        "responses": [
            {
                "id": resp.id,
                "bank_id": resp.bank_id,
                "branch_id": resp.branch_id,
                "response_code": resp.response_code,
                "action_taken": resp.action_taken,
                "hold_amount": resp.hold_amount,
                "remarks": resp.remarks,
                "responded_at": resp.responded_at.isoformat() if resp.responded_at else None,
                # I4C Sync Status fields
                "i4c_sync_status": resp.i4c_sync_status,
                "i4c_sync_attempted_at": resp.i4c_sync_attempted_at.isoformat() if resp.i4c_sync_attempted_at else None,
                "i4c_sync_response_code": resp.i4c_sync_response_code,
                "i4c_sync_message": resp.i4c_sync_message,
                "i4c_job_id": resp.i4c_job_id
            }
            for resp in case.responses
        ],
        "bank_responses": [
            {
                "id": resp.id,
                "bank_id": resp.bank_id,
                "branch_id": resp.branch_id,
                "response_code": resp.response_code,
                "action_taken": resp.action_taken,
                "hold_amount": resp.hold_amount,
                "remarks": resp.remarks,
                "responded_at": resp.responded_at.isoformat() if resp.responded_at else None,
                # I4C Sync Status fields
                "i4c_sync_status": resp.i4c_sync_status,
                "i4c_sync_attempted_at": resp.i4c_sync_attempted_at.isoformat() if resp.i4c_sync_attempted_at else None,
                "i4c_sync_response_code": resp.i4c_sync_response_code,
                "i4c_sync_message": resp.i4c_sync_message,
                "i4c_job_id": resp.i4c_job_id
            }
            for resp in case.responses
        ],
        "sla": {
            "start_time": case.sla.start_time.isoformat() if case.sla and case.sla.start_time else None,
            "deadline": case.sla.deadline.isoformat() if case.sla and case.sla.deadline else None,
            "completion_time": case.sla.completion_time.isoformat() if case.sla and case.sla.completion_time else None,
            "is_breached": case.sla.is_breached if case.sla else None
        } if case.sla else None,
        "workflows": [
            {
                "id": w.id,
                "case_id": w.case_id,
                "job_id": w.job_id,
                "scenario": w.scenario,
                "status": w.status,
                "priority": w.priority,
                "assigned_bank_id": w.assigned_bank_id,
                "assigned_branch_id": w.assigned_branch_id,
                "created_at": w.created_at.isoformat() if w.created_at else None
            }
            for w in case.workflows
        ],
        "hold_actions": [
            {
                "id": h.id,
                "case_id": h.case_id,
                "action_type": h.action_type,
                "outcome": h.outcome,
                "held_amount": h.held_amount,
                "expected_amount": h.expected_amount,
                "created_at": h.created_at.isoformat() if h.created_at else None
            }
            for h in case.hold_actions
        ],
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None
    }


@router.get("/workflow")
def get_workflows(
    case_id: Optional[int] = Query(None, description="Filter by case ID (complaint_id)"),
    bank_id: Optional[int] = Query(None, description="Filter by bank ID"),
    branch_id: Optional[int] = Query(None, description="Filter by branch ID"),
    status: Optional[str] = Query(None, description="Filter by workflow status"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get workflows with optional filtering.
    - case_id: Filter workflows for specific case
    - bank_id: Filter by assigned bank
    - branch_id: Filter by assigned branch
    """
    query = db.query(models.CaseWorkflow)
    
    user_roles = [r.name for r in current_user.roles]
    is_admin = "Lumien Super Admin" in user_roles or "Lumien Operations Manager" in user_roles
    
    # Apply filters
    if case_id:
        query = query.filter(models.CaseWorkflow.complaint_id == case_id)
    
    if bank_id:
        query = query.filter(models.CaseWorkflow.assigned_bank_id == bank_id)
    
    if branch_id:
        query = query.filter(models.CaseWorkflow.assigned_branch_id == branch_id)
    
    if status:
        query = query.filter(models.CaseWorkflow.status == status)
    
    # Non-admin users only see workflows for their bank/branch
    if not is_admin:
        if current_user.bank_id:
            query = query.filter(models.CaseWorkflow.assigned_bank_id == current_user.bank_id)
        if current_user.branch_id:
            query = query.filter(models.CaseWorkflow.assigned_branch_id == current_user.branch_id)
    
    workflows = query.all()
    
    return [
        {
            "id": w.id,
            "case_id": w.case_id,
            "complaint_id": w.complaint_id,
            "job_id": w.job_id,
            "acknowledgement_no": w.acknowledgement_no,
            "scenario": w.scenario,
            "status": w.status,
            "priority": w.priority,
            "assigned_bank_id": w.assigned_bank_id,
            "bank_name": w.bank.name if w.bank else None,
            "bank_code": w.bank.code if w.bank else None,
            "assigned_branch_id": w.assigned_branch_id,
            "branch_name": w.branch.branch_name if w.branch else None,
            "created_at": w.created_at.isoformat() if w.created_at else None,
            "updated_at": w.updated_at.isoformat() if w.updated_at else None,
            "remarks": w.remarks
        }
        for w in workflows
    ]


@router.get("/dashboard")
def get_dashboard(
    bank_id: Optional[int] = Query(None, description="Filter by bank ID"),
    branch_id: Optional[int] = Query(None, description="Filter by branch ID"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get dashboard metrics with optional bank/branch filtering.
    Returns summary statistics for cases, workflows, and actions.
    """
    user_roles = [r.name for r in current_user.roles]
    is_admin = "Lumien Super Admin" in user_roles or "Lumien Operations Manager" in user_roles
    
    # Determine effective bank_id and branch_id
    effective_bank_id = bank_id
    effective_branch_id = branch_id
    
    if not is_admin:
        # Non-admin users can only see their own bank/branch data
        if current_user.bank_id:
            effective_bank_id = current_user.bank_id
        if current_user.branch_id:
            effective_branch_id = current_user.branch_id
    
    # Build base query for complaints
    complaint_query = db.query(models.Complaint)
    if effective_bank_id:
        complaint_query = complaint_query.filter(models.Complaint.bank_id == effective_bank_id)
    if effective_branch_id:
        complaint_query = complaint_query.filter(models.Complaint.branch_id == effective_branch_id)
    
    total_cases = complaint_query.count()
    
    # Cases by status
    status_counts = {}
    for status in models.CaseStatus:
        count = complaint_query.filter(models.Complaint.status == status).count()
        if count > 0:
            status_counts[status.value] = count
    
    # Total amount involved
    total_amount = db.query(models.Complaint).filter(
        models.Complaint.bank_id == effective_bank_id if effective_bank_id else True,
        models.Complaint.branch_id == effective_branch_id if effective_branch_id else True
    ).with_entities(models.Complaint.amount).all()
    total_amount = sum([a[0] for a in total_amount if a[0]])
    
    # Workflow stats
    workflow_query = db.query(models.CaseWorkflow)
    if effective_bank_id:
        workflow_query = workflow_query.filter(models.CaseWorkflow.assigned_bank_id == effective_bank_id)
    if effective_branch_id:
        workflow_query = workflow_query.filter(models.CaseWorkflow.assigned_branch_id == effective_branch_id)
    
    total_workflows = workflow_query.count()
    
    # Hold actions stats
    hold_query = db.query(models.HoldAction)
    if effective_bank_id:
        hold_query = hold_query.filter(models.HoldAction.bank_id == effective_bank_id)
    if effective_branch_id:
        hold_query = hold_query.filter(models.HoldAction.branch_id == effective_branch_id)
    
    total_hold_actions = hold_query.count()
    total_held_amount = db.query(models.HoldAction).filter(
        models.HoldAction.bank_id == effective_bank_id if effective_bank_id else True,
        models.HoldAction.branch_id == effective_branch_id if effective_branch_id else True
    ).with_entities(models.HoldAction.held_amount).all()
    total_held_amount = sum([h[0] for h in total_held_amount if h[0]])
    
    # SLA tracking
    sla_query = db.query(models.SLATracking)
    if effective_bank_id:
        sla_query = sla_query.filter(models.SLATracking.bank_id == effective_bank_id)
    if effective_branch_id:
        sla_query = sla_query.filter(models.SLATracking.branch_id == effective_branch_id)
    
    sla_breaches = sla_query.filter(models.SLATracking.is_breached == True).count()
    
    return {
        "filters_applied": {
            "bank_id": effective_bank_id,
            "branch_id": effective_branch_id
        },
        "cases": {
            "total": total_cases,
            "by_status": status_counts
        },
        "financial": {
            "total_amount": total_amount,
            "total_held_amount": total_held_amount,
            "hold_success_rate": (total_held_amount / total_amount * 100) if total_amount > 0 else 0
        },
        "workflows": {
            "total": total_workflows
        },
        "hold_actions": {
            "total": total_hold_actions,
            "total_held_amount": total_held_amount
        },
        "sla": {
            "breaches": sla_breaches,
            "breach_rate": (sla_breaches / total_cases * 100) if total_cases > 0 else 0
        }
    }


@router.get("/hold-actions")
def get_hold_actions(
    bank_id: Optional[int] = Query(None, description="Filter by bank ID"),
    branch_id: Optional[int] = Query(None, description="Filter by branch ID"),
    case_id: Optional[str] = Query(None, description="Filter by case ID"),
    outcome: Optional[str] = Query(None, description="Filter by outcome"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get hold actions with optional filtering"""
    query = db.query(models.HoldAction)
    
    user_roles = [r.name for r in current_user.roles]
    is_admin = "Lumien Super Admin" in user_roles
    
    if bank_id:
        query = query.filter(models.HoldAction.bank_id == bank_id)
    if branch_id:
        query = query.filter(models.HoldAction.branch_id == branch_id)
    if case_id:
        query = query.filter(models.HoldAction.case_id == case_id)
    if outcome:
        query = query.filter(models.HoldAction.outcome == outcome)
    
    if not is_admin:
        if current_user.bank_id:
            query = query.filter(models.HoldAction.bank_id == current_user.bank_id)
        if current_user.branch_id:
            query = query.filter(models.HoldAction.branch_id == current_user.branch_id)
    
    actions = query.all()
    
    return [
        {
            "id": a.id,
            "case_id": a.case_id,
            "complaint_id": a.complaint.complaint_id if a.complaint else None,
            "action_type": a.action_type,
            "outcome": a.outcome,
            "held_amount": a.held_amount,
            "expected_amount": a.expected_amount,
            "bank_id": a.bank_id,
            "bank_name": a.bank.name if a.bank else None,
            "branch_id": a.branch_id,
            "branch_name": a.branch.branch_name if a.branch else None,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in actions
    ]
