-- ─────────────────────────────────────────────────────────────────────────────
-- PRISM — PostgreSQL bootstrap (runs once on a fresh data volume)
--
-- IMPORTANT: All application tables (leads, campaigns, email_logs, replies,
-- clusters, users, ...) are created automatically by SQLAlchemy
-- (`Base.metadata.create_all`) when the backend starts. Do NOT create them
-- here — a stale DDL would conflict with the ORM schema.
--
-- This file only creates database extensions and tables that have NO ORM
-- model but are used through raw SQL.
-- ─────────────────────────────────────────────────────────────────────────────

-- Enable pgvector extension (used by vector similarity queries, if enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation helpers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Companies (used by the Cikarang scraper via raw SQL; no ORM model) ─────
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(255),
    location VARCHAR(255),
    estate VARCHAR(100),  -- MM2100, EJIP, KIIC, etc.
    website VARCHAR(512),
    employee_count_range VARCHAR(50),
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
