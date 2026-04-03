from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Text, Enum, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum
import uuid

Base = declarative_base()

# Database dependency
def get_db():
    from ..main import engine
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SourceType(str, enum.Enum):
    DEMO = "demo"
    I4C = "i4c"

class UnifiedCaseStatus(str, enum.Enum):
    """Status for unified Case model"""
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    UNDER_REVIEW = "UNDER_REVIEW"
    HOLD = "HOLD"
    FROZEN = "FROZEN"
    CONFIRMED = "CONFIRMED"
    NOT_RELATED = "NOT_RELATED"
    RECONCILED = "RECONCILED"
    CLOSED = "CLOSED"

class TimelineEventType(str, enum.Enum):
    I4C_SIGNAL_RECEIVED = "I4C_SIGNAL_RECEIVED"
    CASE_CREATED = "CASE_CREATED"
    BRANCH_ASSIGNED = "BRANCH_ASSIGNED"
    BANK_ACTION_INITIATED = "BANK_ACTION_INITIATED"
    CASE_UPDATED = "CASE_UPDATED"
    HOLD_INITIATED = "HOLD_INITIATED"
    FREEZE_INITIATED = "FREEZE_INITIATED"
    CONFIRMED_RELATED = "CONFIRMED_RELATED"
    MARKED_NOT_RELATED = "MARKED_NOT_RELATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    CASE_STATUS_UPDATED = "CASE_STATUS_UPDATED"
    EVIDENCE_UPLOADED = "EVIDENCE_UPLOADED"

class CaseStatus(str, enum.Enum):
    # Legacy status for Complaint model - KEEPING for backward compatibility
    NEW = "NEW"
    INGESTED = "INGESTED"
    ENRICHED = "ENRICHED"
    ROUTED = "ROUTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    RELATED_CONFIRMED = "RELATED_CONFIRMED"
    HOLD_INITIATED = "HOLD_INITIATED"
    HOLD_CONFIRMED = "HOLD_CONFIRMED"
    BANK_PENDING = "BANK_PENDING"
    BANK_CONFIRMED = "BANK_CONFIRMED"
    NOT_RELATED = "NOT_RELATED"
    PARTIAL_HOLD = "PARTIAL_HOLD"
    FUNDS_MOVED = "FUNDS_MOVED"
    ALREADY_FROZEN = "ALREADY_FROZEN"
    KYC_PENDING = "KYC_PENDING"
    LEA_PENDING = "LEA_PENDING"
    GRIEVANCE_OPEN = "GRIEVANCE_OPEN"
    RESTORATION_PENDING = "RESTORATION_PENDING"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"
    CLOSED_SUCCESS = "CLOSED_SUCCESS"
    CLOSED_NO_FUNDS = "CLOSED_NO_FUNDS"
    RECONCILED = "RECONCILED"

class Case(Base):
    """Unified cases table for both demo and I4C cases"""
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, unique=True, index=True)
    transaction_id = Column(String, index=True)
    amount = Column(Float)
    payment_mode = Column(String)  # UPI, Net Banking, etc.
    payer_account_number = Column(String)
    payer_bank = Column(String)
    mobile_number = Column(String)
    district = Column(String)
    state = Column(String)
    source_type = Column(Enum(SourceType), default=SourceType.DEMO)  # 'demo' or 'i4c'
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)  # NULL for demo cases
    status = Column(Enum(UnifiedCaseStatus), default=UnifiedCaseStatus.NEW)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    branch = relationship("Branch")
    
    # For I4C cases - link to original I4C data
    acknowledgement_no = Column(String, nullable=True, index=True)
    
    # I4C Sync Tracking
    i4c_sync_status = Column(String, default="PENDING")  # PENDING, SYNCED, FAILED


class Timeline(Base):
    """Case timeline for audit trail - tracks all case events"""
    __tablename__ = "timeline"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True, index=True)
    event_type = Column(Enum(TimelineEventType), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    case = relationship("Case", backref="timeline_events")
    branch = relationship("Branch")
    creator = relationship("User")


class Evidence(Base):
    """Evidence and documents uploaded for cases"""
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    file_name = Column(String, nullable=False)
    file_url = Column(String, nullable=True)
    file_type = Column(String, nullable=True)  # TRANSACTION_SCREENSHOT, BANK_STATEMENT, CBS_CONFIRMATION, INVESTIGATION_NOTE
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    case = relationship("Case", backref="evidence_items")
    uploader = relationship("User")


# Association table for many-to-many relationship between User and Role
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("role_id", Integer, ForeignKey("roles.id")),
)

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)

    users = relationship("User", secondary=user_roles, back_populates="roles")

class Bank(Base):
    __tablename__ = "banks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    code = Column(String, unique=True, index=True)
    ifsc_prefix = Column(String)
    integration_model = Column(String)
    sla_hours = Column(Integer, default=24)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    branches = relationship("Branch", back_populates="bank", cascade="all, delete-orphan")
    users = relationship("User", back_populates="bank")
    complaints = relationship("Complaint", back_populates="bank")

class Branch(Base):
    __tablename__ = "branches"
    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=False)
    branch_code = Column(String, index=True)
    branch_name = Column(String)
    ifsc_code = Column(String, index=True)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    demo_access = Column(Boolean, default=False)  # Enable demo dataset access
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bank = relationship("Bank", back_populates="branches")
    users = relationship("User", back_populates="branch")
    complaints = relationship("Complaint", back_populates="branch")
    workflows = relationship("CaseWorkflow", back_populates="branch")

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    BRANCH_USER = "branch_user"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, default=UserRole.BRANCH_USER.value)  # 'admin' or 'branch_user'
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    bank = relationship("Bank", back_populates="users")
    branch = relationship("Branch", back_populates="users")
    responses = relationship("BankResponse", back_populates="responded_by_user")

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String, unique=True, index=True)
    victim_name = Column(String)
    victim_mobile = Column(String)
    incident_date = Column(DateTime)
    fraud_type = Column(String)
    amount = Column(Float)
    currency = Column(String, default="INR")
    ifsc_signal = Column(String, nullable=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.INGESTED)
    
    # Multi-tenancy foreign keys
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bank = relationship("Bank", back_populates="complaints")
    branch = relationship("Branch", back_populates="complaints")
    enrichment = relationship("EnrichmentResult", back_populates="complaint", uselist=False)
    routing_logs = relationship("RoutingLog", back_populates="complaint")
    responses = relationship("BankResponse", back_populates="complaint")
    sla = relationship("SLATracking", back_populates="complaint", uselist=False)
    workflows = relationship("CaseWorkflow", back_populates="complaint")
    status_updates = relationship("StatusUpdate", back_populates="complaint")
    hold_actions = relationship("HoldAction", back_populates="complaint")
    state_transitions = relationship("StateTransition", back_populates="complaint")

class EnrichmentResult(Base):
    __tablename__ = "enrichment_results"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"))
    target_bank_id = Column(Integer, ForeignKey("banks.id"))
    target_branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    confidence_score = Column(Float)
    signals = Column(Text)
    validation_method = Column(String)
    
    complaint = relationship("Complaint", back_populates="enrichment")
    bank = relationship("Bank")
    branch = relationship("Branch")

class RoutingLog(Base):
    __tablename__ = "routing_logs"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"))
    bank_id = Column(Integer, ForeignKey("banks.id"))
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    routed_at = Column(DateTime, default=datetime.utcnow)
    request_id = Column(String)
    status = Column(String)
    error_message = Column(Text, nullable=True)

    complaint = relationship("Complaint", back_populates="routing_logs")
    bank = relationship("Bank")
    branch = relationship("Branch")

class BankResponse(Base):
    __tablename__ = "bank_responses"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"))
    bank_id = Column(Integer, ForeignKey("banks.id"))
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    response_code = Column(String)
    action_taken = Column(String)
    hold_amount = Column(Float, default=0.0)
    remarks = Column(Text)
    responded_at = Column(DateTime, default=datetime.utcnow)
    responded_by = Column(Integer, ForeignKey("users.id"))
    
    # I4C Sync Tracking Fields
    i4c_sync_status = Column(String, default="PENDING")  # PENDING, SYNCED, FAILED
    i4c_sync_attempted_at = Column(DateTime, nullable=True)
    i4c_sync_response_code = Column(String, nullable=True)
    i4c_sync_message = Column(String, nullable=True)
    i4c_job_id = Column(String, nullable=True)

    complaint = relationship("Complaint", back_populates="responses")
    bank = relationship("Bank")
    branch = relationship("Branch")
    responded_by_user = relationship("User", back_populates="responses")

class SLATracking(Base):
    __tablename__ = "sla_tracking"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"))
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    start_time = Column(DateTime)
    deadline = Column(DateTime)
    completion_time = Column(DateTime, nullable=True)
    is_breached = Column(Boolean, default=False)

    complaint = relationship("Complaint", back_populates="sla")
    bank = relationship("Bank")
    branch = relationship("Branch")

class CaseWorkflow(Base):
    """Dynamic workflow table for case processing"""
    __tablename__ = "case_workflows"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    job_id = Column(String)
    acknowledgement_no = Column(String, index=True)
    assigned_bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    assigned_branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    scenario = Column(String)
    status = Column(String)
    priority = Column(String, default="MEDIUM")
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    remarks = Column(Text, nullable=True)

    complaint = relationship("Complaint", back_populates="workflows")
    bank = relationship("Bank")
    branch = relationship("Branch", back_populates="workflows")
    assigned_user = relationship("User")

class StatusUpdate(Base):
    """Dynamic status updates table"""
    __tablename__ = "status_updates"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"))
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    update_type = Column(String)
    status_code = Column(String)
    previous_status = Column(String, nullable=True)
    new_status = Column(String)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    complaint = relationship("Complaint", back_populates="status_updates")
    bank = relationship("Bank")
    branch = relationship("Branch")
    creator = relationship("User")

class HoldAction(Base):
    """Dynamic hold actions table"""
    __tablename__ = "hold_actions"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"))
    case_id = Column(String, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    action_type = Column(String)
    outcome = Column(String)
    held_amount = Column(Float, default=0.0)
    expected_amount = Column(Float, default=0.0)
    account_number = Column(String, nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    complaint = relationship("Complaint", back_populates="hold_actions")
    bank = relationship("Bank")
    branch = relationship("Branch")
    executor = relationship("User")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    action = Column(String)
    resource = Column(String)
    resource_id = Column(String)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)

    user = relationship("User")
    bank = relationship("Bank")
    branch = relationship("Branch")

class StateTransition(Base):
    __tablename__ = "state_transitions"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"))
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    from_status = Column(String)
    to_status = Column(String)
    changed_by = Column(Integer, ForeignKey("users.id"))
    changed_at = Column(DateTime, default=datetime.utcnow)
    remarks = Column(Text, nullable=True)

    complaint = relationship("Complaint", back_populates="state_transitions")
    bank = relationship("Bank")
    branch = relationship("Branch")
    changer = relationship("User")

class KYCPack(Base):
    """KYC submission packs to authorities"""
    __tablename__ = "kyc_packs"
    id = Column(Integer, primary_key=True, index=True)
    pack_id = Column(String, unique=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    case_id = Column(String, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    version = Column(Integer, default=1)
    status = Column(String, default="DRAFT")  # DRAFT, SUBMITTED, LOCKED
    mandatory_fields = Column(Text, nullable=True)  # JSON of KYC fields
    attachments = Column(Text, nullable=True)  # JSON array of file paths
    acknowledgement_ref = Column(String, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    locked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    remarks = Column(Text, nullable=True)

    complaint = relationship("Complaint")
    bank = relationship("Bank")
    branch = relationship("Branch")
    creator = relationship("User")

class LEAResponse(Base):
    """Law Enforcement Agency request responses"""
    __tablename__ = "lea_responses"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    case_id = Column(String, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    
    # IO/Police details
    io_name = Column(String, nullable=True)
    police_station = Column(String, nullable=True)
    request_received_at = Column(DateTime, nullable=True)
    request_attachment = Column(String, nullable=True)
    
    # Response details
    acknowledgement_proof = Column(String, nullable=True)
    response_pack = Column(Text, nullable=True)  # JSON of response documents
    response_dispatch_proof = Column(String, nullable=True)
    dispatched_at = Column(DateTime, nullable=True)
    
    status = Column(String, default="REGISTERED")  # REGISTERED, ACKNOWLEDGED, RESPONSE_SENT
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    remarks = Column(Text, nullable=True)

    complaint = relationship("Complaint")
    bank = relationship("Bank")
    branch = relationship("Branch")
    creator = relationship("User")

class Grievance(Base):
    """Customer grievance handling"""
    __tablename__ = "grievances"
    id = Column(Integer, primary_key=True, index=True)
    grievance_id = Column(String, unique=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    case_id = Column(String, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    
    grievance_type = Column(String)  # HOLD_REMOVAL, DELAY, OTHER
    escalation_stage = Column(Integer, default=1)  # 1-5 stages
    info_furnished_note = Column(Text, nullable=True)
    outcome_code = Column(String, nullable=True)
    release_direction_doc = Column(String, nullable=True)
    
    status = Column(String, default="OPEN")  # OPEN, ESCALATED, RESOLVED, CLOSED
    opened_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    remarks = Column(Text, nullable=True)

    complaint = relationship("Complaint")
    bank = relationship("Bank")
    branch = relationship("Branch")
    creator = relationship("User", foreign_keys=[created_by])
    resolver = relationship("User", foreign_keys=[resolved_by])

class RestorationOrder(Base):
    """Money restoration/court orders"""
    __tablename__ = "restoration_orders"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    case_id = Column(String, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    
    # Order details
    order_reference = Column(String)
    court_authority = Column(String, nullable=True)
    order_date = Column(DateTime, nullable=True)
    order_document = Column(String, nullable=True)
    
    # Destination account
    destination_account = Column(String)
    beneficiary_name = Column(String, nullable=True)
    verification_details = Column(Text, nullable=True)
    
    # Execution
    amount = Column(Float, default=0.0)
    utr_reference = Column(String, nullable=True)
    execution_proof = Column(String, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    
    status = Column(String, default="REGISTERED")  # REGISTERED, VERIFIED, APPROVED, EXECUTED, CLOSED
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    remarks = Column(Text, nullable=True)

    complaint = relationship("Complaint")
    bank = relationship("Bank")
    branch = relationship("Branch")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])

class ReconciliationItem(Base):
    """CBS vs Platform data reconciliation"""
    __tablename__ = "reconciliation_items"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String, unique=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    case_id = Column(String, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    
    mismatch_type = Column(String)  # AMOUNT_MISMATCH, STATUS_MISMATCH, MISSING_CBS, MISSING_PLATFORM
    platform_value = Column(Text, nullable=True)
    cbs_value = Column(Text, nullable=True)
    cbs_confirmation_ref = Column(String, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    status = Column(String, default="DETECTED")  # DETECTED, RESOLVED, CLOSED
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    remarks = Column(Text, nullable=True)

    complaint = relationship("Complaint")
    bank = relationship("Bank")
    branch = relationship("Branch")
    resolver = relationship("User")

class ExportLog(Base):
    """Audit log for exports and evidence packs"""
    __tablename__ = "export_logs"
    id = Column(Integer, primary_key=True, index=True)
    export_id = Column(String, unique=True, index=True)
    export_type = Column(String)  # CASE_REPORT, EVIDENCE_PACK, MIS_REPORT
    justification = Column(Text)
    case_ids = Column(Text, nullable=True)  # JSON array
    date_range_start = Column(DateTime, nullable=True)
    date_range_end = Column(DateTime, nullable=True)
    file_path = Column(String, nullable=True)
    watermarked = Column(Boolean, default=True)
    
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    bank = relationship("Bank")
    creator = relationship("User")


# ============== I4C INTEGRATION MODELS ==============

class I4CFraudReport(Base):
    """I4C fraud reports received from NCRP/I4C"""
    __tablename__ = "i4c_fraud_reports"
    id = Column(Integer, primary_key=True, index=True)
    acknowledgement_no = Column(String, unique=True, index=True, nullable=False)
    sub_category = Column(String, nullable=False)  # UPI, Internet Banking, etc.
    job_id = Column(String, unique=True, index=True)
    
    # Instrument (Victim) details
    requestor = Column(String, default="I4C-MHA")
    payer_bank = Column(String, nullable=False)
    payer_bank_code = Column(String, nullable=False)
    mode_of_payment = Column(String, nullable=False)  # debit or credit
    payer_mobile_number = Column(String, nullable=False)
    payer_account_number = Column(String, nullable=False)
    payer_state = Column(String, nullable=True)
    payer_district = Column(String, nullable=True)
    transaction_type = Column(String, nullable=True)
    payer_wallet = Column(String, nullable=True)
    
    # Additional victim info
    payer_email = Column(String, nullable=True)
    payer_pan = Column(String, nullable=True)
    payer_ifsc = Column(String, nullable=True)
    
    # Status tracking
    status = Column(String, default="NEW")  # NEW, UNDER_INVESTIGATION, HOLD_INITIATED, CLOSED
    
    # Foreign keys
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True)
    case_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    
    # Timestamps
    received_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = relationship("I4CTransaction", back_populates="fraud_report", cascade="all, delete-orphan")
    bank = relationship("Bank")
    complaint = relationship("Complaint")


class I4CTransaction(Base):
    """Individual transactions within a fraud report"""
    __tablename__ = "i4c_transactions"
    id = Column(Integer, primary_key=True, index=True)
    fraud_report_id = Column(Integer, ForeignKey("i4c_fraud_reports.id"), nullable=False)
    
    # Transaction details
    amount = Column(Float, nullable=False)
    rrn = Column(String, nullable=False, index=True)  # Transaction reference
    transaction_date = Column(DateTime, nullable=False)
    transaction_time = Column(String, nullable=True)
    disputed_amount = Column(Float, nullable=False)
    layer = Column(Integer, nullable=False)  # Fraud chain layer (0, 1, 2...)
    
    # Payee (beneficiary) details
    payee_bank = Column(String, nullable=True)
    payee_bank_code = Column(String, nullable=True)
    payee_account_number = Column(String, nullable=True)
    payee_phone = Column(String, nullable=True)
    payee_email = Column(String, nullable=True)
    payee_pan = Column(String, nullable=True)
    payee_ifsc = Column(String, nullable=True)
    
    # Root transaction details (for layered frauds)
    root_account_number = Column(String, nullable=True)
    root_rrn = Column(String, nullable=True)
    root_bankid = Column(String, nullable=True)
    root_effective_balance = Column(Float, nullable=True, default=0)
    root_ifsc_code = Column(String, nullable=True)
    
    # Status tracking
    status_code = Column(String, nullable=True)  # hold, no balance, blocked, refund, etc.
    remarks = Column(Text, nullable=True)
    hold_initiated = Column(Boolean, default=False)
    hold_amount = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    fraud_report = relationship("I4CFraudReport", back_populates="transactions")


class I4CStatusUpdate(Base):
    """Status updates sent to I4C"""
    __tablename__ = "i4c_status_updates"
    id = Column(Integer, primary_key=True, index=True)
    acknowledgement_no = Column(String, nullable=False, index=True)
    job_id = Column(String, nullable=False)
    
    # Transaction update details
    txn_type = Column(String, nullable=False)  # action type
    txn_type_id = Column(String, nullable=False)
    rrn_transaction_id = Column(String, nullable=False)
    payee_bank = Column(String, nullable=True)
    payee_bank_code = Column(String, nullable=True)
    payee_account_number = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    transaction_datetime = Column(DateTime, nullable=True)
    phone_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    pan_number = Column(String, nullable=True)
    disputed_amount = Column(Float, nullable=True)
    ifsc_code = Column(String, nullable=True)
    root_account_number = Column(String, nullable=True)
    root_rrn_transaction_id = Column(String, nullable=True)
    root_bankid = Column(String, nullable=True)
    status_code = Column(String, nullable=False)  # 00, hold, no balance, etc.
    remarks = Column(Text, nullable=True)
    root_effective_balance = Column(Float, nullable=True)
    root_ifsc_code = Column(String, nullable=True)
    
    # Outbox tracking
    sent_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class APIInbox(Base):
    """Incoming API requests logging"""
    __tablename__ = "api_inbox"
    id = Column(Integer, primary_key=True, index=True)
    correlation_id = Column(String, index=True)
    api_name = Column(String, nullable=False)  # authenticate, fraud-report, etc.
    source_ip = Column(String, nullable=True)
    request_headers = Column(Text, nullable=True)
    request_body_encrypted = Column(Text, nullable=True)
    request_body_decrypted = Column(Text, nullable=True)
    response_code = Column(String, nullable=True)
    response_body = Column(Text, nullable=True)
    validation_errors = Column(Text, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)


class APIOutbox(Base):
    """Outgoing API requests logging"""
    __tablename__ = "api_outbox"
    id = Column(Integer, primary_key=True, index=True)
    correlation_id = Column(String, index=True)
    api_name = Column(String, nullable=False)  # status-update, etc.
    endpoint_url = Column(String, nullable=False)
    request_headers = Column(Text, nullable=True)
    request_body = Column(Text, nullable=True)
    response_code = Column(String, nullable=True)
    response_body = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    status = Column(String, default="PENDING")  # PENDING, SENT, FAILED, RETRYING
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============== DEMO DATASET MIRROR TABLES (EXCEL SHEETS) ==============

class DemoReadme(Base):
    __tablename__ = "demo_readme"
    id = Column(Integer, primary_key=True, index=True)
    line = Column(Text)


class DemoI4CInboundFraudReport(Base):
    __tablename__ = "demo_i4c_inbound_fraud_reports"
    id = Column(Integer, primary_key=True, index=True)
    acknowledgement_no = Column(String, index=True)
    sub_category = Column(String, nullable=True)
    requestor = Column(String, nullable=True)
    payer_bank = Column(String, nullable=True)
    payer_bank_code = Column(String, nullable=True)
    mode_of_payment = Column(String, nullable=True)
    payer_mobile_number = Column(String, nullable=True)
    payer_account_number = Column(String, nullable=True)
    state = Column(String, nullable=True)
    district = Column(String, nullable=True)
    transaction_type = Column(String, nullable=True)
    wallet = Column(String, nullable=True)
    received_at = Column(DateTime, nullable=True)
    incident_count = Column(Integer, nullable=True)
    total_disputed_amount = Column(Float, nullable=True)
    bank_ack_response_code = Column(String, nullable=True)
    bank_job_id = Column(String, nullable=True)
    calc_total_disputed_amount = Column(Float, nullable=True)
    amount_match_flag = Column(String, nullable=True)


class DemoI4CIncident(Base):
    __tablename__ = "demo_i4c_incidents"
    id = Column(Integer, primary_key=True, index=True)
    acknowledgement_no = Column(String, index=True)
    incident_id = Column(String, index=True)
    sub_category = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    rrn = Column(String, nullable=True, index=True)
    transaction_date = Column(DateTime, nullable=True)
    transaction_time = Column(String, nullable=True)
    disputed_amount = Column(Float, nullable=True)
    layer = Column(Integer, nullable=True)
    payee_bank = Column(String, nullable=True)
    payee_bank_code = Column(String, nullable=True)
    payee_ifsc_code = Column(String, nullable=True)
    payee_account_number = Column(String, nullable=True)


class DemoBankCaseWorkflow(Base):
    __tablename__ = "demo_bank_case_workflow"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, index=True)
    acknowledgement_no = Column(String, index=True)
    job_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, nullable=True)
    assigned_queue = Column(String, nullable=True)
    assigned_branch_id = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    current_state = Column(String, nullable=True)
    scenario = Column(String, nullable=True)


class DemoBankHoldAction(Base):
    __tablename__ = "demo_bank_hold_actions"
    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(String, index=True)
    case_id = Column(String, index=True)
    acknowledgement_no = Column(String, index=True)
    incident_id = Column(String, nullable=True, index=True)
    action_type = Column(String, nullable=True)
    action_time = Column(DateTime, nullable=True)
    requested_amount = Column(Float, nullable=True)
    action_amount = Column(Float, nullable=True)
    held_amount = Column(Float, nullable=True)
    hold_reference = Column(String, nullable=True)
    negative_lien_flag = Column(String, nullable=True)
    outcome = Column(String, nullable=True)
    remarks = Column(Text, nullable=True)


class DemoBankStatusUpdateRequest(Base):
    __tablename__ = "demo_bank_statusupdate_request"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True)
    acknowledgement_no = Column(String, index=True)
    job_id = Column(String, nullable=True, index=True)
    sent_at = Column(DateTime, nullable=True)
    content_type = Column(String, nullable=True)
    authorization_type = Column(String, nullable=True)
    payload_encrypted = Column(Text, nullable=True)
    transaction_count = Column(Integer, nullable=True)


class DemoBankStatusUpdateTxnDetail(Base):
    __tablename__ = "demo_bank_statusupdate_txndetails"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True)
    acknowledgement_no = Column(String, index=True)
    job_id = Column(String, nullable=True, index=True)
    incident_id = Column(String, nullable=True, index=True)
    root_rrn_transaction_id = Column(String, nullable=True)
    root_bankid = Column(String, nullable=True)
    root_account_number = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    transaction_datetime = Column(DateTime, nullable=True)
    disputed_amount = Column(Float, nullable=True)
    status_code = Column(String, nullable=True)
    remarks = Column(Text, nullable=True)
    phone_number = Column(String, nullable=True)
    pan_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    root_ifsc_code = Column(String, nullable=True)
    root_effective_balance = Column(Float, nullable=True)
    negative_lien_flag = Column(String, nullable=True)
    hold_reference = Column(String, nullable=True)
    held_amount = Column(Float, nullable=True)


class DemoI4CStatusUpdateResponse(Base):
    __tablename__ = "demo_i4c_statusupdate_response"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True)
    i4c_response_code = Column(String, nullable=True)
    i4c_message = Column(String, nullable=True)
    received_at = Column(DateTime, nullable=True)
    error_flag = Column(String, nullable=True)


class DemoWorkflowTimeline(Base):
    __tablename__ = "demo_workflow_timeline"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, index=True)
    acknowledgement_no = Column(String, index=True)
    job_id = Column(String, nullable=True, index=True)
    step_no = Column(Integer, nullable=True)
    step_name = Column(String, nullable=True)
    actor = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    step_status = Column(String, nullable=True)
    sla_target_minutes = Column(Integer, nullable=True)
    actual_minutes = Column(Integer, nullable=True)
    sla_breached = Column(String, nullable=True)


class MetaStatusCode(Base):
    __tablename__ = "meta_status_codes"
    id = Column(Integer, primary_key=True, index=True)
    status_code = Column(String, unique=True, index=True)
    status_label = Column(String, nullable=True)
    meaning = Column(Text, nullable=True)
    owner = Column(String, nullable=True)
    demo_example_usage = Column(Text, nullable=True)


class DemoScenario(Base):
    __tablename__ = "demo_scenarios"
    id = Column(Integer, primary_key=True, index=True)
    scenario = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)


# ============== NOTIFICATION SYSTEM MODELS ==============

class Notification(Base):
    """In-app notification model"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(20), default="info")  # info, success, warning, error
    link = Column(String(500), nullable=True)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", backref="notifications")

class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    push_notifications = Column(Boolean, default=True)
    
    # Event-specific settings
    notify_new_case = Column(Boolean, default=True)
    notify_status_update = Column(Boolean, default=True)
    notify_sla_warning = Column(Boolean, default=True)
    notify_hold_action = Column(Boolean, default=True)
    notify_lea_request = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", backref="notification_preference")

class CaseEvidence(Base):
    """Case evidence/document uploads"""
    __tablename__ = "case_evidence"
    
    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String, unique=True, index=True)
    case_id = Column(String, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String)
    file_size = Column(Integer)
    description = Column(Text)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", backref="uploaded_evidence")


class LoginAudit(Base):
    """User login audit trail for admin tracking"""
    __tablename__ = "login_audit"
    
    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    username = Column(String, nullable=False)
    email = Column(String, nullable=True)
    bank_id = Column(Integer, ForeignKey("banks.id"), nullable=True, index=True)
    bank_name = Column(String, nullable=True)
    bank_code = Column(String, nullable=True)
    roles = Column(Text)  # JSON array of roles
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    login_time = Column(DateTime, default=datetime.utcnow, index=True)
    logout_time = Column(DateTime, nullable=True)
    session_duration_minutes = Column(Integer, nullable=True)
    status = Column(String, default="active")  # active, logged_out, expired
    
    # Relationships
    user = relationship("User", backref="login_audits")
    bank = relationship("Bank", backref="login_audits")

