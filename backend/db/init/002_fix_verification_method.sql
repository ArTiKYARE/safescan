-- Migration: Fix domains with NULL verification_method
-- Run this in PostgreSQL to fix existing records

-- Check affected domains
SELECT id, domain, verification_method
FROM domains
WHERE verification_method IS NULL;

-- Update NULL verification_method to 'api_token'
UPDATE domains
SET verification_method = 'api_token'
WHERE verification_method IS NULL;

-- Verify the fix
SELECT COUNT(*) as updated_count
FROM domains
WHERE verification_method = 'api_token';
