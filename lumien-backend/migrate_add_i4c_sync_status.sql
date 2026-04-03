-- Migration: Add i4c_sync_status column to cases table
-- This column tracks I4C sync status (PENDING, SYNCED, FAILED)

ALTER TABLE cases ADD COLUMN i4c_sync_status VARCHAR(20) DEFAULT 'PENDING';

-- Update existing cases to have default value
UPDATE cases SET i4c_sync_status = 'PENDING' WHERE i4c_sync_status IS NULL;
