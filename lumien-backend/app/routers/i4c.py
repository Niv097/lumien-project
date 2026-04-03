from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from ..models import models
from ..models.models import get_db
from ..services.enrichment import enrichment_service
from ..services.workflow import workflow_service
from ..core.security import get_current_user, RoleChecker
from ..core.i4c_encryption import get_i4c_encryption
import uuid
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()

# In-memory token storage for I4C sessions (use Redis in production)
i4c_sessions = {}

# Restricted to Lumien Ops and Admins
ops_checker = RoleChecker(["Lumien Super Admin", "Lumien Operations Manager"])


def generate_job_id() -> str:
    """Generate unique job ID for I4C"""
    return f"BANKS-{uuid.uuid4().hex[:12].upper()}"


def success_response(data: dict) -> dict:
    """Standard I4C success response format"""
    return {
        "data": {
            "meta": {
                "response_code": "00",
                "response_message": "Success"
            },
            "data": data
        }
    }


def error_response(code: str, message: str) -> dict:
    """Standard I4C error response format"""
    return {
        "data": {
            "meta": {
                "response_code": code,
                "response_message": message
            },
            "data": {}
        }
    }


@router.post("/ingest")
def ingest_complaint(
    data: dict, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(ops_checker)
):
    # 1. Check if already exists
    existing = db.query(models.Complaint).filter(models.Complaint.complaint_id == data["complaint_id"]).first()
    if existing:
        return {"status": "skipped", "reason": "duplicate", "complaint_id": data["complaint_id"]}

    # 2. Basic Ingestion
    new_case = models.Complaint(
        complaint_id=data["complaint_id"],
        victim_name=data.get("victim_name", "Unknown"),
        victim_mobile=data.get("victim_mobile"),
        incident_date=datetime.fromisoformat(data["incident_date"]),
        fraud_type=data.get("fraud_type", "Cyber Fraud"),
        amount=data["amount"],
        ifsc_signal=data.get("ifsc"),
        status=models.CaseStatus.INGESTED
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    # 3. Enrichment & Integrated Identification
    enrichment_data = enrichment_service.enrich_case(data)
    
    # Identify Bank if found
    bank = None
    if enrichment_data["target_bank"]:
        bank = db.query(models.Bank).filter(models.Bank.code == enrichment_data["target_bank"]).first()

    # Create Enrichment Result
    enrichment_record = models.EnrichmentResult(
        complaint_id=new_case.id,
        target_bank_id=bank.id if bank else None,
        confidence_score=enrichment_data["confidence"],
        signals=str(enrichment_data["signals"]),
        validation_method="DETERMINISTIC_MAPPING"
    )
    db.add(enrichment_record)
    
    # 4. AUTO-ROUTING (The "Direct to Bank" capability)
    final_status = models.CaseStatus.ENRICHED
    if bank:
        final_status = models.CaseStatus.ROUTED
        # Create Routing Log
        log = models.RoutingLog(
            complaint_id=new_case.id,
            bank_id=bank.id,
            status="SUCCESS",
            request_id=f"AUTO-FID-{uuid.uuid4().hex[:8].upper()}",
            routed_at=datetime.utcnow()
        )
        db.add(log)

    # Update Status
    new_case.status = final_status

    # 5. Initialize SLA Tracking (24 hour deadline)
    sla = models.SLATracking(
        complaint_id=new_case.id,
        start_time=datetime.utcnow(),
        deadline=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(sla)
    
    # Audit ingestion and auto-route
    audit = models.AuditLog(
        user_id=current_user.id,
        action="AUTO_INGEST_AND_ROUTE" if bank else "INGEST_DATA",
        resource="complaint",
        resource_id=str(new_case.id),
        new_value=final_status
    )
    db.add(audit)
    
    db.commit()

    return {
        "status": "success",
        "case_id": new_case.id,
        "complaint_id": new_case.complaint_id,
        "confidence": enrichment_data["confidence"],
        "target_bank": bank.name if bank else "UNIDENTIFIED",
        "workflow": "AUTO_ROUTED" if bank else "MANUAL_PENDING"
    }


# ============== I4C MHA INTEGRATION APIS ==============

@router.post("/authenticate")
async def i4c_authenticate(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    I4C Authentication API
    Decrypts credentials and returns JWT token
    """
    try:
        body = await request.body()
        encrypted_payload = body.decode('utf-8')
        
        # Log incoming request
        inbox_log = models.APIInbox(
            correlation_id=str(uuid.uuid4()),
            api_name="authenticate",
            source_ip=request.client.host if request.client else None,
            request_headers=str(dict(request.headers)),
            request_body_encrypted=encrypted_payload,
            received_at=datetime.utcnow()
        )
        db.add(inbox_log)
        
        # Decrypt payload
        encryption = get_i4c_encryption()
        decrypted = encryption.decrypt(encrypted_payload)
        inbox_log.request_body_decrypted = decrypted
        
        # Parse credentials
        try:
            creds = json.loads(decrypted)
            email = creds.get("email")
            password = creds.get("password")
        except json.JSONDecodeError:
            inbox_log.response_code = "400"
            inbox_log.response_body = json.dumps(error_response("400", "Invalid JSON format"))
            inbox_log.processed_at = datetime.utcnow()
            db.commit()
            return error_response("400", "Invalid JSON format")
        
        # Validate credentials
        if email != "i4c@mha.gov.in" or password != "I4C@2024":
            inbox_log.response_code = "401"
            inbox_log.response_body = json.dumps(error_response("401", "Invalid credentials"))
            inbox_log.processed_at = datetime.utcnow()
            db.commit()
            return error_response("401", "Invalid credentials")
        
        # Generate token
        token = hashlib.sha256(f"{email}{uuid.uuid4()}{datetime.utcnow()}".encode()).hexdigest()
        i4c_sessions[token] = {
            "email": email,
            "created_at": datetime.utcnow()
        }
        
        response_data = success_response({"token": token, "expires_in": 3600})
        
        inbox_log.response_code = "00"
        inbox_log.response_body = json.dumps(response_data)
        inbox_log.processed_at = datetime.utcnow()
        db.commit()
        
        return response_data
        
    except Exception as e:
        db.rollback()
        return error_response("500", str(e))


@router.post("/transaction-fraud")
async def receive_fraud_report(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Fraud Report API - Receive fraud reports from I4C
    """
    try:
        if not authorization or not authorization.startswith("Bearer "):
            return error_response("401", "Missing or invalid authorization header")
        
        token = authorization.replace("Bearer ", "")
        if token not in i4c_sessions:
            return error_response("401", "Invalid or expired token")
        
        body = await request.body()
        encrypted_payload = body.decode('utf-8')
        
        inbox_log = models.APIInbox(
            correlation_id=str(uuid.uuid4()),
            api_name="fraud-report",
            source_ip=request.client.host if request.client else None,
            request_headers=str(dict(request.headers)),
            request_body_encrypted=encrypted_payload[:500],
            received_at=datetime.utcnow()
        )
        db.add(inbox_log)
        
        # Decrypt payload
        try:
            encryption = get_i4c_encryption()
            decrypted = encryption.decrypt(encrypted_payload)
            inbox_log.request_body_decrypted = decrypted[:1000]
        except Exception as e:
            inbox_log.response_code = "400"
            inbox_log.response_body = json.dumps(error_response("400", f"Decryption failed: {str(e)}"))
            inbox_log.validation_errors = str(e)
            inbox_log.processed_at = datetime.utcnow()
            db.commit()
            return error_response("400", f"Decryption failed: {str(e)}")
        
        # Parse fraud report
        try:
            report_data = json.loads(decrypted)
        except json.JSONDecodeError as e:
            inbox_log.response_code = "400"
            inbox_log.response_body = json.dumps(error_response("400", "Invalid JSON format"))
            inbox_log.validation_errors = str(e)
            inbox_log.processed_at = datetime.utcnow()
            db.commit()
            return error_response("400", "Invalid JSON format")
        
        acknowledgement_no = report_data.get("acknowledgement_no")
        job_id = generate_job_id()
        
        instrument = report_data.get("instrument", {})
        incidents = report_data.get("incidents", [])
        
        fraud_report = models.I4CFraudReport(
            acknowledgement_no=acknowledgement_no,
            job_id=job_id,
            sub_category=report_data.get("sub_category", "UNKNOWN"),
            requestor=instrument.get("requestor", "I4C-MHA"),
            payer_bank=instrument.get("payer_bank", ""),
            payer_bank_code=instrument.get("payer_bank_code", ""),
            mode_of_payment=instrument.get("mode_of_payment", ""),
            payer_mobile_number=instrument.get("payer_mobile_number", ""),
            payer_account_number=instrument.get("payer_account_number", ""),
            payer_state=instrument.get("payer_state"),
            payer_district=instrument.get("payer_district"),
            transaction_type=instrument.get("transaction_type"),
            payer_wallet=instrument.get("payer_wallet"),
            payer_email=instrument.get("payer_email"),
            payer_pan=instrument.get("payer_pan"),
            payer_ifsc=instrument.get("payer_ifsc"),
            status="NEW",
            received_at=datetime.utcnow()
        )
        db.add(fraud_report)
        db.flush()
        
        # Create transaction records
        for incident in incidents:
            transaction = models.I4CTransaction(
                fraud_report_id=fraud_report.id,
                amount=incident.get("amount", 0),
                rrn=incident.get("rrn", ""),
                transaction_date=incident.get("transaction_date", datetime.utcnow()),
                transaction_time=incident.get("transaction_time"),
                disputed_amount=incident.get("disputed_amount", 0),
                layer=incident.get("layer", 0),
                payee_bank=incident.get("payee_bank"),
                payee_bank_code=incident.get("payee_bank_code"),
                payee_account_number=incident.get("payee_account_number"),
                payee_phone=incident.get("payee_phone"),
                payee_email=incident.get("payee_email"),
                payee_pan=incident.get("payee_pan"),
                payee_ifsc=incident.get("payee_ifsc"),
                root_account_number=incident.get("root_account_number"),
                root_rrn=incident.get("root_rrn"),
                root_bankid=incident.get("root_bankid"),
                root_effective_balance=incident.get("root_effective_balance", 0),
                root_ifsc_code=incident.get("root_ifsc_code"),
                status_code="NEW"
            )
            db.add(transaction)
        
        response_data = success_response({
            "acknowledgement_no": acknowledgement_no,
            "job_id": job_id
        })
        
        inbox_log.response_code = "00"
        inbox_log.response_body = json.dumps(response_data)
        inbox_log.processed_at = datetime.utcnow()
        db.commit()
        
        return response_data
        
    except Exception as e:
        db.rollback()
        return error_response("500", str(e))


@router.post("/banking/FraudReportStatusUpdate")
async def send_status_update(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Status Update API - Send investigation results to I4C
    """
    try:
        if not authorization or not authorization.startswith("Bearer "):
            return error_response("401", "Missing or invalid authorization header")
        
        token = authorization.replace("Bearer ", "")
        if token not in i4c_sessions:
            return error_response("401", "Invalid or expired token")
        
        body = await request.body()
        payload = body.decode('utf-8')
        
        # Parse status update
        try:
            if payload.startswith('{'):
                update_data = json.loads(payload)
            else:
                encryption = get_i4c_encryption()
                decrypted = encryption.decrypt(payload)
                update_data = json.loads(decrypted)
        except Exception as e:
            return error_response("400", f"Failed to parse request: {str(e)}")
        
        # Log to outbox
        outbox_log = models.APIOutbox(
            correlation_id=str(uuid.uuid4()),
            api_name="status-update",
            endpoint_url="/banking/FraudReportStatusUpdate",
            request_headers=str(dict(request.headers)),
            request_body=json.dumps(update_data)[:2000],
            status="SENT",
            sent_at=datetime.utcnow()
        )
        db.add(outbox_log)
        
        acknowledgement_no = update_data.get("acknowledgement_no")
        job_id = update_data.get("job_id")
        
        # Process each transaction update
        for txn in update_data.get("transactions", []):
            status_update = models.I4CStatusUpdate(
                acknowledgement_no=acknowledgement_no,
                job_id=job_id,
                txn_type=txn.get("txn_type", ""),
                txn_type_id=txn.get("txn_type_id", ""),
                rrn_transaction_id=txn.get("rrn_transaction_id", ""),
                payee_bank=txn.get("payee_bank"),
                payee_bank_code=txn.get("payee_bank_code"),
                payee_account_number=txn.get("payee_account_number"),
                amount=txn.get("amount"),
                transaction_datetime=txn.get("transaction_datetime"),
                phone_number=txn.get("phone_number"),
                email=txn.get("email"),
                pan_number=txn.get("pan_number"),
                disputed_amount=txn.get("disputed_amount"),
                ifsc_code=txn.get("ifsc_code"),
                root_account_number=txn.get("root_account_number"),
                root_rrn_transaction_id=txn.get("root_rrn_transaction_id"),
                root_bankid=txn.get("root_bankid"),
                status_code=txn.get("status_code", ""),
                remarks=txn.get("remarks"),
                root_effective_balance=txn.get("root_effective_balance"),
                root_ifsc_code=txn.get("root_ifsc_code"),
                sent_at=datetime.utcnow()
            )
            db.add(status_update)
        
        # Update fraud report status
        fraud_report = db.query(models.I4CFraudReport).filter(
            models.I4CFraudReport.acknowledgement_no == acknowledgement_no
        ).first()
        
        if fraud_report:
            fraud_report.status = "UPDATED"
            
            for txn in update_data.get("transactions", []):
                transaction = db.query(models.I4CTransaction).filter(
                    models.I4CTransaction.fraud_report_id == fraud_report.id,
                    models.I4CTransaction.rrn == txn.get("rrn_transaction_id")
                ).first()
                
                if transaction:
                    transaction.status_code = txn.get("status_code")
                    transaction.remarks = txn.get("remarks")
                    transaction.hold_initiated = txn.get("status_code") == "hold"
                    transaction.hold_amount = txn.get("disputed_amount")
        
        db.commit()
        
        return success_response({
            "acknowledgement_no": acknowledgement_no,
            "job_id": job_id,
            "status": "UPDATED"
        })
        
    except Exception as e:
        db.rollback()
        return error_response("500", str(e))


@router.get("/ncrp-mock")
def get_ncrp_mock_data(current_user: models.User = Depends(ops_checker)):
    return [
        {
            "complaint_id": f"NCRP-{uuid.uuid4().hex[:8].upper()}",
            "victim_name": "Rohan Sharma",
            "incident_date": datetime.utcnow().isoformat(),
            "amount": 54000.0,
            "ifsc": "SBIN0001234",
            "vpa": "victim@oksbi",
            "fraud_type": "UPI Fraud"
        },
        {
            "complaint_id": f"NCRP-{uuid.uuid4().hex[:8].upper()}",
            "victim_name": "Sunita Devi",
            "incident_date": datetime.utcnow().isoformat(),
            "amount": 12000.0,
            "ifsc": "HDFC0000102",
            "vpa": "scammer@okhdfcbank",
            "fraud_type": "Phishing"
        },
        {
            "complaint_id": f"NCRP-{uuid.uuid4().hex[:8].upper()}",
            "victim_name": "Amit Patel",
            "incident_date": datetime.utcnow().isoformat(),
            "amount": 8900.0,
            "ifsc": "ICIC0001234",
            "vpa": "amit@okicici",
            "fraud_type": "Identity Theft"
        }
    ]
