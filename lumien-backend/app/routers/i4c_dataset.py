"""
I4C Demo Dataset Router

This router provides endpoints to access the I4C Simulated Demo Dataset.
It maps the Excel sheets to API responses for the frontend.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
import json

from ..models import models
from ..models.models import get_db
from ..core.security import get_current_user

router = APIRouter(tags=["I4C Dataset"])


def _append_timeline_event(
    db: Session,
    acknowledgement_no: str,
    actor: str,
    step_name: str,
):
    next_step_no = (
        db.query(models.DemoWorkflowTimeline)
        .filter(models.DemoWorkflowTimeline.acknowledgement_no == acknowledgement_no)
        .count()
        + 1
    )
    timeline = models.DemoWorkflowTimeline(
        case_id=acknowledgement_no,
        acknowledgement_no=acknowledgement_no,
        step_no=next_step_no,
        step_name=step_name,
        actor=actor,
        start_time=datetime.utcnow(),
        step_status="COMPLETED",
    )
    db.add(timeline)


def _simulate_i4c_fraud_report_status_update(_: dict) -> dict:
    # Mocked I4C API response.
    return {
        "response_code": "00",
        "message": "Success",
    }


def _build_recipient_bank_filters(bank: "models.Bank"):
    """Build filters for recipient bank (where money was credited to fraudulent accounts)"""
    filters = []
    if getattr(bank, "code", None):
        # Look for incidents where this bank is the payee (recipient)
        filters.append(models.DemoI4CIncident.payee_bank_code == bank.code)
        filters.append(models.DemoI4CIncident.payee_bank_code.ilike(f"%{bank.code}%"))
    if getattr(bank, "name", None):
        filters.append(models.DemoI4CIncident.payee_bank.ilike(f"%{bank.name}%"))
    return filters


def _is_report_for_recipient_bank(report: "models.DemoI4CInboundFraudReport", bank: "models.Bank", db: Session) -> bool:
    """Check if any incident in this report has the bank as recipient (payee)"""
    if bank is None:
        return False
    
    # Get all incidents for this report
    incidents = db.query(models.DemoI4CIncident).filter(
        models.DemoI4CIncident.acknowledgement_no == report.acknowledgement_no
    ).all()
    
    for inc in incidents:
        # Check if this bank is the payee (recipient) for any incident
        if bank.code and inc.payee_bank_code:
            if inc.payee_bank_code == bank.code or bank.code.lower() in inc.payee_bank_code.lower():
                return True
        if bank.name and inc.payee_bank:
            if bank.name.lower() in inc.payee_bank.lower():
                return True
    return False


@router.get("/fraud-reports")
def get_fraud_reports(
    bank_id: Optional[int] = Query(None, description="Filter by recipient bank ID (where money was credited)"),
    branch_id: Optional[int] = Query(None, description="Filter by assigned branch ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get I4C Inbound Fraud Reports (Case Inbox data source)
    Maps to I4C_Inbound_FraudReports sheet
    
    FILTERING LOGIC:
    - For branch users: Shows cases where money was credited to THEIR bank's accounts
    - This is based on payee_bank in the incidents table, not payer_bank
    - Example: HDFC user sees cases where fraudulent money went to HDFC accounts
    """
    # Start with all reports
    query = db.query(models.DemoI4CInboundFraudReport)
    
    # Get user info
    user_roles = [r.name for r in current_user.roles]
    is_admin = "Lumien Super Admin" in user_roles or "Lumien Operations Manager" in user_roles
    
    # For non-admin users, filter by their bank as RECIPIENT (payee)
    if not is_admin and current_user.bank_id:
        bank = db.query(models.Bank).filter(models.Bank.id == current_user.bank_id).first()
        branch = None
        if current_user.branch_id:
            branch = db.query(models.Branch).filter(models.Branch.id == current_user.branch_id).first()
        
        if bank:
            # Find all incidents where this bank is the recipient (payee)
            incident_filters = [
                models.DemoI4CIncident.payee_bank_code == bank.code,
                models.DemoI4CIncident.payee_bank_code.ilike(f"%{bank.code}%"),
                models.DemoI4CIncident.payee_bank.ilike(f"%{bank.name}%")
            ]
            
            # If user has a branch, also filter by branch state
            if branch and branch.state:
                # Filter reports by branch state
                state_filter = models.DemoI4CInboundFraudReport.state.ilike(f"%{branch.state}%")
                query = query.filter(state_filter)
            
            recipient_incidents = db.query(models.DemoI4CIncident.acknowledgement_no).filter(
                or_(*incident_filters)
            ).distinct()
            
            # Get the acknowledgement numbers
            ack_nos = [row[0] for row in recipient_incidents.all()]
            
            if ack_nos:
                query = query.filter(models.DemoI4CInboundFraudReport.acknowledgement_no.in_(ack_nos))
            else:
                # No cases for this bank as recipient
                query = query.filter(False)  # Return empty
    
    # Admin can filter by specific bank as recipient
    if bank_id and is_admin:
        bank = db.query(models.Bank).filter(models.Bank.id == bank_id).first()
        if bank:
            recipient_incidents = db.query(models.DemoI4CIncident.acknowledgement_no).filter(
                or_(
                    models.DemoI4CIncident.payee_bank_code == bank.code,
                    models.DemoI4CIncident.payee_bank_code.ilike(f"%{bank.code}%"),
                    models.DemoI4CIncident.payee_bank.ilike(f"%{bank.name}%")
                )
            ).distinct()
            ack_nos = [row[0] for row in recipient_incidents.all()]
            if ack_nos:
                query = query.filter(models.DemoI4CInboundFraudReport.acknowledgement_no.in_(ack_nos))
            else:
                query = query.filter(False)
    
    # Filter by assigned branch (for branch-specific users)
    if branch_id:
        # Check workflow for branch assignment
        branch_workflows = db.query(models.DemoBankCaseWorkflow.acknowledgement_no).filter(
            models.DemoBankCaseWorkflow.assigned_branch_id == str(branch_id)
        ).distinct()
        ack_nos = [row[0] for row in branch_workflows.all()]
        if ack_nos:
            query = query.filter(models.DemoI4CInboundFraudReport.acknowledgement_no.in_(ack_nos))
    
    reports = query.all()
    
    # DEBUG: Log what we found
    print(f"DEBUG: Found {len(reports)} reports for user_bank_id={current_user.bank_id}, is_admin={is_admin}")
    if reports:
        print(f"DEBUG: First report payer_bank={reports[0].payer_bank}")
        # Show recipient banks for first report
        first_incidents = db.query(models.DemoI4CIncident).filter(
            models.DemoI4CIncident.acknowledgement_no == reports[0].acknowledgement_no
        ).all()
        for inc in first_incidents[:3]:
            print(f"DEBUG: Incident payee_bank={inc.payee_bank}, payee_bank_code={inc.payee_bank_code}")
    
    # Get workflow statuses for each report
    result = []
    for report in reports:
        # Get workflow status
        workflow = db.query(models.DemoBankCaseWorkflow).filter(
            models.DemoBankCaseWorkflow.acknowledgement_no == report.acknowledgement_no
        ).first()
        
        status_value = workflow.current_state if workflow else "ROUTED"
        
        # DEBUG: Log status comparison
        if status:
            print(f"DEBUG: report={report.acknowledgement_no}, status_filter={status.upper()}, status_value={status_value.upper()}, match={status.upper() in status_value.upper()}")

        if status and status_value:
            # Dataset workflow values may be more specific than UI filter values
            # (e.g. ROUTED_TO_BANK should match ROUTED)
            if status.upper() not in status_value.upper():
                continue
        
        result.append({
            "id": report.id,
            "acknowledgement_no": report.acknowledgement_no,
            "case_id": report.acknowledgement_no,  # Map to case_id for frontend
            "fraud_type": report.sub_category,
            "amount": report.total_disputed_amount,
            "victim_name": report.requestor,
            "victim_mobile": report.payer_mobile_number,
            "payer_bank": report.payer_bank,
            "payer_bank_code": report.payer_bank_code,
            "mode_of_payment": report.mode_of_payment,
            "state": report.state,
            "district": report.district,
            "received_at": report.received_at.isoformat() if report.received_at else None,
            "incident_count": report.incident_count,
            "status": status_value,
            "bank_ack_response_code": report.bank_ack_response_code,
            "bank_job_id": report.bank_job_id,
        })
    
    return result


@router.get("/fraud-reports/{acknowledgement_no}")
def get_fraud_report_detail(
    acknowledgement_no: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get detailed fraud report with incidents (transactions) and timeline
    """
    # Support both acknowledgement number and numeric internal id in the URL.
    # IMPORTANT: acknowledgement_no values can be all digits and much larger than a Postgres INTEGER.
    # So for long numeric strings, query by acknowledgement_no first to avoid integer overflow.
    report_query = db.query(models.DemoI4CInboundFraudReport)
    if acknowledgement_no.isdigit():
        if len(acknowledgement_no) > 10:
            report = report_query.filter(
                models.DemoI4CInboundFraudReport.acknowledgement_no == acknowledgement_no
            ).first()
        else:
            report = None

        if not report:
            # It could still be an internal numeric id.
            try:
                report = report_query.filter(models.DemoI4CInboundFraudReport.id == int(acknowledgement_no)).first()
            except Exception:
                report = None

        if not report:
            report = report_query.filter(
                models.DemoI4CInboundFraudReport.acknowledgement_no == acknowledgement_no
            ).first()
    else:
        report = report_query.filter(models.DemoI4CInboundFraudReport.acknowledgement_no == acknowledgement_no).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Normalize acknowledgement number for downstream queries
    ack_no = report.acknowledgement_no

    # Check authorization
    user_roles = [r.name for r in current_user.roles]
    is_admin = "Lumien Super Admin" in user_roles or "Lumien Operations Manager" in user_roles
    # Check authorization - check if bank is recipient (payee) in any incident
    if not is_admin and current_user.bank_id:
        bank = db.query(models.Bank).filter(models.Bank.id == current_user.bank_id).first()
        if bank and not _is_report_for_recipient_bank(report, bank, db):
            raise HTTPException(status_code=403, detail="Not authorized to view this report")
    
    # Get incidents (transactions) for this report
    incidents = db.query(models.DemoI4CIncident).filter(
        models.DemoI4CIncident.acknowledgement_no == ack_no
    ).all()
    
    # Get workflow
    workflow = db.query(models.DemoBankCaseWorkflow).filter(
        models.DemoBankCaseWorkflow.acknowledgement_no == ack_no
    ).first()
    
    # Get timeline events
    timeline = db.query(models.DemoWorkflowTimeline).filter(
        models.DemoWorkflowTimeline.acknowledgement_no == ack_no
    ).order_by(models.DemoWorkflowTimeline.step_no).all()
    
    # Get hold actions
    hold_actions = db.query(models.DemoBankHoldAction).filter(
        models.DemoBankHoldAction.acknowledgement_no == ack_no
    ).all()
    
    # Get status update requests + latest I4C response to compute sync status
    status_requests = db.query(models.DemoBankStatusUpdateRequest).filter(
        models.DemoBankStatusUpdateRequest.acknowledgement_no == ack_no
    ).all()

    latest_request_id = None
    if status_requests:
        latest_request_id = max(
            status_requests,
            key=lambda r: (r.sent_at or datetime.min, r.id or 0),
        ).request_id

    latest_i4c_response = None
    if latest_request_id:
        latest_i4c_response = (
            db.query(models.DemoI4CStatusUpdateResponse)
            .filter(models.DemoI4CStatusUpdateResponse.request_id == latest_request_id)
            .order_by(models.DemoI4CStatusUpdateResponse.id.desc())
            .first()
        )

    i4c_sync_status = "PENDING"
    if latest_i4c_response and latest_i4c_response.i4c_response_code:
        i4c_sync_status = "SYNCED" if latest_i4c_response.i4c_response_code == "00" else "FAILED"
    
    return {
        "report": {
            "id": report.id,
            "acknowledgement_no": report.acknowledgement_no,
            "complaint_id": report.acknowledgement_no,  # For frontend compatibility
            "fraud_type": report.sub_category,
            "amount": report.total_disputed_amount,
            "victim_name": report.requestor,
            "victim_mobile": report.payer_mobile_number,
            "payer_bank": report.payer_bank,
            "payer_bank_code": report.payer_bank_code,
            "mode_of_payment": report.mode_of_payment,
            "state": report.state,
            "district": report.district,
            "received_at": report.received_at.isoformat() if report.received_at else None,
            "incident_count": report.incident_count,
            "status": workflow.current_state if workflow else "ROUTED",
        },
        "incidents": [
            {
                "id": inc.id,
                "incident_id": inc.incident_id,
                "rrn": inc.rrn,
                "amount": inc.amount,
                "disputed_amount": inc.disputed_amount,
                "transaction_date": inc.transaction_date.isoformat() if inc.transaction_date else None,
                "transaction_time": inc.transaction_time,
                "layer": inc.layer,
                "payee_bank": inc.payee_bank,
                "payee_ifsc_code": inc.payee_ifsc_code,
                "payee_account_number": inc.payee_account_number,
            }
            for inc in incidents
        ],
        "transactions": [  # Alias for incidents
            {
                "id": inc.id,
                "rrn": inc.rrn,
                "amount": inc.amount,
                "disputed_amount": inc.disputed_amount,
                "transaction_date": inc.transaction_date.isoformat() if inc.transaction_date else None,
                "transaction_time": inc.transaction_time,
                "layer": inc.layer,
                "payee_bank": inc.payee_bank,
            }
            for inc in incidents
        ],
        "workflow": {
            "case_id": workflow.case_id if workflow else None,
            "job_id": workflow.job_id if workflow else None,
            "current_state": workflow.current_state if workflow else "ROUTED",
            "assigned_queue": workflow.assigned_queue if workflow else None,
            "priority": workflow.priority if workflow else None,
            "created_at": workflow.created_at.isoformat() if workflow and workflow.created_at else None,
        },
        "timeline": [
            {
                "step_no": t.step_no,
                "step_name": t.step_name,
                "actor": t.actor,
                "start_time": t.start_time.isoformat() if t.start_time else None,
                "end_time": t.end_time.isoformat() if t.end_time else None,
                "step_status": t.step_status,
                "sla_target_minutes": t.sla_target_minutes,
                "actual_minutes": t.actual_minutes,
                "sla_breached": t.sla_breached,
            }
            for t in timeline
        ],
        "hold_actions": [
            {
                "action_id": ha.action_id,
                "action_type": ha.action_type,
                "action_time": ha.action_time.isoformat() if ha.action_time else None,
                "requested_amount": ha.requested_amount,
                "action_amount": ha.action_amount,
                "held_amount": ha.held_amount,
                "hold_reference": ha.hold_reference,
                "outcome": ha.outcome,
                "remarks": ha.remarks,
            }
            for ha in hold_actions
        ],
        "status_updates": [
            {
                "request_id": sr.request_id,
                "sent_at": sr.sent_at.isoformat() if sr.sent_at else None,
                "transaction_count": sr.transaction_count,
            }
            for sr in status_requests
        ],
        "i4c_sync_status": i4c_sync_status,
        "i4c_status_update_response": {
            "request_id": latest_i4c_response.request_id,
            "response_code": latest_i4c_response.i4c_response_code,
            "response_message": latest_i4c_response.i4c_message,
            "timestamp": latest_i4c_response.received_at.isoformat() if latest_i4c_response.received_at else None,
        }
        if latest_i4c_response
        else None,
    }


@router.get("/incidents")
def get_incidents(
    acknowledgement_no: Optional[str] = Query(None, description="Filter by acknowledgement number"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get I4C Incidents (transactions data source)
    Maps to I4C_Incidents sheet
    """
    query = db.query(models.DemoI4CIncident)
    
    if acknowledgement_no:
        query = query.filter(models.DemoI4CIncident.acknowledgement_no == acknowledgement_no)
    
    incidents = query.all()
    
    return [
        {
            "id": inc.id,
            "acknowledgement_no": inc.acknowledgement_no,
            "incident_id": inc.incident_id,
            "rrn": inc.rrn,
            "amount": inc.amount,
            "disputed_amount": inc.disputed_amount,
            "transaction_date": inc.transaction_date.isoformat() if inc.transaction_date else None,
            "transaction_time": inc.transaction_time,
            "layer": inc.layer,
            "payee_bank": inc.payee_bank,
            "payee_ifsc_code": inc.payee_ifsc_code,
            "payee_account_number": inc.payee_account_number,
        }
        for inc in incidents
    ]


@router.get("/workflow/{acknowledgement_no}")
def get_case_workflow(
    acknowledgement_no: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get case workflow status
    Maps to Bank_Case_Workflow sheet
    """
    workflow = db.query(models.DemoBankCaseWorkflow).filter(
        models.DemoBankCaseWorkflow.acknowledgement_no == acknowledgement_no
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {
        "case_id": workflow.case_id,
        "acknowledgement_no": workflow.acknowledgement_no,
        "job_id": workflow.job_id,
        "current_state": workflow.current_state,
        "assigned_queue": workflow.assigned_queue,
        "assigned_branch_id": workflow.assigned_branch_id,
        "priority": workflow.priority,
        "scenario": workflow.scenario,
        "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
    }


@router.get("/timeline/{acknowledgement_no}")
def get_workflow_timeline(
    acknowledgement_no: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get workflow timeline events
    Maps to Workflow_Timeline sheet
    """
    timeline = db.query(models.DemoWorkflowTimeline).filter(
        models.DemoWorkflowTimeline.acknowledgement_no == acknowledgement_no
    ).order_by(models.DemoWorkflowTimeline.step_no).all()
    
    return [
        {
            "step_no": t.step_no,
            "step_name": t.step_name,
            "actor": t.actor,
            "start_time": t.start_time.isoformat() if t.start_time else None,
            "end_time": t.end_time.isoformat() if t.end_time else None,
            "step_status": t.step_status,
            "sla_target_minutes": t.sla_target_minutes,
            "actual_minutes": t.actual_minutes,
            "sla_breached": t.sla_breached,
        }
        for t in timeline
    ]


@router.get("/hold-actions/{acknowledgement_no}")
def get_hold_actions(
    acknowledgement_no: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get hold actions for a case
    Maps to Bank_Hold_Actions sheet
    """
    actions = db.query(models.DemoBankHoldAction).filter(
        models.DemoBankHoldAction.acknowledgement_no == acknowledgement_no
    ).all()
    
    return [
        {
            "action_id": a.action_id,
            "case_id": a.case_id,
            "incident_id": a.incident_id,
            "action_type": a.action_type,
            "action_time": a.action_time.isoformat() if a.action_time else None,
            "requested_amount": a.requested_amount,
            "action_amount": a.action_amount,
            "held_amount": a.held_amount,
            "hold_reference": a.hold_reference,
            "negative_lien_flag": a.negative_lien_flag,
            "outcome": a.outcome,
            "remarks": a.remarks,
        }
        for a in actions
    ]


@router.post("/status-updates")
def create_status_update(
    status_data: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new status update request for I4C
    Maps to Bank_StatusUpdate_Request table
    """
    acknowledgement_no = status_data.get("acknowledgement_no")
    status_code = status_data.get("status_code")
    response_code = status_data.get("response_code", "RELATED")
    remarks = status_data.get("remarks", "")

    if not acknowledgement_no:
        raise HTTPException(status_code=400, detail="acknowledgement_no is required")
    
    # Generate request ID
    request_id = f"REQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{acknowledgement_no[-4:]}"
    
    # Load report/workflow/incidents for payload construction
    report = db.query(models.DemoI4CInboundFraudReport).filter(
        models.DemoI4CInboundFraudReport.acknowledgement_no == acknowledgement_no
    ).first()

    workflow = db.query(models.DemoBankCaseWorkflow).filter(
        models.DemoBankCaseWorkflow.acknowledgement_no == acknowledgement_no
    ).first()

    incidents = db.query(models.DemoI4CIncident).filter(
        models.DemoI4CIncident.acknowledgement_no == acknowledgement_no
    ).all()

    job_id = status_data.get("job_id") or (workflow.job_id if workflow else None) or (report.bank_job_id if report else None)

    # Default status_code based on bank action
    if not status_code:
        if response_code == "RELATED":
            status_code = "RELATED"
        elif response_code == "NOT_RELATED":
            status_code = "NOT_RELATED"
        elif response_code == "ACTION_INITIATED":
            status_code = "HOLD_INITIATED"
        else:
            status_code = response_code
    
    actor = current_user.email if current_user else "system"

    # Create status update request row (represents Bank_StatusUpdate_Request sheet)
    status_request = models.DemoBankStatusUpdateRequest(
        request_id=request_id,
        acknowledgement_no=acknowledgement_no,
        job_id=job_id,
        sent_at=datetime.utcnow(),
        content_type="application/json",
        authorization_type="Bearer",
        transaction_count=len(incidents),
    )
    db.add(status_request)

    # Create txn detail rows (represents Bank_StatusUpdate_TxnDetails sheet)
    txn_details = []
    for inc in incidents:
        detail = models.DemoBankStatusUpdateTxnDetail(
            request_id=request_id,
            acknowledgement_no=acknowledgement_no,
            job_id=job_id,
            incident_id=inc.incident_id,
            root_rrn_transaction_id=inc.rrn,
            root_account_number=(report.payer_account_number if report else None),
            amount=inc.amount,
            transaction_datetime=inc.transaction_date,
            disputed_amount=inc.disputed_amount,
            status_code=status_code,
            remarks=remarks,
            root_ifsc_code=None,
            root_effective_balance=None,
        )
        db.add(detail)
        txn_details.append(
            {
                "txn_type": (report.transaction_type if report else None),
                "rrn_transaction_id": inc.rrn,
                "amount": inc.amount,
                "root_account_number": (report.payer_account_number if report else None),
                "root_ifsc_code": None,
                "root_effective_balance": None,
                "status_code": status_code,
                "remarks": remarks,
            }
        )

    payload = {
        "acknowledgement_no": acknowledgement_no,
        "job_id": job_id,
        "txn_details": txn_details,
        "status_code": status_code,
        "remarks": remarks,
    }

    # Store payload in the request row (encrypted field is used as a blob store in demo)
    status_request.payload_encrypted = json.dumps(payload)

    _append_timeline_event(db, acknowledgement_no, actor, "Status Sent to I4C")

    # Simulate I4C API call
    i4c_result = _simulate_i4c_fraud_report_status_update(payload)
    i4c_response_code = i4c_result.get("response_code")
    i4c_message = i4c_result.get("message")

    # Store I4C response (represents I4C_StatusUpdate_Response sheet)
    response = models.DemoI4CStatusUpdateResponse(
        request_id=request_id,
        i4c_response_code=i4c_response_code,
        i4c_message=i4c_message,
        received_at=datetime.utcnow(),
        error_flag=None if i4c_response_code == "00" else "Y",
    )
    db.add(response)

    _append_timeline_event(db, acknowledgement_no, actor, "I4C Acknowledgement Received")
    
    if workflow:
        if response_code == "RELATED":
            workflow.current_state = "RELATED_CONFIRMED"
        elif response_code == "NOT_RELATED":
            workflow.current_state = "NOT_RELATED"
        elif response_code == "ACTION_INITIATED":
            workflow.current_state = "HOLD_INITIATED"
    
    # Add bank decision timeline event
    step_name_map = {
        "RELATED": "Related Confirmed",
        "NOT_RELATED": "Marked Not Related",
        "ACTION_INITIATED": "Hold Initiated",
    }

    _append_timeline_event(db, acknowledgement_no, actor, step_name_map.get(response_code, "Bank Response"))
    
    db.commit()
    
    # Query all status updates for this case to build the history
    status_requests = db.query(models.DemoBankStatusUpdateRequest).filter(
        models.DemoBankStatusUpdateRequest.acknowledgement_no == acknowledgement_no
    ).order_by(models.DemoBankStatusUpdateRequest.sent_at.desc()).all()
    
    # The response we just created is the latest one
    latest_i4c_response = response
    
    # Build response cycle data
    response_cycle = {
        "request_id": request_id,
        "acknowledgement_no": acknowledgement_no,
        "job_id": job_id,
        "status_code": status_code,
        "response_code": response_code,
        "sent_at": status_request.sent_at.isoformat() if status_request.sent_at else None,
        "received_at": response.received_at.isoformat() if response.received_at else None,
        "transaction_count": len(incidents),
    }
    
    # Build callback response data
    callback_response = {
        "request_id": latest_i4c_response.request_id,
        "response_code": i4c_response_code,
        "response_message": i4c_message,
        "received_at": latest_i4c_response.received_at.isoformat() if latest_i4c_response.received_at else None,
        "error_flag": latest_i4c_response.error_flag,
    }
    
    # Build status payload (what was sent to I4C)
    status_payload = {
        "endpoint": "/banking/FraudReportStatusUpdate",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer {token}"
        },
        "body": payload,
    }
    
    # Build richer status updates array
    richer_status_updates = []
    for sr in status_requests:
        # Find corresponding response
        sr_response = None
        for resp in db.query(models.DemoI4CStatusUpdateResponse).filter(
            models.DemoI4CStatusUpdateResponse.request_id == sr.request_id
        ).all():
            sr_response = resp
            break
        
        richer_status_updates.append({
            "request_id": sr.request_id,
            "sent_at": sr.sent_at.isoformat() if sr.sent_at else None,
            "transaction_count": sr.transaction_count,
            "i4c_response_code": sr_response.i4c_response_code if sr_response else None,
            "i4c_response_message": sr_response.i4c_message if sr_response else None,
            "received_at": sr_response.received_at.isoformat() if sr_response and sr_response.received_at else None,
        })
    
    return {
        "request_id": request_id,
        "status": workflow.current_state if workflow else response_code,
        "i4c_sync": {
            "status": "SYNCED" if i4c_response_code == "00" else "FAILED",
            "response_code": i4c_response_code,
            "response_message": i4c_message,
        },
        "response_cycle": response_cycle,
        "callback_response": callback_response,
        "status_payload": status_payload,
        "status_updates": richer_status_updates,
        "message": f"Status update recorded and workflow updated to {workflow.current_state if workflow else response_code}",
    }


@router.post("/hold-actions")
def create_hold_action(
    action_data: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new hold action and update workflow
    """
    acknowledgement_no = action_data.get("acknowledgement_no")
    incident_id = action_data.get("incident_id")
    action_type = action_data.get("action_type", "HOLD")
    requested_amount = action_data.get("requested_amount", 0)
    
    # Generate action ID
    action_id = f"ACT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{acknowledgement_no[-4:]}"
    
    # Create hold action record
    action = models.DemoBankHoldAction(
        action_id=action_id,
        case_id=acknowledgement_no,
        acknowledgement_no=acknowledgement_no,
        incident_id=incident_id,
        action_type=action_type,
        action_time=datetime.utcnow(),
        requested_amount=requested_amount,
        action_amount=requested_amount,
        outcome="PENDING",
        remarks=action_data.get("remarks", ""),
    )
    db.add(action)
    
    # Update workflow status
    workflow = db.query(models.DemoBankCaseWorkflow).filter(
        models.DemoBankCaseWorkflow.acknowledgement_no == acknowledgement_no
    ).first()
    
    if workflow:
        workflow.current_state = "HOLD_INITIATED"
    
    # Add timeline event
    timeline = models.DemoWorkflowTimeline(
        case_id=acknowledgement_no,
        acknowledgement_no=acknowledgement_no,
        step_no=db.query(models.DemoWorkflowTimeline).filter(
            models.DemoWorkflowTimeline.acknowledgement_no == acknowledgement_no
        ).count() + 1,
        step_name="Hold Initiated",
        actor=current_user.email if current_user else "system",
        start_time=datetime.utcnow(),
        step_status="COMPLETED",
    )
    db.add(timeline)
    
    db.commit()
    
    return {
        "action_id": action_id,
        "status": "HOLD_INITIATED",
        "message": "Hold action recorded and workflow updated",
    }


@router.get("/status-codes")
def get_status_codes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all status codes for UI badge mapping
    Maps to Meta_StatusCodes sheet
    """
    codes = db.query(models.MetaStatusCode).all()
    
    return [
        {
            "status_code": c.status_code,
            "status_label": c.status_label,
            "meaning": c.meaning,
            "owner": c.owner,
            "demo_example_usage": c.demo_example_usage,
        }
        for c in codes
    ]


@router.get("/bank-master")
def get_bank_master(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get bank master data
    Maps to Meta_BankMaster sheet
    """
    banks = db.query(models.Bank).filter(models.Bank.is_active == True).all()
    
    return [
        {
            "id": b.id,
            "bank_name": b.name,
            "bank_code": b.code,
        }
        for b in banks
    ]
