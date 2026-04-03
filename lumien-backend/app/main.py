from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .routers import auth, complaints, admin, i4c, bank, tenant, operations, i4c_dataset, cases, demo_upload
from .models.models import Base
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .models import models
from .core import security
from pydantic import BaseModel

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Database initialization (PostgreSQL)
engine = create_engine(settings.DATABASE_URL)
Base.metadata.create_all(bind=engine)


def _ensure_timeline_event_type_enum_values() -> None:
    """Idempotently add new enum values to the Postgres timelineeventtype enum."""
    # Postgres enum values must be migrated separately; otherwise inserts will fail with
    # 'invalid input value for enum ...'.
    statements = [
        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid WHERE t.typname = 'timelineeventtype' AND e.enumlabel = 'CASE_STATUS_UPDATED') THEN ALTER TYPE timelineeventtype ADD VALUE 'CASE_STATUS_UPDATED'; END IF; END $$;",
        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid WHERE t.typname = 'timelineeventtype' AND e.enumlabel = 'EVIDENCE_UPLOADED') THEN ALTER TYPE timelineeventtype ADD VALUE 'EVIDENCE_UPLOADED'; END IF; END $$;",
    ]

    try:
        with engine.begin() as conn:
            for stmt in statements:
                conn.execute(text(stmt))
    except Exception:
        # If DB isn't Postgres or enum doesn't exist yet, ignore.
        # The main app will still start; errors will surface if inserts happen without enum support.
        pass


def _seed_friendly_bank_users():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        # Ensure roles exist
        bank_role = db.query(models.Role).filter(models.Role.name == "Bank HQ Integration User").first()
        if not bank_role:
            bank_role = models.Role(name="Bank HQ Integration User", description="Bank User")
            db.add(bank_role)
            db.flush()

        admin_role = db.query(models.Role).filter(models.Role.name == "Lumien Super Admin").first()
        if not admin_role:
            admin_role = models.Role(name="Lumien Super Admin", description="Platform Administrator")
            db.add(admin_role)
            db.flush()

        # Create predictable usernames derived from IFSC prefix
        # Bank codes in DB can be numeric, so we cannot rely on bank.code for usernames.
        prefix_to_username = {
            "SBIN": "sbi_user",
            "HDFC": "hdfc_user",
            "ICIC": "icici_user",
            "UTIB": "axis_user",
            "PUNB": "pnb_user",
            "BARB": "bob_user",
            "KKBK": "kotak_user",
            "YESB": "yes_user",
            "INDB": "indusind_user",
            "IDFB": "idfc_user",
            "CNRB": "canara_user",
            "UBIN": "union_user",
            "UCBA": "uco_user",
        }

        banks = db.query(models.Bank).all()
        for bank in banks:
            ifsc_prefix_raw = (bank.ifsc_prefix or "")
            ifsc_prefix = str(ifsc_prefix_raw).strip().upper()
            if ifsc_prefix in {"NAN", "NONE", "NULL"}:
                ifsc_prefix = ""

            username = None
            if ifsc_prefix:
                username = prefix_to_username.get(ifsc_prefix)

            if not username:
                bank_name = (bank.name or "").strip().lower()
                if "state bank" in bank_name or bank_name == "sbi" or bank_name.startswith("sbi"):
                    username = "sbi_user"
                elif "hdfc" in bank_name:
                    username = "hdfc_user"
                elif "icici" in bank_name:
                    username = "icici_user"
                elif "axis" in bank_name:
                    username = "axis_user"
                elif "punjab national" in bank_name or "pnb" in bank_name:
                    username = "pnb_user"
                elif "baroda" in bank_name:
                    username = "bob_user"
                elif "kotak" in bank_name:
                    username = "kotak_user"
                elif bank_name.startswith("yes") or "yes bank" in bank_name:
                    username = "yes_user"
                elif "indusind" in bank_name:
                    username = "indusind_user"
                elif "idfc" in bank_name:
                    username = "idfc_user"
                elif "canara" in bank_name:
                    username = "canara_user"
                elif "union bank" in bank_name:
                    username = "union_user"
                elif "uco" in bank_name:
                    username = "uco_user"

            if not username:
                continue

            existing = db.query(models.User).filter(models.User.username == username).first()
            if existing:
                continue

            branch = (
                db.query(models.Branch)
                .filter(models.Branch.bank_id == bank.id)
                .order_by(models.Branch.id.asc())
                .first()
            )

            user = models.User(
                username=username,
                email=f"{username}@lumien.local",
                hashed_password=security.get_password_hash("password123"),
                is_active=True,
                bank_id=bank.id,
                branch_id=branch.id if branch else None,
                roles=[bank_role],
            )
            db.add(user)

        # Ensure platform admin exists
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin_user:
            admin_user = models.User(
                username="admin",
                email="admin@lumien.local",
                hashed_password=security.get_password_hash("password123"),
                is_active=True,
                bank_id=None,
                branch_id=None,
                roles=[admin_role],
            )
            db.add(admin_user)

        db.commit()
    finally:
        db.close()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(i4c.router, prefix=f"{settings.API_V1_STR}/i4c", tags=["I4C Ingestion"])
# app.include_router(complaints.router, prefix=f"{settings.API_V1_STR}/cases", tags=["Case Management"])  # OLD - replaced by unified cases
app.include_router(cases.router, prefix="", tags=["Unified Cases"])  # cases.router already has /api/v1/cases prefix
app.include_router(bank.router, prefix=f"{settings.API_V1_STR}/bank", tags=["Bank Operations"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["Administration"])
app.include_router(tenant.router, prefix=f"{settings.API_V1_STR}/tenant", tags=["Multi-Tenant Operations"])
app.include_router(operations.router, prefix=f"{settings.API_V1_STR}/operations", tags=["Operations"])
app.include_router(i4c_dataset.router, prefix=f"{settings.API_V1_STR}/i4c-dataset", tags=["I4C Dataset"])
app.include_router(demo_upload.router, prefix=f"{settings.API_V1_STR}/demo", tags=["Demo Upload"])


@app.on_event("startup")
def _startup_seed_data():
    _ensure_timeline_event_type_enum_values()
    _seed_friendly_bank_users()

@app.get("/")
def root():
    return {"message": "LUMIEN API is operational", "status": "healthy"}


class MockI4CFraudReportStatusUpdateRequest(BaseModel):
    acknowledgement_no: str
    job_id: str | None = None
    txn_details: list[dict] | None = None
    status_code: str | None = None
    remarks: str | None = None


@app.post("/banking/FraudReportStatusUpdate")
def mock_i4c_fraud_report_status_update(_: MockI4CFraudReportStatusUpdateRequest):
    return {
        "response_code": "00",
        "message": "Success",
    }
