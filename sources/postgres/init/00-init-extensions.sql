-- ============================================================
-- FinFlow PostgreSQL — Initial Setup
-- Runs once on first container start
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for hashing (used in governance/masking)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Verify extensions
SELECT extname, extversion
FROM pg_extension
ORDER BY extname;
