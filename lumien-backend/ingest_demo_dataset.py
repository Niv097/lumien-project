"""
Dynamic Multi-Tenant Excel Data Ingestion Script for FIDUCIA

This script ingests data from the I4C Simulated Demo Dataset Excel file
and populates the database with proper multi-tenancy support:
- Banks from Meta_BankMaster
- Branches from Bank_Branches
- Users from Bank_Users
- Cases, Workflows, Status Updates, Hold Actions with proper foreign key links
"""

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import uuid
import os
import sys
import json
import re

# Add the app directory to sys.path to import models
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.models.models import (
    Base, Complaint, EnrichmentResult, Bank, Branch, User, Role,
    RoutingLog, BankResponse, SLATracking, CaseStatus, AuditLog,
    CaseWorkflow, StatusUpdate, HoldAction, StateTransition,
    KYCPack, LEAResponse, Grievance, RestorationOrder, ReconciliationItem,
    DemoReadme, DemoI4CInboundFraudReport, DemoI4CIncident,
    DemoBankCaseWorkflow, DemoBankHoldAction,
    DemoBankStatusUpdateRequest, DemoBankStatusUpdateTxnDetail,
    DemoI4CStatusUpdateResponse, DemoWorkflowTimeline,
    MetaStatusCode, DemoScenario
)
from app.core.config import settings
from app.core.security import get_password_hash

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Excel file path - using relative path for portability
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "I4C_Simulated_Demo_Dataset.xlsx")
if len(sys.argv) > 1 and sys.argv[1].endswith('.xlsx'):
    EXCEL_PATH = sys.argv[1]
EXCEL_PATH = os.path.abspath(EXCEL_PATH)


def clear_existing_data(db):
    """Clear all existing data from tables in proper order (child tables first)"""
    print("Clearing existing data...")
    
    # Delete in order of dependencies (children first)
    # Handle many-to-many relationship first
    db.execute(text("DELETE FROM user_roles"))
    
    # Clear all tables that reference users (must come before User delete)
    for tbl in [
        "login_audit", "notifications", "notification_preferences",
        "case_evidence", "timeline", "evidence", "export_logs",
        "api_inbox", "api_outbox", "i4c_status_updates",
        "i4c_transactions", "i4c_fraud_reports", "cases",
    ]:
        try:
            db.execute(text(f"DELETE FROM {tbl}"))
        except Exception:
            pass  # table may not exist yet
    
    db.query(HoldAction).delete()
    db.query(StatusUpdate).delete()
    db.query(CaseWorkflow).delete()
    db.query(StateTransition).delete()
    db.query(AuditLog).delete()
    db.query(BankResponse).delete()
    db.query(RoutingLog).delete()
    db.query(SLATracking).delete()
    db.query(EnrichmentResult).delete()
    # Operations tables (must be cleared before Complaints)
    db.query(ReconciliationItem).delete()
    db.query(RestorationOrder).delete()
    db.query(Grievance).delete()
    db.query(LEAResponse).delete()
    db.query(KYCPack).delete()
    db.query(Complaint).delete()

    db.query(DemoBankStatusUpdateTxnDetail).delete()
    db.query(DemoBankStatusUpdateRequest).delete()
    db.query(DemoI4CStatusUpdateResponse).delete()
    db.query(DemoWorkflowTimeline).delete()
    db.query(DemoBankHoldAction).delete()
    db.query(DemoBankCaseWorkflow).delete()
    db.query(DemoI4CIncident).delete()
    db.query(DemoI4CInboundFraudReport).delete()
    db.query(DemoScenario).delete()
    db.query(MetaStatusCode).delete()
    db.query(DemoReadme).delete()
    db.query(User).delete()
    db.query(Branch).delete()
    db.query(Bank).delete()
    db.query(Role).delete()
    
    db.commit()
    print("Existing data cleared.")


def _parse_dt(value):
    if value is None or (isinstance(value, float) and pd.isna(value)) or pd.isna(value):
        return None
    try:
        dt = pd.to_datetime(value)
        if pd.isna(dt):
            return None
        return dt.to_pydatetime() if hasattr(dt, "to_pydatetime") else dt
    except Exception:
        return None


def ingest_demo_readme(db, df_readme):
    if df_readme is None or df_readme.empty:
        return
    col = df_readme.columns.tolist()[0] if len(df_readme.columns) else None
    if not col:
        return
    for _, row in df_readme.iterrows():
        db.add(DemoReadme(line=str(row.get(col, "")).strip()))
    db.commit()


def ingest_meta_status_codes(db, df_status_codes):
    if df_status_codes is None or df_status_codes.empty:
        return
    for _, row in df_status_codes.iterrows():
        code = str(row.get("status_code", "")).strip()
        if not code:
            continue
        db.add(MetaStatusCode(
            status_code=code,
            status_label=str(row.get("status_label", "")).strip() if pd.notna(row.get("status_label")) else None,
            meaning=str(row.get("meaning", "")).strip() if pd.notna(row.get("meaning")) else None,
            owner=str(row.get("owner", "")).strip() if pd.notna(row.get("owner")) else None,
            demo_example_usage=str(row.get("demo_example_usage", "")).strip() if pd.notna(row.get("demo_example_usage")) else None,
        ))
    db.commit()


def ingest_demo_scenarios(db, df_scenarios):
    if df_scenarios is None or df_scenarios.empty:
        return
    for _, row in df_scenarios.iterrows():
        scenario = str(row.get("scenario", "")).strip()
        if not scenario:
            continue
        db.add(DemoScenario(
            scenario=scenario,
            description=str(row.get("description", "")).strip() if pd.notna(row.get("description")) else None,
        ))
    db.commit()


def ingest_demo_i4c_inbound_fraud_reports(db, df_reports):
    if df_reports is None or df_reports.empty:
        return
    for _, row in df_reports.iterrows():
        ack = str(row.get("acknowledgement_no", "")).strip()
        db.add(DemoI4CInboundFraudReport(
            acknowledgement_no=ack,
            sub_category=str(row.get("sub_category", "")).strip() if pd.notna(row.get("sub_category")) else None,
            requestor=str(row.get("requestor", "")).strip() if pd.notna(row.get("requestor")) else None,
            payer_bank=str(row.get("payer_bank", "")).strip() if pd.notna(row.get("payer_bank")) else None,
            payer_bank_code=str(row.get("payer_bank_code", "")).strip() if pd.notna(row.get("payer_bank_code")) else None,
            mode_of_payment=str(row.get("mode_of_payment", "")).strip() if pd.notna(row.get("mode_of_payment")) else None,
            payer_mobile_number=str(row.get("payer_mobile_number", "")).strip() if pd.notna(row.get("payer_mobile_number")) else None,
            payer_account_number=str(row.get("payer_account_number", "")).strip() if pd.notna(row.get("payer_account_number")) else None,
            state=str(row.get("state", "")).strip() if pd.notna(row.get("state")) else None,
            district=str(row.get("district", "")).strip() if pd.notna(row.get("district")) else None,
            transaction_type=str(row.get("transaction_type", "")).strip() if pd.notna(row.get("transaction_type")) else None,
            wallet=str(row.get("wallet", "")).strip() if pd.notna(row.get("wallet")) else None,
            received_at=_parse_dt(row.get("received_at")),
            incident_count=int(row.get("incident_count")) if pd.notna(row.get("incident_count")) else None,
            total_disputed_amount=float(row.get("total_disputed_amount")) if pd.notna(row.get("total_disputed_amount")) else None,
            bank_ack_response_code=str(row.get("bank_ack_response_code", "")).strip() if pd.notna(row.get("bank_ack_response_code")) else None,
            bank_job_id=str(row.get("bank_job_id", "")).strip() if pd.notna(row.get("bank_job_id")) else None,
            calc_total_disputed_amount=float(row.get("calc_total_disputed_amount")) if pd.notna(row.get("calc_total_disputed_amount")) else None,
            amount_match_flag=str(row.get("amount_match_flag", "")).strip() if pd.notna(row.get("amount_match_flag")) else None,
        ))
    db.commit()


def ingest_demo_i4c_incidents(db, df_incidents):
    if df_incidents is None or df_incidents.empty:
        return
    for _, row in df_incidents.iterrows():
        db.add(DemoI4CIncident(
            acknowledgement_no=str(row.get("acknowledgement_no", "")).strip(),
            incident_id=str(row.get("incident_id", "")).strip() if pd.notna(row.get("incident_id")) else None,
            sub_category=str(row.get("sub_category", "")).strip() if pd.notna(row.get("sub_category")) else None,
            amount=float(row.get("amount")) if pd.notna(row.get("amount")) else None,
            rrn=str(row.get("rrn", "")).strip() if pd.notna(row.get("rrn")) else None,
            transaction_date=_parse_dt(row.get("transaction_date")),
            transaction_time=str(row.get("transaction_time", "")).strip() if pd.notna(row.get("transaction_time")) else None,
            disputed_amount=float(row.get("disputed_amount")) if pd.notna(row.get("disputed_amount")) else None,
            layer=int(row.get("layer")) if pd.notna(row.get("layer")) else None,
            payee_bank=str(row.get("payee_bank", "")).strip() if pd.notna(row.get("payee_bank")) else None,
            payee_bank_code=str(row.get("payee_bank_code", "")).strip() if pd.notna(row.get("payee_bank_code")) else None,
            payee_ifsc_code=str(row.get("payee_ifsc_code", "")).strip() if pd.notna(row.get("payee_ifsc_code")) else None,
            payee_account_number=str(row.get("payee_account_number", "")).strip() if pd.notna(row.get("payee_account_number")) else None,
        ))
    db.commit()


def ingest_demo_bank_case_workflow(db, df_workflow):
    if df_workflow is None or df_workflow.empty:
        return
    for _, row in df_workflow.iterrows():
        db.add(DemoBankCaseWorkflow(
            case_id=str(row.get("case_id", "")).strip(),
            acknowledgement_no=str(row.get("acknowledgement_no", "")).strip(),
            job_id=str(row.get("job_id", "")).strip() if pd.notna(row.get("job_id")) else None,
            created_at=_parse_dt(row.get("created_at")),
            assigned_queue=str(row.get("assigned_queue", "")).strip() if pd.notna(row.get("assigned_queue")) else None,
            assigned_branch_id=str(row.get("assigned_branch_id", "")).strip() if pd.notna(row.get("assigned_branch_id")) else None,
            priority=str(row.get("priority", "")).strip() if pd.notna(row.get("priority")) else None,
            current_state=str(row.get("current_state", "")).strip() if pd.notna(row.get("current_state")) else None,
            scenario=str(row.get("scenario", "")).strip() if pd.notna(row.get("scenario")) else None,
        ))
    db.commit()


def ingest_demo_bank_hold_actions(db, df_holds):
    if df_holds is None or df_holds.empty:
        return
    for _, row in df_holds.iterrows():
        db.add(DemoBankHoldAction(
            action_id=str(row.get("action_id", "")).strip() if pd.notna(row.get("action_id")) else None,
            case_id=str(row.get("case_id", "")).strip(),
            acknowledgement_no=str(row.get("acknowledgement_no", "")).strip(),
            incident_id=str(row.get("incident_id", "")).strip() if pd.notna(row.get("incident_id")) else None,
            action_type=str(row.get("action_type", "")).strip() if pd.notna(row.get("action_type")) else None,
            action_time=_parse_dt(row.get("action_time")),
            requested_amount=float(row.get("requested_amount")) if pd.notna(row.get("requested_amount")) else None,
            action_amount=float(row.get("action_amount")) if pd.notna(row.get("action_amount")) else None,
            held_amount=float(row.get("held_amount")) if pd.notna(row.get("held_amount")) else None,
            hold_reference=str(row.get("hold_reference", "")).strip() if pd.notna(row.get("hold_reference")) else None,
            negative_lien_flag=str(row.get("negative_lien_flag", "")).strip() if pd.notna(row.get("negative_lien_flag")) else None,
            outcome=str(row.get("outcome", "")).strip() if pd.notna(row.get("outcome")) else None,
            remarks=str(row.get("remarks", "")).strip() if pd.notna(row.get("remarks")) else None,
        ))
    db.commit()


def ingest_demo_bank_statusupdate_request(db, df_requests):
    if df_requests is None or df_requests.empty:
        return
    for _, row in df_requests.iterrows():
        db.add(DemoBankStatusUpdateRequest(
            request_id=str(row.get("request_id", "")).strip(),
            acknowledgement_no=str(row.get("acknowledgement_no", "")).strip(),
            job_id=str(row.get("job_id", "")).strip() if pd.notna(row.get("job_id")) else None,
            sent_at=_parse_dt(row.get("sent_at")),
            content_type=str(row.get("content_type", "")).strip() if pd.notna(row.get("content_type")) else None,
            authorization_type=str(row.get("authorization_type", "")).strip() if pd.notna(row.get("authorization_type")) else None,
            payload_encrypted=str(row.get("payload_encrypted", "")).strip() if pd.notna(row.get("payload_encrypted")) else None,
            transaction_count=int(row.get("transaction_count")) if pd.notna(row.get("transaction_count")) else None,
        ))
    db.commit()


def ingest_demo_bank_statusupdate_txndetails(db, df_txn):
    if df_txn is None or df_txn.empty:
        return
    for _, row in df_txn.iterrows():
        db.add(DemoBankStatusUpdateTxnDetail(
            request_id=str(row.get("request_id", "")).strip(),
            acknowledgement_no=str(row.get("acknowledgement_no", "")).strip(),
            job_id=str(row.get("job_id", "")).strip() if pd.notna(row.get("job_id")) else None,
            incident_id=str(row.get("incident_id", "")).strip() if pd.notna(row.get("incident_id")) else None,
            root_rrn_transaction_id=str(row.get("root_rrn_transaction_id", "")).strip() if pd.notna(row.get("root_rrn_transaction_id")) else None,
            root_bankid=str(row.get("root_bankid", "")).strip() if pd.notna(row.get("root_bankid")) else None,
            root_account_number=str(row.get("root_account_number", "")).strip() if pd.notna(row.get("root_account_number")) else None,
            amount=float(row.get("amount")) if pd.notna(row.get("amount")) else None,
            transaction_datetime=_parse_dt(row.get("transaction_datetime")),
            disputed_amount=float(row.get("disputed_amount")) if pd.notna(row.get("disputed_amount")) else None,
            status_code=str(row.get("status_code", "")).strip() if pd.notna(row.get("status_code")) else None,
            remarks=str(row.get("remarks", "")).strip() if pd.notna(row.get("remarks")) else None,
            phone_number=str(row.get("phone_number", "")).strip() if pd.notna(row.get("phone_number")) else None,
            pan_number=str(row.get("pan_number", "")).strip() if pd.notna(row.get("pan_number")) else None,
            email=str(row.get("email", "")).strip() if pd.notna(row.get("email")) else None,
            root_ifsc_code=str(row.get("root_ifsc_code", "")).strip() if pd.notna(row.get("root_ifsc_code")) else None,
            root_effective_balance=float(row.get("root_effective_balance")) if pd.notna(row.get("root_effective_balance")) else None,
            negative_lien_flag=str(row.get("negative_lien_flag", "")).strip() if pd.notna(row.get("negative_lien_flag")) else None,
            hold_reference=str(row.get("hold_reference", "")).strip() if pd.notna(row.get("hold_reference")) else None,
            held_amount=float(row.get("held_amount")) if pd.notna(row.get("held_amount")) else None,
        ))
    db.commit()


def ingest_demo_i4c_statusupdate_response(db, df_resp):
    if df_resp is None or df_resp.empty:
        return
    for _, row in df_resp.iterrows():
        db.add(DemoI4CStatusUpdateResponse(
            request_id=str(row.get("request_id", "")).strip(),
            i4c_response_code=str(row.get("i4c_response_code", "")).strip() if pd.notna(row.get("i4c_response_code")) else None,
            i4c_message=str(row.get("i4c_message", "")).strip() if pd.notna(row.get("i4c_message")) else None,
            received_at=_parse_dt(row.get("received_at")),
            error_flag=str(row.get("error_flag", "")).strip() if pd.notna(row.get("error_flag")) else None,
        ))
    db.commit()


def ingest_demo_workflow_timeline(db, df_timeline):
    if df_timeline is None or df_timeline.empty:
        return
    for _, row in df_timeline.iterrows():
        db.add(DemoWorkflowTimeline(
            case_id=str(row.get("case_id", "")).strip(),
            acknowledgement_no=str(row.get("acknowledgement_no", "")).strip(),
            job_id=str(row.get("job_id", "")).strip() if pd.notna(row.get("job_id")) else None,
            step_no=int(row.get("step_no")) if pd.notna(row.get("step_no")) else None,
            step_name=str(row.get("step_name", "")).strip() if pd.notna(row.get("step_name")) else None,
            actor=str(row.get("actor", "")).strip() if pd.notna(row.get("actor")) else None,
            start_time=_parse_dt(row.get("start_time")),
            end_time=_parse_dt(row.get("end_time")),
            step_status=str(row.get("step_status", "")).strip() if pd.notna(row.get("step_status")) else None,
            sla_target_minutes=int(row.get("sla_target_minutes")) if pd.notna(row.get("sla_target_minutes")) else None,
            actual_minutes=int(row.get("actual_minutes")) if pd.notna(row.get("actual_minutes")) else None,
            sla_breached=str(row.get("sla_breached", "")).strip() if pd.notna(row.get("sla_breached")) else None,
        ))
    db.commit()


def ingest_banks(db, df_bank_master):
    """Ingest banks from Meta_BankMaster sheet"""
    print(f"Ingesting {len(df_bank_master)} banks...")
    
    bank_map = {}  # code -> Bank object
    
    for _, row in df_bank_master.iterrows():
        bank_code = str(row.get('bank_code', '')).strip()
        bank_name = str(row.get('bank_name', '')).strip()
        
        if not bank_code or not bank_name:
            continue
            
        bank = Bank(
            name=bank_name,
            code=bank_code,
            ifsc_prefix=str(row.get('ifsc_prefix', ''))[:10],
            integration_model=str(row.get('integration_model', 'MANUAL')),
            sla_hours=int(row.get('sla_hours', 24)) if pd.notna(row.get('sla_hours')) else 24,
            is_active=True
        )
        db.add(bank)
        db.flush()
        bank_map[bank_code] = bank
        print(f"  Created bank: {bank_name} ({bank_code}) - ID: {bank.id}")
    
    db.commit()
    return bank_map


def ingest_branches(db, df_branches, bank_map):
    """Ingest branches from Bank_Branches sheet using ifsc_prefix to link to banks"""
    print(f"Ingesting {len(df_branches)} branches...")
    
    branch_map = {}  # branch_id -> Branch object
    
    # Build ifsc_prefix -> bank mapping
    ifsc_to_bank = {}
    for code, bank in bank_map.items():
        if bank.ifsc_prefix:
            ifsc_to_bank[bank.ifsc_prefix.upper()] = bank
    
    for _, row in df_branches.iterrows():
        branch_id = str(row.get('branch_id', '')).strip()
        ifsc_prefix = str(row.get('ifsc_prefix', '')).strip().upper()
        
        if not branch_id:
            continue
        
        # Find the bank by ifsc_prefix
        bank = ifsc_to_bank.get(ifsc_prefix)
        if not bank:
            print(f"  Warning: No bank found with IFSC prefix '{ifsc_prefix}' for branch {branch_id}")
            continue
        
        branch = Branch(
            bank_id=bank.id,
            branch_code=branch_id,
            branch_name=str(row.get('branch_name', '')).strip() or branch_id,
            ifsc_code=str(row.get('ifsc_prefix', '')).strip(),
            address=f"{row.get('district', '')}, {row.get('state', '')}".strip(', '),
            city=str(row.get('district', '')).strip(),
            state=str(row.get('state', '')).strip(),
            is_active=True
        )
        db.add(branch)
        db.flush()
        branch_map[branch_id] = branch
        print(f"  Created branch: {branch_id} for bank {bank.name} - ID: {branch.id}")
    
    db.commit()
    return branch_map


def ingest_users(db, df_users, bank_map, branch_map):
    """Ingest users from Bank_Users sheet"""
    print(f"Ingesting {len(df_users)} users...")
    print(f"Available columns: {df_users.columns.tolist()}")
    
    user_map = {}  # username -> User object
    
    # Get or create default roles
    admin_role = db.query(Role).filter(Role.name == "Lumien Super Admin").first()
    if not admin_role:
        admin_role = Role(name="Lumien Super Admin", description="Platform Administrator")
        db.add(admin_role)
    
    bank_role = db.query(Role).filter(Role.name == "Bank HQ Integration User").first()
    if not bank_role:
        bank_role = Role(name="Bank HQ Integration User", description="Bank User")
        db.add(bank_role)
    
    ops_role = db.query(Role).filter(Role.name == "Lumien Operations Manager").first()
    if not ops_role:
        ops_role = Role(name="Lumien Operations Manager", description="Operations")
        db.add(ops_role)
    
    db.flush()
    
    for _, row in df_users.iterrows():
        # Excel columns observed: user_id, full_name, role, branch_id, email, mobile
        username = str(row.get('user_id', '')).strip()
        if not username:
            username = str(row.get('username', row.get('user_name', ''))).strip()

        email = str(row.get('email', '')).strip() if pd.notna(row.get('email')) else ''
        if not email:
            email = f"{username}@lumien.local"

        branch_id_col = str(row.get('branch_id', '')).strip() if pd.notna(row.get('branch_id')) else ''
        
        if not username:
            continue
        
        # Find bank and branch
        bank_id = None
        branch_id = None
        
        # Try to find branch by branch_id
        if branch_id_col:
            branch = branch_map.get(branch_id_col)
            if branch:
                branch_id = branch.id
                bank_id = branch.bank_id
            else:
                # Try to extract bank code from branch_id (e.g., BR-SBI-001 -> SBI)
                parts = branch_id_col.split('-')
                if len(parts) >= 2:
                    bank_code = parts[1]
                    bank = bank_map.get(bank_code)
                    if bank:
                        bank_id = bank.id
        
        # Default password for seed users
        password_hash = get_password_hash('password123')
        
        user = User(
            username=username,
            email=email,
            hashed_password=password_hash,
            is_active=True,
            bank_id=bank_id,
            branch_id=branch_id
        )
        
        # Assign role from Excel 'role' column
        # Map dataset roles -> app roles used by RoleChecker
        excel_role = str(row.get('role', '')).strip().upper() if pd.notna(row.get('role')) else ''
        if excel_role in {"ADMIN", "SUPER_ADMIN", "LUMIEN_ADMIN"}:
            user.roles = [admin_role]
        elif excel_role in {"OPERATIONS", "OPS", "LUMIEN_OPS"}:
            user.roles = [ops_role]
        else:
            # MAKER / CHECKER / BRANCH_USER / anything else => bank user
            user.roles = [bank_role]
        
        db.add(user)
        db.flush()
        user_map[username] = user
        print(f"  Created user: {username} (Bank ID: {bank_id}, Branch ID: {branch_id}) - ID: {user.id}")
    
    db.commit()
    return user_map


def ingest_complaints(db, df_reports, df_incidents, bank_map, branch_map):
    """Ingest complaints from I4C_Inbound_FraudReports and I4C_Incidents"""
    print(f"Ingesting {len(df_reports)} complaints...")
    
    complaint_map = {}  # acknowledgement_no -> Complaint object
    
    for _, row in df_reports.iterrows():
        ack_no = str(int(row['acknowledgement_no'])) if pd.notna(row.get('acknowledgement_no')) else None
        if not ack_no:
            continue
        
        # Find associated incident for amount/date
        incident_row = None
        if df_incidents is not None and not df_incidents.empty:
            incident_matches = df_incidents[df_incidents['acknowledgement_no'] == row['acknowledgement_no']]
            if not incident_matches.empty:
                incident_row = incident_matches.iloc[0]
        
        # Determine bank and branch from payer_bank
        payer_bank_name = str(row.get('payer_bank', '')).strip()
        bank_id = None
        branch_id = None
        
        # Try to match bank by name or code
        for code, bank in bank_map.items():
            if code.upper() in payer_bank_name.upper() or payer_bank_name.upper() in bank.name.upper():
                bank_id = bank.id
                # Try to find a default branch for this bank
                default_branch = db.query(Branch).filter(Branch.bank_id == bank.id).first()
                if default_branch:
                    branch_id = default_branch.id
                break
        
        # Create complaint
        incident_date = datetime.utcnow()
        if incident_row is not None and pd.notna(incident_row.get('transaction_date')):
            try:
                incident_date = pd.to_datetime(incident_row['transaction_date'])
            except:
                pass
        
        amount = 0.0
        if incident_row is not None and pd.notna(incident_row.get('amount')):
            try:
                amount = float(incident_row['amount'])
            except:
                pass
        
        complaint = Complaint(
            complaint_id=ack_no,
            victim_name=f"Victim_{ack_no[-4:]}" if len(ack_no) >= 4 else f"Victim_{ack_no}",
            victim_mobile=str(row.get('payer_mobile_number', '')).strip(),
            incident_date=incident_date,
            fraud_type=str(row.get('sub_category', 'Unknown')),
            amount=amount,
            currency="INR",
            ifsc_signal=str(row.get('payer_bank_ifsc', '')).strip() if pd.notna(row.get('payer_bank_ifsc')) else None,
            status=CaseStatus.INGESTED,
            bank_id=bank_id,
            branch_id=branch_id
        )
        db.add(complaint)
        db.flush()
        complaint_map[ack_no] = complaint
        
        # Create enrichment result
        if bank_id:
            enrichment = EnrichmentResult(
                complaint_id=complaint.id,
                target_bank_id=bank_id,
                target_branch_id=branch_id,
                confidence_score=0.95,
                signals=json.dumps({"bank_name_match": payer_bank_name, "ifsc": complaint.ifsc_signal}),
                validation_method="METADATA_MATCH"
            )
            db.add(enrichment)
            
            # Create routing log
            routing = RoutingLog(
                complaint_id=complaint.id,
                bank_id=bank_id,
                branch_id=branch_id,
                request_id=f"ROUTE-{uuid.uuid4().hex[:12].upper()}",
                status="SUCCESS"
            )
            db.add(routing)
            
            # Create SLA tracking
            sla = SLATracking(
                complaint_id=complaint.id,
                bank_id=bank_id,
                branch_id=branch_id,
                start_time=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(sla)
            
            # Update status to ROUTED
            complaint.status = CaseStatus.ROUTED
    
    db.commit()
    return complaint_map


def ingest_workflows(db, df_workflow, complaint_map, bank_map, branch_map):
    """Ingest workflows from Bank_Case_Workflow sheet"""
    print(f"Ingesting {len(df_workflow)} workflows...")
    
    workflow_map = {}  # case_id -> workflow record
    
    for _, row in df_workflow.iterrows():
        case_id = str(row.get('case_id', '')).strip()
        ack_no = str(int(row['acknowledgement_no'])) if pd.notna(row.get('acknowledgement_no')) else None
        
        if not case_id:
            continue
        
        # Get complaint
        complaint = complaint_map.get(ack_no) if ack_no else None
        
        # Parse assigned_branch_id to get bank and branch
        assigned_branch_id = str(row.get('assigned_branch_id', '')).strip()
        bank_id = None
        branch_id = None
        
        if assigned_branch_id:
            # Try to find branch by code
            branch = branch_map.get(assigned_branch_id)
            if branch:
                branch_id = branch.id
                bank_id = branch.bank_id
            else:
                # Try to match by bank code prefix
                parts = assigned_branch_id.split('-')
                if parts:
                    bank = bank_map.get(parts[0])
                    if bank:
                        bank_id = bank.id
        
        # If no bank found, use complaint's bank
        if not bank_id and complaint:
            bank_id = complaint.bank_id
            branch_id = complaint.branch_id
        
        created_at = datetime.utcnow()
        if pd.notna(row.get('created_at')):
            try:
                created_at = pd.to_datetime(row['created_at'])
            except:
                pass
        
        workflow = CaseWorkflow(
            case_id=case_id,
            complaint_id=complaint.id if complaint else None,
            job_id=str(row.get('job_id', '')).strip(),
            acknowledgement_no=ack_no,
            assigned_bank_id=bank_id,
            assigned_branch_id=branch_id,
            scenario=str(row.get('scenario', '')).strip(),
            status=str(row.get('status', 'PENDING')).strip(),
            priority=str(row.get('priority', 'MEDIUM')).strip(),
            created_at=created_at,
            updated_at=created_at,
            remarks=str(row.get('remarks', '')).strip() if pd.notna(row.get('remarks')) else None
        )
        db.add(workflow)
        db.flush()
        workflow_map[case_id] = workflow
    
    db.commit()
    return workflow_map


def ingest_hold_actions(db, df_holds, df_workflow, complaint_map, bank_map, branch_map, workflow_map):
    """Ingest hold actions from Bank_Hold_Actions sheet"""
    print(f"Ingesting {len(df_holds)} hold actions...")
    
    for _, row in df_holds.iterrows():
        case_id = str(row.get('case_id', '')).strip()
        
        if not case_id:
            continue
        
        # Find workflow to get acknowledgement_no
        workflow = workflow_map.get(case_id)
        ack_no = workflow.acknowledgement_no if workflow else None
        
        # Get complaint
        complaint = complaint_map.get(ack_no) if ack_no else None
        
        # Get bank and branch
        bank_id = None
        branch_id = None
        
        if workflow:
            bank_id = workflow.assigned_bank_id
            branch_id = workflow.assigned_branch_id
        elif complaint:
            bank_id = complaint.bank_id
            branch_id = complaint.branch_id
        
        created_at = datetime.utcnow()
        if pd.notna(row.get('created_at')):
            try:
                created_at = pd.to_datetime(row['created_at'])
            except:
                pass
        
        hold_action = HoldAction(
            complaint_id=complaint.id if complaint else None,
            case_id=case_id,
            bank_id=bank_id,
            branch_id=branch_id,
            action_type=str(row.get('action_type', '')).strip(),
            outcome=str(row.get('outcome', '')).strip(),
            held_amount=float(row['held_amount']) if pd.notna(row.get('held_amount')) else 0.0,
            expected_amount=float(row['expected_amount']) if pd.notna(row.get('expected_amount')) else 0.0,
            account_number=str(row.get('account_number', '')).strip() if pd.notna(row.get('account_number')) else None,
            remarks=str(row.get('remarks', '')).strip() if pd.notna(row.get('remarks')) else None,
            created_at=created_at
        )
        db.add(hold_action)
        
        # Update complaint status based on outcome
        if complaint:
            outcome = str(row.get('outcome', '')).upper()
            if 'HOLD' in outcome or 'CONFIRMED' in outcome:
                complaint.status = CaseStatus.HOLD_CONFIRMED
            elif 'PARTIAL' in outcome:
                complaint.status = CaseStatus.PARTIAL_HOLD
            elif 'NOT_RELATED' in outcome or 'REJECTED' in outcome:
                complaint.status = CaseStatus.NOT_RELATED
            elif 'ALREADY_FROZEN' in outcome:
                complaint.status = CaseStatus.ALREADY_FROZEN
    
    db.commit()


def ingest_status_updates(db, df_status_updates, df_txn_details, complaint_map, bank_map, branch_map):
    """Ingest status updates from Bank_StatusUpdate_Request sheet"""
    print(f"Ingesting {len(df_status_updates)} status updates...")
    
    if df_status_updates is None or df_status_updates.empty:
        return

    txn_by_request_id = {}
    if df_txn_details is not None and not df_txn_details.empty and 'request_id' in df_txn_details.columns:
        for _, tx in df_txn_details.iterrows():
            rid = str(tx.get('request_id', '')).strip()
            if not rid:
                continue
            txn_by_request_id.setdefault(rid, []).append(tx)

    for _, row in df_status_updates.iterrows():
        request_id = str(row.get('request_id', '')).strip()
        ack_no = str(int(row['acknowledgement_no'])) if pd.notna(row.get('acknowledgement_no')) else None
        if not ack_no:
            continue

        complaint = complaint_map.get(ack_no)
        bank_id = complaint.bank_id if complaint else None
        branch_id = complaint.branch_id if complaint else None

        created_at = datetime.utcnow()
        if pd.notna(row.get('sent_at')):
            try:
                created_at = pd.to_datetime(row['sent_at'])
            except Exception:
                pass

        txns = txn_by_request_id.get(request_id, [])
        if not txns:
            # Still create a single record so the request is visible
            db.add(StatusUpdate(
                complaint_id=complaint.id if complaint else None,
                bank_id=bank_id,
                branch_id=branch_id,
                update_type="STATUS_UPDATE_REQUEST",
                status_code="",
                previous_status=None,
                new_status="",
                remarks=f"request_id={request_id}",
                created_at=created_at,
            ))
            continue

        for tx in txns:
            status_code = str(tx.get('status_code', '')).strip() if pd.notna(tx.get('status_code')) else ''
            remarks = str(tx.get('remarks', '')).strip() if pd.notna(tx.get('remarks')) else None
            incident_id = str(tx.get('incident_id', '')).strip() if pd.notna(tx.get('incident_id')) else ''
            db.add(StatusUpdate(
                complaint_id=complaint.id if complaint else None,
                bank_id=bank_id,
                branch_id=branch_id,
                update_type="STATUS_UPDATE",
                status_code=status_code,
                previous_status=None,
                new_status=status_code,
                remarks=(f"request_id={request_id} incident_id={incident_id} " + (remarks or "")).strip(),
                created_at=created_at,
            ))
    
    db.commit()


def seed_operations_data(db, complaint_map, bank_map, branch_map):
    """Seed sample data for KYC, LEA, Grievance, Money Restoration, and Reconciliation modules"""
    print("Seeding operations data (KYC, LEA, Grievance, Restoration, Reconciliation)...")
    
    complaints = list(complaint_map.values()) if complaint_map else []
    if not complaints:
        print("No complaints found to link operations data")
        return
    
    # Get some bank users for created_by fields
    users = db.query(User).filter(User.bank_id.isnot(None)).limit(10).all()
    default_user = users[0] if users else None
    
    # Sample LEA agency names
    lea_agencies = ["Mumbai Cyber Crime", "Delhi Police EOW", "Bangalore CCB", "Hyderabad Cyber Cell", "Chennai CCIT"]
    
    # Seed KYC Packs (2-3 per complaint)
    for i, complaint in enumerate(complaints[:20]):  # Limit to first 20 complaints
        bank_id = complaint.bank_id or (list(bank_map.values())[0].id if bank_map else None)
        branch_id = complaint.branch_id
        
        for version in range(1, 3):
            pack_id = f"KYC-{complaint.complaint_id[-6:]}-{version}"
            pack = KYCPack(
                pack_id=pack_id,
                case_id=complaint.complaint_id,
                complaint_id=complaint.id,
                bank_id=bank_id,
                branch_id=branch_id,
                version=version,
                status="SUBMITTED" if version == 1 else "LOCKED",
                mandatory_fields=json.dumps({
                    "voter_id": "XXXX-" + str(i).zfill(4),
                    "aadhaar_masked": "XXXX-XXXX-" + str(i).zfill(4),
                    "pan_masked": "XXXXX" + str(i).zfill(4)
                }),
                attachments=json.dumps([f"identity_doc_v{version}.pdf", "address_proof.pdf"]),
                created_by=default_user.id if default_user else None,
                submitted_at=datetime.utcnow() if version == 1 else None,
                locked_at=datetime.utcnow() if version == 2 else None,
                remarks=f"Version {version} pack for {complaint.complaint_id}"
            )
            db.add(pack)
    
    # Seed LEA Requests (1-2 per complaint)
    for i, complaint in enumerate(complaints[:15]):
        bank_id = complaint.bank_id or (list(bank_map.values())[0].id if bank_map else None)
        branch_id = complaint.branch_id
        agency = lea_agencies[i % len(lea_agencies)]
        
        lea = LEAResponse(
            request_id=f"LEA-{complaint.complaint_id[-6:]}-{uuid.uuid4().hex[:4].upper()}",
            case_id=complaint.complaint_id,
            complaint_id=complaint.id,
            bank_id=bank_id,
            branch_id=branch_id,
            io_name=f"Inspector {i+1}",
            police_station=agency,
            request_received_at=datetime.utcnow() - timedelta(days=5),
            request_attachment=f"lea_request_{i}.pdf",
            acknowledgement_proof=f"ack_proof_{i}.pdf" if i % 2 == 0 else None,
            response_pack=json.dumps({"documents": [f"response_{i}.pdf"]}),
            response_dispatch_proof=f"dispatch_{i}.pdf" if i % 2 != 0 else None,
            dispatched_at=datetime.utcnow() if i % 2 != 0 else None,
            status="ACKNOWLEDGED" if i % 2 == 0 else "RESPONSE_SENT",
            created_by=default_user.id if default_user else None,
            remarks=f"LEA request from {agency}"
        )
        db.add(lea)
    
    # Seed Grievances (1 per complaint)
    grievance_categories = ["SERVICE_DELAY", "DATA_INACCURACY", "HOLD_DISPUTE", "STATUS_MISMATCH"]
    for i, complaint in enumerate(complaints[:25]):
        bank_id = complaint.bank_id or (list(bank_map.values())[0].id if bank_map else None)
        branch_id = complaint.branch_id
        
        grievance = Grievance(
            grievance_id=f"GRV-{complaint.complaint_id[-6:]}-{uuid.uuid4().hex[:4].upper()}",
            case_id=complaint.complaint_id,
            complaint_id=complaint.id,
            bank_id=bank_id,
            branch_id=branch_id,
            grievance_type=grievance_categories[i % len(grievance_categories)],
            escalation_stage=2 if i % 4 == 2 else 1,
            info_furnished_note=f"Info furnished for grievance {i+1}" if i % 2 == 0 else None,
            outcome_code=f"OUTCOME_{i}" if i % 4 == 3 else None,
            release_direction_doc=f"release_doc_{i}.pdf" if i % 4 == 3 else None,
            status="OPEN" if i % 4 == 0 else "ESCALATED" if i % 4 == 2 else "RESOLVED" if i % 4 == 3 else "OPEN",
            opened_at=datetime.utcnow() - timedelta(days=i),
            resolved_at=datetime.utcnow() if i % 4 == 3 else None,
            created_by=default_user.id if default_user else None,
            resolved_by=default_user.id if default_user and i % 4 == 3 else None,
            remarks=f"Grievance #{i+1}"
        )
        db.add(grievance)
    
    # Seed Money Restoration Orders (1 per 3 complaints)
    for i, complaint in enumerate(complaints[::3][:10]):
        bank_id = complaint.bank_id or (list(bank_map.values())[0].id if bank_map else None)
        branch_id = complaint.branch_id
        
        order = RestorationOrder(
            order_id=f"RST-{complaint.complaint_id[-6:]}-{uuid.uuid4().hex[:4].upper()}",
            case_id=complaint.complaint_id,
            complaint_id=complaint.id,
            bank_id=bank_id,
            branch_id=branch_id,
            order_reference=f"COURT/ORD/{2024}/{i+1000}",
            court_authority=f"Metropolitan Magistrate Court {i+1}",
            order_date=datetime.utcnow() - timedelta(days=30),
            order_document=f"court_order_{i}.pdf",
            destination_account=f"12ABCD{i:04d}89",
            beneficiary_name=complaint.victim_name or f"Beneficiary {i+1}",
            amount=complaint.amount * 0.8 if complaint.amount else 50000.0,
            verification_details=json.dumps({"kyc_verified": True, "bank_confirmed": True}),
            status="REGISTERED" if i % 3 == 0 else "VERIFIED" if i % 3 == 1 else "EXECUTED",
            utr_reference=f"UTR{i:08d}" if i % 3 == 2 else None,
            executed_at=datetime.utcnow() - timedelta(days=5) if i % 3 == 2 else None,
            execution_proof=f"execution_receipt_{i}.pdf" if i % 3 == 2 else None,
            created_by=default_user.id if default_user else None,
            approved_by=default_user.id if default_user and i % 3 == 2 else None,
            remarks=f"Restoration order for case {complaint.complaint_id}"
        )
        db.add(order)
    
    # Seed Reconciliation Items (random mismatches)
    mismatch_types = ["AMOUNT_MISMATCH", "STATUS_MISMATCH", "MISSING_CBS", "MISSING_PLATFORM"]
    for i in range(min(30, len(complaints))):
        complaint = complaints[i]
        bank_id = complaint.bank_id or (list(bank_map.values())[0].id if bank_map else None)
        branch_id = complaint.branch_id
        
        mismatch_type = mismatch_types[i % len(mismatch_types)]
        platform_val = str(complaint.amount) if complaint.amount else "10000.00"
        cbs_val = str(complaint.amount * 0.95 if complaint.amount else "9500.00") if mismatch_type == "AMOUNT_MISMATCH" else platform_val
        
        item = ReconciliationItem(
            item_id=f"REC-{uuid.uuid4().hex[:8].upper()}",
            case_id=complaint.complaint_id,
            complaint_id=complaint.id,
            bank_id=bank_id,
            branch_id=branch_id,
            mismatch_type=mismatch_type,
            platform_value=platform_val,
            cbs_value=cbs_val,
            cbs_confirmation_ref=f"CBS/{bank_id}/{2024}/{i+1000}" if bank_id else None,
            status="DETECTED" if i % 3 == 0 else "RESOLVED" if i % 3 == 1 else "CLOSED",
            detected_at=datetime.utcnow() - timedelta(days=10),
            resolved_at=datetime.utcnow() - timedelta(days=5) if i % 3 != 0 else None,
            resolution_notes=f"Reconciled via manual review" if i % 3 != 0 else None,
            remarks=f"Auto-generated reconciliation item #{i+1}"
        )
        db.add(item)
    
    db.commit()
    print(f"Seeded: {db.query(KYCPack).count()} KYC packs, {db.query(LEAResponse).count()} LEA requests, {db.query(Grievance).count()} grievances, {db.query(RestorationOrder).count()} restoration orders, {db.query(ReconciliationItem).count()} reconciliation items")


def ingest():
    """Main ingestion function - uses SmartMapper for dynamic sheet/column discovery"""
    from smart_mapper import SmartMapper

    db = SessionLocal()

    try:
        print(f"Reading dataset from {EXCEL_PATH}...")

        if not os.path.exists(EXCEL_PATH):
            print(f"ERROR: Excel file not found at {EXCEL_PATH}")
            print("Please ensure an Excel (.xlsx) file is available.")
            return

        xl = pd.ExcelFile(EXCEL_PATH)
        print(f"Found sheets: {xl.sheet_names}")

        # ---- SmartMapper: discover sheets & normalize columns ----
        mapper = SmartMapper(xl)

        # Clear existing data
        clear_existing_data(db)

        # Load all sheets via SmartMapper (auto-discovers + normalizes columns)
        df_readme       = mapper.load_sheet('readme')
        df_bank_master  = mapper.load_sheet('banks')
        df_meta_status_codes = mapper.load_sheet('status_codes')
        df_branches     = mapper.load_sheet('branches')
        df_users        = mapper.load_sheet('users')
        df_reports      = mapper.load_sheet('fraud_reports')
        df_incidents    = mapper.load_sheet('incidents')
        df_workflow     = mapper.load_sheet('workflow')
        df_holds        = mapper.load_sheet('hold_actions')
        df_status_updates = mapper.load_sheet('status_updates')
        df_txn_details  = mapper.load_sheet('txn_details')
        df_i4c_statusupdate_response = mapper.load_sheet('status_responses')
        df_workflow_timeline = mapper.load_sheet('timeline')
        df_demo_scenarios = mapper.load_sheet('scenarios')

        # ---- Auto-generate missing core data from available sheets ----
        # If no dedicated banks sheet, extract banks from case/fraud data
        if df_bank_master.empty and not df_reports.empty:
            print("INFO: No banks sheet found. Extracting banks from case data...")
            df_bank_master = mapper.extract_banks_from_cases(df_reports)

        # ---- Ingest demo mirror tables (raw Excel data) ----
        ingest_demo_readme(db, df_readme)
        ingest_meta_status_codes(db, df_meta_status_codes)
        ingest_demo_scenarios(db, df_demo_scenarios)
        ingest_demo_i4c_inbound_fraud_reports(db, df_reports)
        ingest_demo_i4c_incidents(db, df_incidents)
        ingest_demo_bank_case_workflow(db, df_workflow)
        ingest_demo_bank_hold_actions(db, df_holds)
        ingest_demo_bank_statusupdate_request(db, df_status_updates)
        ingest_demo_bank_statusupdate_txndetails(db, df_txn_details)
        ingest_demo_i4c_statusupdate_response(db, df_i4c_statusupdate_response)
        ingest_demo_workflow_timeline(db, df_workflow_timeline)

        # ---- Ingest relational data: Banks -> Branches -> Users -> Cases ----
        bank_map = {}
        branch_map = {}
        user_map = {}
        complaint_map = {}
        workflow_map = {}

        if not df_bank_master.empty:
            bank_map = ingest_banks(db, df_bank_master)
        else:
            print("Warning: No bank data found in any sheet")

        # If no branches sheet, auto-generate default HQ branches
        if df_branches.empty and bank_map:
            print("INFO: No branches sheet found. Generating default branches...")
            bank_names_codes = [(b.name, b.code) for b in bank_map.values()]
            df_branches = mapper.generate_default_branches(bank_names_codes)

        if not df_branches.empty and bank_map:
            branch_map = ingest_branches(db, df_branches, bank_map)
        else:
            print("Warning: No branch data found or no banks ingested")

        # If no users sheet, auto-generate default users
        if df_users.empty and bank_map:
            print("INFO: No users sheet found. Generating default users...")
            bank_names_codes = [(b.name, b.code) for b in bank_map.values()]
            df_users = mapper.generate_default_users(bank_names_codes)

        if not df_users.empty:
            user_map = ingest_users(db, df_users, bank_map, branch_map)
        else:
            print("Warning: No user data found")

        if not df_reports.empty:
            complaint_map = ingest_complaints(db, df_reports, df_incidents, bank_map, branch_map)
        else:
            print("Warning: No fraud reports / case data found")

        if not df_workflow.empty and complaint_map:
            workflow_map = ingest_workflows(db, df_workflow, complaint_map, bank_map, branch_map)
        else:
            print("Warning: No workflow data found or no complaints ingested")

        if not df_holds.empty:
            ingest_hold_actions(db, df_holds, df_workflow, complaint_map, bank_map, branch_map, workflow_map)
        else:
            print("Warning: No hold actions data found")

        if not df_status_updates.empty:
            ingest_status_updates(db, df_status_updates, df_txn_details, complaint_map, bank_map, branch_map)
        else:
            print("Warning: No status update data found")

        # Seed operations data (KYC, LEA, Grievance, Restoration, Reconciliation)
        if complaint_map and bank_map:
            seed_operations_data(db, complaint_map, bank_map, branch_map)
        else:
            print("Warning: Cannot seed operations data - no complaints or banks found")

        print("\n" + "=" * 60)
        print("INGESTION SUMMARY")
        print("=" * 60)
        print(f"Banks ingested: {len(bank_map)}")
        print(f"Branches ingested: {len(branch_map)}")
        print(f"Users ingested: {len(user_map)}")
        print(f"Complaints ingested: {len(complaint_map)}")
        print(f"Workflows ingested: {len(workflow_map)}")
        print(f"Hold actions: {db.query(HoldAction).count()}")
        print(f"Status updates: {db.query(StatusUpdate).count()}")
        print("-" * 60)
        print("OPERATIONS DATA:")
        print(f"  KYC Packs: {db.query(KYCPack).count()}")
        print(f"  LEA Responses: {db.query(LEAResponse).count()}")
        print(f"  Grievances: {db.query(Grievance).count()}")
        print(f"  Restoration Orders: {db.query(RestorationOrder).count()}")
        print(f"  Reconciliation Items: {db.query(ReconciliationItem).count()}")
        print("=" * 60)
        print("Ingestion completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Critical error during ingestion: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    ingest()
