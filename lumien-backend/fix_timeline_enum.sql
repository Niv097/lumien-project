-- Fix PostgreSQL enum for timeline.event_type
-- Run this in your PostgreSQL database

-- Check current enum values
SELECT t.typname, e.enumlabel 
FROM pg_type t 
JOIN pg_enum e ON t.oid = e.enumtypid 
WHERE t.typname = 'timelineeventtype';

-- Add missing enum values
ALTER TYPE timelineeventtype ADD VALUE IF NOT EXISTS 'CASE_STATUS_UPDATED';
ALTER TYPE timelineeventtype ADD VALUE IF NOT EXISTS 'EVIDENCE_UPLOADED';

-- Verify all values are present
SELECT t.typname, e.enumlabel 
FROM pg_type t 
JOIN pg_enum e ON t.oid = e.enumtypid 
WHERE t.typname = 'timelineeventtype';
