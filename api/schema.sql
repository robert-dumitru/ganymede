CREATE SCHEMA ganymede;
CREATE TABLE ganymede.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    input_file_id TEXT NOT NULL,
    output_file_id TEXT,
    error TEXT,
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running'
);
