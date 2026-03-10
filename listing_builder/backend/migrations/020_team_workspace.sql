-- Migration 009: Team workspace tables
-- Purpose: Teams, members, invitations for collaborative workspace
-- Run via: Supabase Management API or psql

-- Teams
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    owner_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_teams_owner_id ON teams(owner_id);

-- Team members
CREATE TABLE IF NOT EXISTS team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'editor',
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_team_user UNIQUE (team_id, user_id)
);
CREATE INDEX IF NOT EXISTS ix_team_members_team_id ON team_members(team_id);
CREATE INDEX IF NOT EXISTS ix_team_members_user_id ON team_members(user_id);

-- Team invitations
CREATE TABLE IF NOT EXISTS team_invitations (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'editor',
    token VARCHAR(64) NOT NULL UNIQUE,
    invited_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_team_invite_email UNIQUE (team_id, email)
);
CREATE INDEX IF NOT EXISTS ix_team_invitations_team_id ON team_invitations(team_id);
CREATE INDEX IF NOT EXISTS ix_team_invitations_email ON team_invitations(email);
CREATE INDEX IF NOT EXISTS ix_team_invitations_token ON team_invitations(token);

-- RLS policies (Supabase requirement — all 58 tables have RLS enabled)
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_invitations ENABLE ROW LEVEL SECURITY;

-- WHY: Service role bypasses RLS — our backend uses service key
-- No per-user policies needed since backend enforces access control
