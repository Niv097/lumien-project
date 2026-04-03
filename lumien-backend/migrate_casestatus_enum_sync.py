"""One-time migration: sync Postgres enum used by complaints.status with Python CaseStatus.

This fixes errors like:
  invalid input value for enum casestatus: "UNDER_REVIEW"

It is safe/idempotent: it only adds missing enum labels.

Note: PostgreSQL doesn't support removing enum values easily, so this script only adds.
"""

import psycopg2
from app.core.config import settings
from app.models.models import CaseStatus


def _to_psycopg_url(sqlalchemy_url: str) -> str:
    return (
        sqlalchemy_url.replace("postgresql+psycopg://", "postgresql://")
        .replace("postgresql+psycopg2://", "postgresql://")
        .replace("postgresql+asyncpg://", "postgresql://")
    )


def _get_status_enum_type(cur) -> str:
    cur.execute(
        """
        SELECT t.typname
        FROM pg_attribute a
        JOIN pg_class c ON a.attrelid = c.oid
        JOIN pg_type t ON a.atttypid = t.oid
        WHERE c.relname = 'complaints'
          AND a.attname = 'status'
          AND a.attnum > 0
          AND NOT a.attisdropped
        """
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError("Could not find complaints.status column type")
    return row[0]


def _get_existing_labels(cur, enum_type: str) -> set[str]:
    cur.execute(
        """
        SELECT e.enumlabel
        FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = %s
        """,
        (enum_type,),
    )
    return {r[0] for r in cur.fetchall()}


def migrate():
    db_url = _to_psycopg_url(settings.DATABASE_URL)
    conn = psycopg2.connect(db_url)
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            enum_type = _get_status_enum_type(cur)
            existing = _get_existing_labels(cur, enum_type)

            desired = [s.value for s in CaseStatus]
            missing = [v for v in desired if v not in existing]

            if not missing:
                print(f"OK: enum '{enum_type}' already contains all CaseStatus labels.")
                return

            print(f"Enum type: {enum_type}")
            print("Missing labels:")
            for v in missing:
                print(f"  - {v}")

            for v in missing:
                # Postgres < 12 doesn't support IF NOT EXISTS, so we pre-check above.
                cur.execute(f"ALTER TYPE {enum_type} ADD VALUE '{v}'")

            print("Done.")

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
