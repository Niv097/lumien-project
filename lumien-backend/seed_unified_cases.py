from datetime import datetime

from sqlalchemy.orm import sessionmaker

from app.main import engine
from app.models import models


def seed(branch_id: int | None = None, enable_demo_access: bool = True, limit: int | None = None):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        if branch_id is not None:
            branch = db.query(models.Branch).filter(models.Branch.id == branch_id).first()
            if branch and enable_demo_access:
                branch.demo_access = True
                db.commit()

        q = db.query(models.DemoI4CInboundFraudReport)
        if limit:
            q = q.limit(limit)
        reports = q.all()

        created = 0
        skipped = 0

        for r in reports:
            case_id = r.acknowledgement_no
            if not case_id:
                skipped += 1
                continue

            existing = db.query(models.Case).filter(models.Case.case_id == case_id).first()
            if existing:
                skipped += 1
                continue

            inc = (
                db.query(models.DemoI4CIncident)
                .filter(models.DemoI4CIncident.acknowledgement_no == case_id)
                .order_by(models.DemoI4CIncident.id.asc())
                .first()
            )

            txn_id = inc.rrn if inc and inc.rrn else case_id
            amt = None
            if inc and inc.amount is not None:
                amt = float(inc.amount)
            elif r.total_disputed_amount is not None:
                amt = float(r.total_disputed_amount)
            else:
                amt = 0.0

            created_at = r.received_at if r.received_at else datetime.utcnow()

            c = models.Case(
                case_id=case_id,
                transaction_id=txn_id,
                amount=amt,
                payment_mode=r.mode_of_payment,
                payer_account_number=r.payer_account_number,
                payer_bank=r.payer_bank,
                mobile_number=r.payer_mobile_number,
                district=r.district,
                state=r.state,
                source_type=models.SourceType.DEMO,
                branch_id=None,
                status=models.UnifiedCaseStatus.NEW,
                created_at=created_at,
                acknowledgement_no=case_id,
            )
            db.add(c)
            created += 1

        db.commit()
        return {"created": created, "skipped": skipped, "total_reports": len(reports)}
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--branch-id", type=int, default=None)
    parser.add_argument("--no-enable-demo-access", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    res = seed(
        branch_id=args.branch_id,
        enable_demo_access=not args.no_enable_demo_access,
        limit=args.limit,
    )
    print(res)
