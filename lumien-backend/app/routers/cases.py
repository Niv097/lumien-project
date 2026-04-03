"""
Cases API Router - Unified case management for demo and I4C cases
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List
from datetime import datetime

from ..models import models
from ..core.security import get_current_user
from ..models.models import SourceType, UnifiedCaseStatus, TimelineEventType

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])


def add_timeline_event(db: Session, case_id: int, branch_id: int | None, event_type: TimelineEventType, description: str, created_by: int | None = None):
    """Helper function to add a timeline event for a case"""
    event = models.Timeline(
        case_id=case_id,
        branch_id=branch_id,
        event_type=event_type,
        description=description,
        created_by=created_by
    )
    db.add(event)
    db.commit()
    return event


def get_db():
    from ..main import engine
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_case_with_branch_scope(db: Session, case_id: str, user: models.User) -> models.Case:
    """
    Get case with strict branch scoping.
    Security: Always filters by branch_id for non-admin users.
    """
    is_admin = user.role == models.UserRole.ADMIN.value
    
    if is_admin:
        # Admin can access any case - but still scope the query
        return db.query(models.Case).filter(models.Case.case_id == case_id).first()
    else:
        # Branch user - MUST filter by branch_id for security
        if not user.branch_id:
            raise HTTPException(status_code=403, detail="User not assigned to any branch")
        
        branch = db.query(models.Branch).filter(models.Branch.id == user.branch_id).first()
        if not branch:
            raise HTTPException(status_code=403, detail="User's branch not found")
        
        # STRICT SECURITY:
        # - Case must match case_id
        # - Branch users can access cases assigned to their branch
        # - Additionally, if demo_access is enabled, they can access ALL demo cases
        case = db.query(models.Case).filter(
            models.Case.case_id == case_id,
            or_(
                models.Case.branch_id == user.branch_id,
                and_(
                    models.Case.source_type == SourceType.DEMO,
                    branch.demo_access == True
                ),
            ),
        ).first()
        
        return case


@router.get("/")
def get_cases(
    status: Optional[str] = Query(None, description="Filter by case status"),
    source_type: Optional[str] = Query(None, description="Filter by source: demo or i4c"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get cases based on user role and branch assignment.
    
    Branch users see:
    1. Cases assigned to their branch
    2. Demo cases if demo_access is enabled for their branch
    
    Admins see all cases.
    """
    user = current_user
    
    # Check if user is admin
    is_admin = user.role == models.UserRole.ADMIN.value
    
    if is_admin:
        # Admin sees all cases
        query = db.query(models.Case)
    else:
        # Branch user - apply visibility rules
        branch = None
        if user.branch_id:
            branch = db.query(models.Branch).filter(models.Branch.id == user.branch_id).first()
        
        if not branch:
            raise HTTPException(status_code=403, detail="User not assigned to any branch")
        
        # Build query for branch user
        # Show:
        # 1. Cases assigned to this branch
        # 2. ALL demo cases if demo_access enabled
        filters = []
        
        # 1. Cases assigned to this branch
        filters.append(models.Case.branch_id == user.branch_id)
        
        # 2. All demo cases if demo_access is enabled
        if branch.demo_access:
            filters.append(models.Case.source_type == SourceType.DEMO)
        
        query = db.query(models.Case).filter(or_(*filters))
    
    # Apply status filter if provided
    if status:
        try:
            status_enum = UnifiedCaseStatus(status.upper())
            query = query.filter(models.Case.status == status_enum)
        except ValueError:
            pass  # Invalid status, ignore filter
    
    # Apply source_type filter if provided
    if source_type:
        try:
            source_enum = SourceType(source_type.lower())
            query = query.filter(models.Case.source_type == source_enum)
        except ValueError:
            pass
    
    cases = query.order_by(models.Case.created_at.desc()).all()
    
    # Format response - HIDE ALL bank identity information
    result = []
    for case in cases:
        # Get assigned branch info if available
        assigned_branch = None
        if case.branch_id:
            branch = db.query(models.Branch).filter(models.Branch.id == case.branch_id).first()
            if branch:
                assigned_branch = branch.branch_name
        
        result.append({
            "id": case.id,
            "case_id": case.case_id,
            "transaction_id": case.transaction_id,
            "amount": case.amount,
            "payment_mode": case.payment_mode,
            "mobile_number": case.mobile_number,
            "district": case.district,
            "state": case.state,
            "status": case.status.value,
            "source_type": case.source_type.value,
            "assigned_branch": assigned_branch or ("Demo Environment" if case.source_type == SourceType.DEMO else "Unassigned"),
            "created_at": case.created_at.isoformat() if case.created_at else None,
            # ALL bank identity info is INTENTIONALLY EXCLUDED:
            # - payer_bank (victim bank) - HIDDEN
            # - payer_account_number - HIDDEN  
            # - receiver bank - HIDDEN
        })
    
    return {
        "total": len(result),
        "cases": result
    }


@router.get("/{case_id}")
def get_case_detail(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get detailed case information - hides ALL bank identity
    Uses strict branch scoping for security
    """
    # Use strict branch scoping for security
    case = _get_case_with_branch_scope(db, case_id, current_user)
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or not authorized")
    
    # Get assigned branch info
    assigned_branch = None
    if case.branch_id:
        branch = db.query(models.Branch).filter(models.Branch.id == case.branch_id).first()
        if branch:
            assigned_branch = branch.branch_name
    
    # Get evidence items for this case
    evidence_items = db.query(models.Evidence).filter(
        models.Evidence.case_id == case.id
    ).order_by(models.Evidence.uploaded_at.desc()).all()
    
    evidence_data = []
    for ev in evidence_items:
        evidence_data.append({
            "id": ev.id,
            "file_name": ev.file_name,
            "file_type": ev.file_type,
            "file_url": ev.file_url,
            "uploaded_at": ev.uploaded_at.isoformat() if ev.uploaded_at else None,
        })
    
    # Calculate SLA risk level
    # SLA: 24 hours from case creation
    sla_risk = "LOW"
    sla_remaining_hours = 24
    if case.created_at:
        elapsed_hours = (datetime.utcnow() - case.created_at).total_seconds() / 3600
        sla_remaining_hours = max(0, 24 - elapsed_hours)
        
        if sla_remaining_hours > 12:
            sla_risk = "LOW"
        elif sla_remaining_hours >= 3:
            sla_risk = "MEDIUM"
        else:
            sla_risk = "HIGH"
    
    # Get timeline events for this case
    timeline = db.query(models.Timeline).filter(
        models.Timeline.case_id == case.id
    ).order_by(models.Timeline.created_at.desc()).all()
    
    timeline_data = []
    for event in timeline:
        timeline_data.append({
            "id": event.id,
            "event_type": event.event_type.value,
            "description": event.description,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        })
    
    # Get case status from lifecycle field or fallback to enum
    case_status = getattr(case, 'case_status', None) or (case.status.value if case.status else "NEW")
    
    # Return case details - HIDE ALL bank identity
    return {
        "id": case.id,
        "case_id": case.case_id,
        "transaction_id": case.transaction_id,
        "amount": case.amount,
        "payment_mode": case.payment_mode,
        "mobile_number": case.mobile_number,
        "district": case.district,
        "state": case.state,
        "status": case_status,
        "source_type": case.source_type.value,
        "assigned_branch": assigned_branch or ("Demo Environment" if case.source_type == SourceType.DEMO else "Unassigned"),
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "acknowledgement_no": case.acknowledgement_no,
        "i4c_sync_status": getattr(case, 'i4c_sync_status', 'PENDING'),  # Include I4C sync status
        "timeline": timeline_data,
        "evidence": evidence_data,
        "sla_risk": sla_risk,
        "sla_remaining_hours": round(sla_remaining_hours, 1),
        # ALL bank identity fields INTENTIONALLY EXCLUDED:
        # - payer_bank - HIDDEN for security
        # - payer_account_number - HIDDEN for security
    }


@router.post("/{case_id}/assign")
def assign_case(
    case_id: str,
    target_branch_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Admin only: Assign a case to a specific branch
    Creates timeline event for the assignment
    """
    if current_user.role != models.UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Only admins can assign cases")
    
    case = db.query(models.Case).filter(models.Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Verify target branch exists
    branch = db.query(models.Branch).filter(models.Branch.id == target_branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Target branch not found")
    
    # Store previous branch for timeline
    previous_branch_id = case.branch_id
    
    case.branch_id = target_branch_id
    case.status = UnifiedCaseStatus.ASSIGNED
    db.commit()
    
    # Add timeline event for branch assignment
    add_timeline_event(
        db=db,
        case_id=case.id,
        branch_id=target_branch_id,
        event_type=TimelineEventType.BRANCH_ASSIGNED,
        description=f"Case assigned to branch: {branch.branch_name}",
        created_by=current_user.id
    )
    
    return {"message": f"Case {case_id} assigned to branch {branch.branch_name}"}


@router.post("/{case_id}/action")
def case_action(
    case_id: str,
    action: str,  # hold, freeze, confirm, not_related, reconcile
    remarks: str = "",
    hold_amount: float = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Perform actions on a case:
    - hold: Initiate hold on funds → status becomes HOLD_INITIATED
    - freeze: Freeze account → status becomes HOLD_INITIATED
    - confirm: Confirm case is related to bank → status becomes UNDER_REVIEW
    - not_related: Mark as not related → status becomes CLOSED
    - reconcile: Mark as reconciled → status becomes CLOSED
    
    Hold validation: hold_amount must be ≤ case.amount
    Creates timeline event for each action and status change.
    """
    # Use strict branch scoping
    case = _get_case_with_branch_scope(db, case_id, current_user)
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or not authorized")
    
    # Validate hold amount if provided
    if action in ["hold", "freeze"] and hold_amount is not None:
        if hold_amount > case.amount:
            raise HTTPException(
                status_code=400, 
                detail=f"Hold amount cannot exceed exposure amount. Max: ₹{case.amount}"
            )
    
    # Map action to new lifecycle status and timeline event type
    # Lifecycle: NEW → UNDER_REVIEW (confirm) → HOLD_INITIATED (hold/freeze) → CLOSED
    action_map = {
        "hold": ("HOLD_INITIATED", TimelineEventType.HOLD_INITIATED, "Hold initiated on case"),
        "freeze": ("HOLD_INITIATED", TimelineEventType.FREEZE_INITIATED, "Account freeze initiated"),
        "confirm": ("UNDER_REVIEW", TimelineEventType.CONFIRMED_RELATED, "Case confirmed as related"),
        "not_related": ("CLOSED", TimelineEventType.MARKED_NOT_RELATED, "Case marked as not related"),
        "reconcile": ("CLOSED", TimelineEventType.STATUS_CHANGED, "Case reconciled and closed"),
    }
    
    if action not in action_map:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
    
    new_status, event_type, description = action_map[action]
    # Get current status value
    previous_status = case.status.value if case.status else "NEW"
    
    # Update case status using the status enum field
    status_enum_map = {
        "HOLD_INITIATED": UnifiedCaseStatus.HOLD,
        "UNDER_REVIEW": UnifiedCaseStatus.ASSIGNED,
        "CLOSED": UnifiedCaseStatus.CLOSED,
    }
    case.status = status_enum_map.get(new_status, UnifiedCaseStatus.NEW)
    
    # Update I4C sync status to show action has been synced
    case.i4c_sync_status = "SYNCED"
    
    db.commit()
    
    # Add timeline event for the action
    timeline_description = description
    if remarks:
        timeline_description += f" - Remarks: {remarks}"
    if hold_amount:
        timeline_description += f" - Hold Amount: ₹{hold_amount}"
    
    add_timeline_event(
        db=db,
        case_id=case.id,
        branch_id=case.branch_id,
        event_type=event_type,
        description=timeline_description,
        created_by=current_user.id
    )
    
    # Add separate timeline event for status change (use existing enum)
    add_timeline_event(
        db=db,
        case_id=case.id,
        branch_id=case.branch_id,
        event_type=TimelineEventType.STATUS_CHANGED,  # Use existing enum
        description=f"Case status updated from {previous_status} to {new_status}",
        created_by=current_user.id
    )
    
    return {
        "message": f"Action '{action}' performed on case {case_id}",
        "new_status": new_status,
        "previous_status": previous_status
    }


# Admin endpoints for branch management

@router.get("/admin/branches")
def get_branches(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Admin: Get all branches with demo_access status"""
    if current_user.role != models.UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    branches = db.query(models.Branch).all()
    return [
        {
            "id": b.id,
            "branch_name": b.branch_name,
            "city": b.city,
            "state": b.state,
            "demo_access": b.demo_access,
            "is_active": b.is_active,
        }
        for b in branches
    ]


@router.post("/admin/branches/{branch_id}/demo-access")
def toggle_demo_access(
    branch_id: int,
    enable: bool,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Admin: Enable or disable demo dataset access for a branch"""
    if current_user.role != models.UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    branch = db.query(models.Branch).filter(models.Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    branch.demo_access = enable
    db.commit()
    
    return {
        "message": f"Demo access {'enabled' if enable else 'disabled'} for {branch.branch_name}",
        "branch_id": branch_id,
        "demo_access": enable
    }


@router.post("/{case_id}/evidence")
def upload_evidence(
    case_id: str,
    file_name: str,
    file_type: str = "DOCUMENT",  # TRANSACTION_SCREENSHOT, BANK_STATEMENT, CBS_CONFIRMATION, INVESTIGATION_NOTE
    file_url: str = "",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Upload evidence/document for a case.
    Creates timeline entry automatically.
    """
    # Use strict branch scoping
    case = _get_case_with_branch_scope(db, case_id, current_user)
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or not authorized")
    
    # Create evidence record
    evidence = models.Evidence(
        case_id=case.id,
        uploaded_by=current_user.id,
        file_name=file_name,
        file_type=file_type,
        file_url=file_url
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    
    # Add timeline event
    add_timeline_event(
        db=db,
        case_id=case.id,
        branch_id=case.branch_id,
        event_type=TimelineEventType.EVIDENCE_UPLOADED,
        description=f"Investigation document uploaded: {file_name} ({file_type})",
        created_by=current_user.id
    )
    
    return {
        "message": "Evidence uploaded successfully",
        "evidence_id": evidence.id,
        "case_id": case_id,
        "file_name": file_name
    }


@router.get("/{case_id}/evidence")
def get_evidence(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all evidence items for a case.
    """
    # Use strict branch scoping
    case = _get_case_with_branch_scope(db, case_id, current_user)
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or not authorized")
    
    evidence_items = db.query(models.Evidence).filter(
        models.Evidence.case_id == case.id
    ).order_by(models.Evidence.uploaded_at.desc()).all()
    
    return {
        "case_id": case_id,
        "evidence_count": len(evidence_items),
        "evidence": [
            {
                "id": ev.id,
                "file_name": ev.file_name,
                "file_type": ev.file_type,
                "file_url": ev.file_url,
                "uploaded_at": ev.uploaded_at.isoformat() if ev.uploaded_at else None,
            }
            for ev in evidence_items
        ]
    }
