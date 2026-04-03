"""One-time migration: sync Postgres case_status enum with Python CaseStatus.

Fixes errors like:
  invalid input value for enum case_status: "NEW"

This script is idempotent: it checks if the enum value exists before adding.
"""

import psycopg2
from app.core.config import settings


def _to_psycopg_url(sqlalchemy_url: str) -> str:
    return (
        sqlalchemy_url.replace("postgresql+psycopg://", "postgresql://")
        .replace("postgresql+psycopg2://", "postgresql://")
        .replace("postgresql+asyncpg://", "postgresql://")
    )


def migrate():
    db_url = _to_psycopg_url(settings.DATABASE_URL)
    conn = psycopg2.connect(db_url)
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            # Detect the enum type used by complaints.status
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

            enum_type = row[0]

            # Check if NEW exists
            cur.execute(
                """
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = %s
                  AND e.enumlabel = 'NEW'
                """,
                (enum_type,),
            )
            exists = cur.fetchone() is not None
            if exists:
                print(f"OK: enum '{enum_type}' already contains value 'NEW'.")
                return

            # Add enum value.
            # Note: Postgres < 12 doesn't support IF NOT EXISTS for ADD VALUE.
            print(f"Adding 'NEW' to enum type '{enum_type}'...")
            cur.execute(f"ALTER TYPE {enum_type} ADD VALUE 'NEW'")
            print("Done.")

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
