CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE bronze.ingestion_run (
    ingestion_id uuid PRIMARY KEY,
    started_at timestamptz NOT NULL,
    finished_at timestamptz,
    status text NOT NULL CHECK (status IN ('running', 'succeeded', 'failed', 'skipped')),
    source_updated_at timestamptz,
    base_url text NOT NULL,
    query_scope jsonb NOT NULL,
    scope_hash text NOT NULL,
    force_requested boolean NOT NULL DEFAULT false,
    error_message text,
    CONSTRAINT ingestion_run_finished_status_ck CHECK (
        (status = 'running' AND finished_at IS NULL)
        OR (status IN ('succeeded', 'failed', 'skipped') AND finished_at IS NOT NULL)
    )
);

CREATE INDEX ingestion_run_current_idx
    ON bronze.ingestion_run (status, source_updated_at DESC, finished_at DESC);

CREATE UNIQUE INDEX ingestion_run_running_snapshot_uidx
    ON bronze.ingestion_run (source_updated_at, scope_hash)
    WHERE status = 'running' AND source_updated_at IS NOT NULL;

CREATE TABLE bronze.ingestion_resource (
    ingestion_id uuid NOT NULL REFERENCES bronze.ingestion_run (ingestion_id),
    resource_name text NOT NULL,
    endpoint text NOT NULL,
    total_pages integer NOT NULL,
    total_items integer NOT NULL,
    pages_received integer NOT NULL DEFAULT 0,
    items_received integer NOT NULL DEFAULT 0,
    status text NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'succeeded', 'failed')),
    PRIMARY KEY (ingestion_id, resource_name)
);

CREATE TABLE bronze.ingestion_page (
    ingestion_id uuid NOT NULL REFERENCES bronze.ingestion_run (ingestion_id),
    resource_name text NOT NULL,
    page_number integer NOT NULL,
    requested_page_size integer NOT NULL,
    returned_page_size integer NOT NULL,
    returned_item_count integer NOT NULL,
    total_pages integer NOT NULL,
    total_items integer NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (ingestion_id, resource_name, page_number),
    FOREIGN KEY (ingestion_id, resource_name)
        REFERENCES bronze.ingestion_resource (ingestion_id, resource_name)
);

CREATE TABLE bronze.obrasgov_project_raw (
    ingestion_id uuid NOT NULL REFERENCES bronze.ingestion_run (ingestion_id),
    page_number integer NOT NULL,
    page_size integer NOT NULL,
    record_index integer NOT NULL,
    payload jsonb NOT NULL,
    record_hash text NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (ingestion_id, page_number, record_index)
);

CREATE TABLE bronze.obrasgov_geometry_raw (
    ingestion_id uuid NOT NULL REFERENCES bronze.ingestion_run (ingestion_id),
    page_number integer NOT NULL,
    page_size integer NOT NULL,
    record_index integer NOT NULL,
    payload jsonb NOT NULL,
    record_hash text NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (ingestion_id, page_number, record_index)
);

CREATE TABLE bronze.obrasgov_contract_raw (
    ingestion_id uuid NOT NULL REFERENCES bronze.ingestion_run (ingestion_id),
    page_number integer NOT NULL,
    page_size integer NOT NULL,
    record_index integer NOT NULL,
    payload jsonb NOT NULL,
    record_hash text NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (ingestion_id, page_number, record_index)
);

CREATE TABLE bronze.obrasgov_commitment_raw (
    ingestion_id uuid NOT NULL REFERENCES bronze.ingestion_run (ingestion_id),
    page_number integer NOT NULL,
    page_size integer NOT NULL,
    record_index integer NOT NULL,
    payload jsonb NOT NULL,
    record_hash text NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (ingestion_id, page_number, record_index)
);

CREATE TABLE bronze.obrasgov_physical_execution_raw (
    ingestion_id uuid NOT NULL REFERENCES bronze.ingestion_run (ingestion_id),
    page_number integer NOT NULL,
    page_size integer NOT NULL,
    record_index integer NOT NULL,
    payload jsonb NOT NULL,
    record_hash text NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (ingestion_id, page_number, record_index)
);

CREATE TABLE bronze.obrasgov_status_history_raw (
    ingestion_id uuid NOT NULL REFERENCES bronze.ingestion_run (ingestion_id),
    page_number integer NOT NULL,
    page_size integer NOT NULL,
    record_index integer NOT NULL,
    payload jsonb NOT NULL,
    record_hash text NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (ingestion_id, page_number, record_index)
);

CREATE TABLE bronze.obrasgov_feasibility_study_raw (
    ingestion_id uuid NOT NULL REFERENCES bronze.ingestion_run (ingestion_id),
    page_number integer NOT NULL,
    page_size integer NOT NULL,
    record_index integer NOT NULL,
    payload jsonb NOT NULL,
    record_hash text NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (ingestion_id, page_number, record_index)
);

CREATE TABLE bronze.obrasgov_source_update_raw (
    ingestion_id uuid NOT NULL REFERENCES bronze.ingestion_run (ingestion_id),
    page_number integer NOT NULL,
    page_size integer NOT NULL,
    record_index integer NOT NULL,
    payload jsonb NOT NULL,
    record_hash text NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (ingestion_id, page_number, record_index)
);
