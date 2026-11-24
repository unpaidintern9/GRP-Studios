-- Planned studio-only metadata schema. Not applied by this commit.
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS workspaces (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workspace_members (
  workspace_id TEXT NOT NULL REFERENCES workspaces(id), subject TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('owner','producer','reviewer')),
  PRIMARY KEY(workspace_id, subject)
);
CREATE TABLE IF NOT EXISTS assets (
  workspace_id TEXT NOT NULL REFERENCES workspaces(id), id TEXT NOT NULL,
  object_key TEXT NOT NULL UNIQUE, sha256 TEXT NOT NULL CHECK(length(sha256)=64),
  media_type TEXT NOT NULL, approval_state TEXT NOT NULL CHECK(approval_state IN ('pending','approved','rejected')),
  created_at TEXT NOT NULL, PRIMARY KEY(workspace_id,id)
);
CREATE TABLE IF NOT EXISTS render_jobs (
  workspace_id TEXT NOT NULL REFERENCES workspaces(id), id TEXT NOT NULL,
  requested_by TEXT NOT NULL, template_id TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('queued','running','cancelling','cancelled','succeeded','failed')),
  idempotency_key TEXT NOT NULL, created_at TEXT NOT NULL, finished_at TEXT,
  artifact_asset_id TEXT,
  PRIMARY KEY(workspace_id,id), UNIQUE(workspace_id,idempotency_key),
  FOREIGN KEY(workspace_id,requested_by) REFERENCES workspace_members(workspace_id,subject),
  FOREIGN KEY(workspace_id,artifact_asset_id) REFERENCES assets(workspace_id,id)
);
CREATE INDEX IF NOT EXISTS render_jobs_state ON render_jobs(workspace_id,state,created_at);
