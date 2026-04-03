"""
Standalone ingestion script for I4C Simulated Demo Dataset.
This script loads data from I4C_Simulated_Demo_Dataset.xlsx directly into PostgreSQL.
"""

import os
import sys
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean

# Database URL - using the same as .env file
DATABASE_URL = "postgresql+psycopg://postgres:niv123@localhost:5432/fiducia_sass"

# Replace driver for SQLAlchemy
DB_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")

print(f"Connecting to database...")
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define models inline to avoid import issues
class DemoI4CInboundFraudReport(Base):
    __tablename__ = "demo_i4c_inbound_fraud_reports"
    id = Column(Integer, primary_key=True, index=True)
    acknowledgement_no = Column(String, index=True)
    sub_category = Column(String)
    requestor = Column(String)
    payer_bank = Column(String)
    payer_bank_code = Column(String)
    mode_of_payment = Column(String)
    payer_mobile_number = Column(String)
    payer_account_number = Column(String)
    state = Column(String)
    district = Column(String)
    transaction_type = Column(String)
    wallet = Column(String)
    received_at = Column(DateTime)
    incident_count = Column(Integer)
    total_disputed_amount = Column(Float)
    bank_ack_response_code = Column(String)
    bank_job_id = Column(String)
    calc_total_disputed_amount = Column(Float)
    amount_match_flag = Column(String)

class DemoI4CIncident(Base):
    __tablename__ = "demo_i4c_incidents"
    id = Column(Integer, primary_key=True, index=True)
    acknowledgement_no = Column(String, index=True)
    incident_id = Column(String)
    sub_category = Column(String)
    amount = Column(Float)
    rrn = Column(String)
    transaction_date = Column(DateTime)
    transaction_time = Column(String)
    disputed_amount = Column(Float)
    layer = Column(Integer)  # Fixed: Integer not String
    payee_bank = Column(String)
    payee_bank_code = Column(String)
    payee_ifsc_code = Column(String)
    payee_account_number = Column(String)

class DemoBankCaseWorkflow(Base):
    __tablename__ = "demo_bank_case_workflows"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, index=True)
    acknowledgement_no = Column(String, index=True)
    job_id = Column(String)
    created_at = Column(DateTime)
    assigned_queue = Column(String)
    assigned_branch_id = Column(String)
    priority = Column(String)
    current_state = Column(String)
    scenario = Column(String)

class DemoBankHoldAction(Base):
    __tablename__ = "demo_bank_hold_actions"
    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(String)
    case_id = Column(String, index=True)
    acknowledgement_no = Column(String, index=True)
    incident_id = Column(String)
    action_type = Column(String)
    action_time = Column(DateTime)
    requested_amount = Column(Float)
    action_amount = Column(Float)
    held_amount = Column(Float)
    hold_reference = Column(String)
    negative_lien_flag = Column(String)
    outcome = Column(String)
    remarks = Column(String)

class DemoBankStatusUpdateRequest(Base):
    __tablename__ = "demo_bank_status_update_requests"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True)
    acknowledgement_no = Column(String, index=True)
    job_id = Column(String)
    sent_at = Column(DateTime)
    content_type = Column(String)
    authorization_type = Column(String)
    payload_encrypted = Column(String)
    transaction_count = Column(Integer)

class DemoBankStatusUpdateTxnDetail(Base):
    __tablename__ = "demo_bank_status_update_txn_details"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True)
    acknowledgement_no = Column(String, index=True)
    job_id = Column(String)
    incident_id = Column(String)
    root_rrn_transaction_id = Column(String)
    root_bankid = Column(String)
    root_account_number = Column(String)
    amount = Column(Float)
    transaction_datetime = Column(DateTime)
    disputed_amount = Column(Float)
    status_code = Column(String)
    remarks = Column(String)
    phone_number = Column(String)
    pan_number = Column(String)
    email = Column(String)
    root_ifsc_code = Column(String)
    root_effective_balance = Column(Float)
    negative_lien_flag = Column(String)
    hold_reference = Column(String)
    held_amount = Column(Float)

class DemoI4CStatusUpdateResponse(Base):
    __tablename__ = "demo_i4c_status_update_responses"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True)
    i4c_response_code = Column(String)
    i4c_message = Column(String)
    received_at = Column(DateTime)
    error_flag = Column(String)

class DemoWorkflowTimeline(Base):
    __tablename__ = "demo_workflow_timeline"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, index=True)
    acknowledgement_no = Column(String, index=True)
    job_id = Column(String)
    step_no = Column(Integer)
    step_name = Column(String)
    actor = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    step_status = Column(String)
    sla_target_minutes = Column(Integer)
    actual_minutes = Column(Integer)
    sla_breached = Column(String)

class MetaStatusCode(Base):
    __tablename__ = "meta_status_codes"
    id = Column(Integer, primary_key=True, index=True)
    status_code = Column(String, unique=True, index=True)
    status_label = Column(String)
    meaning = Column(String)
    owner = Column(String)
    demo_example_usage = Column(String)

class Bank(Base):
    __tablename__ = "banks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    code = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)

class Branch(Base):
    __tablename__ = "branches"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    code = Column(String)
    bank_id = Column(Integer)
    state = Column(String)
    district = Column(String)
    is_active = Column(Boolean, default=True)

class DemoScenario(Base):
    __tablename__ = "demo_scenarios"
    id = Column(Integer, primary_key=True, index=True)
    scenario = Column(String)
    description = Column(String)

def parse_datetime(value):
    """Parse various datetime formats"""
    if pd.isna(value) or value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d-%m-%Y"]:
            try:
                return datetime.strptime(str(value), fmt)
            except:
                continue
        return pd.to_datetime(value).to_pydatetime()
    except:
        return None

def ingest_fraud_reports(db, df):
    print("Ingesting I4C Inbound Fraud Reports...")
    db.execute(text("DELETE FROM demo_i4c_inbound_fraud_reports"))
    db.commit()
    
    for _, row in df.iterrows():
        report = DemoI4CInboundFraudReport(
            acknowledgement_no=str(row.get('acknowledgement_no', '')) if pd.notna(row.get('acknowledgement_no')) else None,
            sub_category=str(row.get('sub_category', '')) if pd.notna(row.get('sub_category')) else None,
            requestor=str(row.get('requestor', '')) if pd.notna(row.get('requestor')) else None,
            payer_bank=str(row.get('payer_bank', '')) if pd.notna(row.get('payer_bank')) else None,
            payer_bank_code=str(row.get('payer_bank_code', '')) if pd.notna(row.get('payer_bank_code')) else None,
            mode_of_payment=str(row.get('mode_of_payment', '')) if pd.notna(row.get('mode_of_payment')) else None,
            payer_mobile_number=str(row.get('payer_mobile_number', '')) if pd.notna(row.get('payer_mobile_number')) else None,
            payer_account_number=str(row.get('payer_account_number', '')) if pd.notna(row.get('payer_account_number')) else None,
            state=str(row.get('state', '')) if pd.notna(row.get('state')) else None,
            district=str(row.get('district', '')) if pd.notna(row.get('district')) else None,
            transaction_type=str(row.get('transaction_type', '')) if pd.notna(row.get('transaction_type')) else None,
            wallet=str(row.get('wallet', '')) if pd.notna(row.get('wallet')) else None,
            received_at=parse_datetime(row.get('received_at')),
            incident_count=int(row.get('incident_count', 0)) if pd.notna(row.get('incident_count')) else None,
            total_disputed_amount=float(row.get('total_disputed_amount', 0)) if pd.notna(row.get('total_disputed_amount')) else None,
            bank_ack_response_code=str(row.get('bank_ack_response_code', '')) if pd.notna(row.get('bank_ack_response_code')) else None,
            bank_job_id=str(row.get('bank_job_id', '')) if pd.notna(row.get('bank_job_id')) else None,
            calc_total_disputed_amount=float(row.get('calc_total_disputed_amount', 0)) if pd.notna(row.get('calc_total_disputed_amount')) else None,
            amount_match_flag=str(row.get('amount_match_flag', '')) if pd.notna(row.get('amount_match_flag')) else None
        )
        db.add(report)
    db.commit()
    print(f"  Ingested {len(df)} fraud reports")

def ingest_incidents(db, df):
    print("Ingesting I4C Incidents...")
    db.execute(text("DELETE FROM demo_i4c_incidents"))
    db.commit()
    
    for _, row in df.iterrows():
        incident = DemoI4CIncident(
            acknowledgement_no=str(row.get('acknowledgement_no', '')) if pd.notna(row.get('acknowledgement_no')) else None,
            incident_id=str(row.get('incident_id', '')) if pd.notna(row.get('incident_id')) else None,
            sub_category=str(row.get('sub_category', '')) if pd.notna(row.get('sub_category')) else None,
            amount=float(row.get('amount', 0)) if pd.notna(row.get('amount')) else None,
            rrn=str(row.get('rrn', '')) if pd.notna(row.get('rrn')) else None,
            transaction_date=parse_datetime(row.get('transaction_date')),  # Fixed: parse as datetime
            transaction_time=str(row.get('transaction_time', '')) if pd.notna(row.get('transaction_time')) else None,
            disputed_amount=float(row.get('disputed_amount', 0)) if pd.notna(row.get('disputed_amount')) else None,
            layer=int(row.get('layer', 0)) if pd.notna(row.get('layer')) else None,
            payee_bank=str(row.get('payee_bank', '')) if pd.notna(row.get('payee_bank')) else None,
            payee_bank_code=str(row.get('payee_bank_code', '')) if pd.notna(row.get('payee_bank_code')) else None,
            payee_ifsc_code=str(row.get('payee_ifsc_code', '')) if pd.notna(row.get('payee_ifsc_code')) else None,
            payee_account_number=str(row.get('payee_account_number', '')) if pd.notna(row.get('payee_account_number')) else None
        )
        db.add(incident)
    db.commit()
    print(f"  Ingested {len(df)} incidents")

def ingest_case_workflows(db, df):
    print("Ingesting Bank Case Workflows...")
    db.execute(text("DELETE FROM demo_bank_case_workflows"))
    db.commit()
    
    for _, row in df.iterrows():
        workflow = DemoBankCaseWorkflow(
            case_id=str(row.get('case_id', '')) if pd.notna(row.get('case_id')) else None,
            acknowledgement_no=str(row.get('acknowledgement_no', '')) if pd.notna(row.get('acknowledgement_no')) else None,
            job_id=str(row.get('job_id', '')) if pd.notna(row.get('job_id')) else None,
            created_at=parse_datetime(row.get('created_at')),
            assigned_queue=str(row.get('assigned_queue', '')) if pd.notna(row.get('assigned_queue')) else None,
            assigned_branch_id=str(row.get('assigned_branch_id', '')) if pd.notna(row.get('assigned_branch_id')) else None,
            priority=str(row.get('priority', '')) if pd.notna(row.get('priority')) else None,
            current_state=str(row.get('current_state', '')) if pd.notna(row.get('current_state')) else None,
            scenario=str(row.get('scenario', '')) if pd.notna(row.get('scenario')) else None
        )
        db.add(workflow)
    db.commit()
    print(f"  Ingested {len(df)} workflows")

def ingest_hold_actions(db, df):
    print("Ingesting Bank Hold Actions...")
    db.execute(text("DELETE FROM demo_bank_hold_actions"))
    db.commit()
    
    for _, row in df.iterrows():
        action = DemoBankHoldAction(
            action_id=str(row.get('action_id', '')) if pd.notna(row.get('action_id')) else None,
            case_id=str(row.get('case_id', '')) if pd.notna(row.get('case_id')) else None,
            acknowledgement_no=str(row.get('acknowledgement_no', '')) if pd.notna(row.get('acknowledgement_no')) else None,
            incident_id=str(row.get('incident_id', '')) if pd.notna(row.get('incident_id')) else None,
            action_type=str(row.get('action_type', '')) if pd.notna(row.get('action_type')) else None,
            action_time=parse_datetime(row.get('action_time')),
            requested_amount=float(row.get('requested_amount', 0)) if pd.notna(row.get('requested_amount')) else None,
            action_amount=float(row.get('action_amount', 0)) if pd.notna(row.get('action_amount')) else None,
            held_amount=float(row.get('held_amount', 0)) if pd.notna(row.get('held_amount')) else None,
            hold_reference=str(row.get('hold_reference', '')) if pd.notna(row.get('hold_reference')) else None,
            negative_lien_flag=str(row.get('negative_lien_flag', '')) if pd.notna(row.get('negative_lien_flag')) else None,
            outcome=str(row.get('outcome', '')) if pd.notna(row.get('outcome')) else None,
            remarks=str(row.get('remarks', '')) if pd.notna(row.get('remarks')) else None
        )
        db.add(action)
    db.commit()
    print(f"  Ingested {len(df)} hold actions")

def ingest_status_update_requests(db, df):
    print("Ingesting Bank Status Update Requests...")
    db.execute(text("DELETE FROM demo_bank_status_update_requests"))
    db.commit()
    
    for _, row in df.iterrows():
        request = DemoBankStatusUpdateRequest(
            request_id=str(row.get('request_id', '')) if pd.notna(row.get('request_id')) else None,
            acknowledgement_no=str(row.get('acknowledgement_no', '')) if pd.notna(row.get('acknowledgement_no')) else None,
            job_id=str(row.get('job_id', '')) if pd.notna(row.get('job_id')) else None,
            sent_at=parse_datetime(row.get('sent_at')),
            content_type=str(row.get('content_type', '')) if pd.notna(row.get('content_type')) else None,
            authorization_type=str(row.get('authorization_type', '')) if pd.notna(row.get('authorization_type')) else None,
            payload_encrypted=str(row.get('payload_encrypted', '')) if pd.notna(row.get('payload_encrypted')) else None,
            transaction_count=int(row.get('transaction_count', 0)) if pd.notna(row.get('transaction_count')) else None
        )
        db.add(request)
    db.commit()
    print(f"  Ingested {len(df)} status update requests")

def ingest_status_update_txn_details(db, df):
    print("Ingesting Bank Status Update Transaction Details...")
    db.execute(text("DELETE FROM demo_bank_status_update_txn_details"))
    db.commit()
    
    for _, row in df.iterrows():
        detail = DemoBankStatusUpdateTxnDetail(
            request_id=str(row.get('request_id', '')) if pd.notna(row.get('request_id')) else None,
            acknowledgement_no=str(row.get('acknowledgement_no', '')) if pd.notna(row.get('acknowledgement_no')) else None,
            job_id=str(row.get('job_id', '')) if pd.notna(row.get('job_id')) else None,
            incident_id=str(row.get('incident_id', '')) if pd.notna(row.get('incident_id')) else None,
            root_rrn_transaction_id=str(row.get('root_rrn_transaction_id', '')) if pd.notna(row.get('root_rrn_transaction_id')) else None,
            root_bankid=str(row.get('root_bankid', '')) if pd.notna(row.get('root_bankid')) else None,
            root_account_number=str(row.get('root_account_number', '')) if pd.notna(row.get('root_account_number')) else None,
            amount=float(row.get('amount', 0)) if pd.notna(row.get('amount')) else None,
            transaction_datetime=parse_datetime(row.get('transaction_datetime')),
            disputed_amount=float(row.get('disputed_amount', 0)) if pd.notna(row.get('disputed_amount')) else None,
            status_code=str(row.get('status_code', '')) if pd.notna(row.get('status_code')) else None,
            remarks=str(row.get('remarks', '')) if pd.notna(row.get('remarks')) else None,
            phone_number=str(row.get('phone_number', '')) if pd.notna(row.get('phone_number')) else None,
            pan_number=str(row.get('pan_number', '')) if pd.notna(row.get('pan_number')) else None,
            email=str(row.get('email', '')) if pd.notna(row.get('email')) else None,
            root_ifsc_code=str(row.get('root_ifsc_code', '')) if pd.notna(row.get('root_ifsc_code')) else None,
            root_effective_balance=float(row.get('root_effective_balance', 0)) if pd.notna(row.get('root_effective_balance')) else None,
            negative_lien_flag=str(row.get('negative_lien_flag', '')) if pd.notna(row.get('negative_lien_flag')) else None,
            hold_reference=str(row.get('hold_reference', '')) if pd.notna(row.get('hold_reference')) else None,
            held_amount=float(row.get('held_amount', 0)) if pd.notna(row.get('held_amount')) else None
        )
        db.add(detail)
    db.commit()
    print(f"  Ingested {len(df)} status update transaction details")

def ingest_i4c_responses(db, df):
    print("Ingesting I4C Status Update Responses...")
    db.execute(text("DELETE FROM demo_i4c_status_update_responses"))
    db.commit()
    
    for _, row in df.iterrows():
        response = DemoI4CStatusUpdateResponse(
            request_id=str(row.get('request_id', '')) if pd.notna(row.get('request_id')) else None,
            i4c_response_code=str(row.get('i4c_response_code', '')) if pd.notna(row.get('i4c_response_code')) else None,
            i4c_message=str(row.get('i4c_message', '')) if pd.notna(row.get('i4c_message')) else None,
            received_at=parse_datetime(row.get('received_at')),
            error_flag=str(row.get('error_flag', '')) if pd.notna(row.get('error_flag')) else None
        )
        db.add(response)
    db.commit()
    print(f"  Ingested {len(df)} I4C responses")

def ingest_workflow_timeline(db, df):
    print("Ingesting Workflow Timeline...")
    db.execute(text("DELETE FROM demo_workflow_timeline"))
    db.commit()
    
    for _, row in df.iterrows():
        timeline = DemoWorkflowTimeline(
            case_id=str(row.get('case_id', '')) if pd.notna(row.get('case_id')) else None,
            acknowledgement_no=str(row.get('acknowledgement_no', '')) if pd.notna(row.get('acknowledgement_no')) else None,
            job_id=str(row.get('job_id', '')) if pd.notna(row.get('job_id')) else None,
            step_no=int(row.get('step_no', 0)) if pd.notna(row.get('step_no')) else None,
            step_name=str(row.get('step_name', '')) if pd.notna(row.get('step_name')) else None,
            actor=str(row.get('actor', '')) if pd.notna(row.get('actor')) else None,
            start_time=parse_datetime(row.get('start_time')),
            end_time=parse_datetime(row.get('end_time')),
            step_status=str(row.get('step_status', '')) if pd.notna(row.get('step_status')) else None,
            sla_target_minutes=int(row.get('sla_target_minutes', 0)) if pd.notna(row.get('sla_target_minutes')) else None,
            actual_minutes=int(row.get('actual_minutes', 0)) if pd.notna(row.get('actual_minutes')) else None,
            sla_breached=str(row.get('sla_breached', '')) if pd.notna(row.get('sla_breached')) else None
        )
        db.add(timeline)
    db.commit()
    print(f"  Ingested {len(df)} timeline events")

def ingest_bank_master(db, df):
    print("Ingesting Bank Master Data...")
    
    for _, row in df.iterrows():
        bank_code = str(row.get('bank_code', '')) if pd.notna(row.get('bank_code')) else None
        if not bank_code:
            continue
        
        existing = db.execute(text("SELECT id FROM banks WHERE code = :code"), {"code": bank_code}).fetchone()
        if not existing:
            db.execute(text("""
                INSERT INTO banks (name, code, is_active) 
                VALUES (:name, :code, true)
            """), {
                "name": str(row.get('bank_name', '')) if pd.notna(row.get('bank_name')) else None,
                "code": bank_code
            })
    db.commit()
    print(f"  Ingested {len(df)} banks")

def ingest_status_codes(db, df):
    print("Ingesting Status Codes...")
    db.execute(text("DELETE FROM meta_status_codes"))
    db.commit()
    
    for _, row in df.iterrows():
        db.execute(text("""
            INSERT INTO meta_status_codes (status_code, status_label, meaning, owner, demo_example_usage)
            VALUES (:code, :label, :meaning, :owner, :usage)
        """), {
            "code": str(row.get('status_code', '')) if pd.notna(row.get('status_code')) else None,
            "label": str(row.get('status_label', '')) if pd.notna(row.get('status_label')) else None,
            "meaning": str(row.get('meaning', '')) if pd.notna(row.get('meaning')) else None,
            "owner": str(row.get('owner', '')) if pd.notna(row.get('owner')) else None,
            "usage": str(row.get('demo_example_usage', '')) if pd.notna(row.get('demo_example_usage')) else None
        })
    db.commit()
    print(f"  Ingested {len(df)} status codes")

def ingest_bank_branches(db, df):
    print("Ingesting Bank Branches...")
    # Skip deleting branches due to foreign key constraints with users
    # Instead, update existing or insert new
    
    for _, row in df.iterrows():
        branch_code = str(row.get('ifsc_prefix', '')) if pd.notna(row.get('ifsc_prefix')) else None
        if not branch_code:
            continue
            
        # Check if branch exists
        existing = db.execute(text("SELECT id FROM branches WHERE code = :code"), {"code": branch_code}).fetchone()
        
        if existing:
            # Update existing branch
            db.execute(text("""
                UPDATE branches 
                SET name = :name, state = :state, district = :district
                WHERE code = :code
            """), {
                "name": str(row.get('branch_name', '')) if pd.notna(row.get('branch_name')) else None,
                "code": branch_code,
                "state": str(row.get('state', '')) if pd.notna(row.get('state')) else None,
                "district": str(row.get('district', '')) if pd.notna(row.get('district')) else None
            })
        else:
            # Insert new branch
            db.execute(text("""
                INSERT INTO branches (name, code, bank_id, state, district, is_active)
                VALUES (:name, :code, :bank_id, :state, :district, true)
            """), {
                "name": str(row.get('branch_name', '')) if pd.notna(row.get('branch_name')) else None,
                "code": branch_code,
                "bank_id": 1,
                "state": str(row.get('state', '')) if pd.notna(row.get('state')) else None,
                "district": str(row.get('district', '')) if pd.notna(row.get('district')) else None
            })
    
    db.commit()
    print(f"  Processed {len(df)} branches")

def ingest_bank_users(db, df):
    print("Ingesting Bank Users...")
    print("  Skipping (requires bank_id mapping to existing banks)")

def ingest_demo_scenarios(db, df):
    print("Ingesting Demo Scenarios...")
    db.execute(text("DELETE FROM demo_scenarios"))
    db.commit()
    
    for _, row in df.iterrows():
        scenario = DemoScenario(
            scenario=str(row.get('scenario', '')) if pd.notna(row.get('scenario')) else None,
            description=str(row.get('description', '')) if pd.notna(row.get('description')) else None
        )
        db.add(scenario)
    db.commit()
    print(f"  Ingested {len(df)} demo scenarios")

def main():
    excel_path = os.path.join(os.path.dirname(__file__), "I4C_Simulated_Demo_Dataset.xlsx")
    
    if not os.path.exists(excel_path):
        print(f"Error: Excel file not found at {excel_path}")
        sys.exit(1)
    
    print(f"Loading Excel file: {excel_path}")
    xl = pd.ExcelFile(excel_path)
    
    print(f"Found sheets: {xl.sheet_names}")
    print()
    
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created/verified.")
    print()
    
    db = SessionLocal()
    
    try:
        sheet_handlers = {
            'I4C_Inbound_FraudReports': ingest_fraud_reports,
            'I4C_Incidents': ingest_incidents,
            'Bank_Case_Workflow': ingest_case_workflows,
            'Bank_Hold_Actions': ingest_hold_actions,
            'Bank_StatusUpdate_Request': ingest_status_update_requests,
            'Bank_StatusUpdate_TxnDetails': ingest_status_update_txn_details,
            'I4C_StatusUpdate_Response': ingest_i4c_responses,
            'Workflow_Timeline': ingest_workflow_timeline,
            'Meta_BankMaster': ingest_bank_master,
            'Meta_StatusCodes': ingest_status_codes,
            'Bank_Branches': ingest_bank_branches,
            'Bank_Users': ingest_bank_users,
            'Demo_Scenarios': ingest_demo_scenarios,
        }
        
        for sheet_name in xl.sheet_names:
            if sheet_name in ['README']:
                print(f"Skipping {sheet_name}")
                continue
            
            if sheet_name in sheet_handlers:
                df = pd.read_excel(xl, sheet_name=sheet_name)
                print(f"\nProcessing sheet: {sheet_name} ({len(df)} rows)")
                sheet_handlers[sheet_name](db, df)
            else:
                print(f"Warning: No handler for sheet {sheet_name}")
        
        print("\n" + "="*50)
        print("Ingestion completed successfully!")
        print("="*50)
        
    except Exception as e:
        print(f"\nError during ingestion: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
