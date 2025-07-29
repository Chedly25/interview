-- Initialize PostgreSQL database for production
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create automotive_assistant database if it doesn't exist
-- (This file runs automatically in docker-entrypoint-initdb.d)