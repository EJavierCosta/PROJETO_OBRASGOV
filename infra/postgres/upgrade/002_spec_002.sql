CREATE TABLE IF NOT EXISTS bronze.obrasgov_contract_raw (
    ingestion_id uuid NOT NULL REFERENCES bronze.ingestion_run (ingestion_id),
    page_number integer NOT NULL,
    page_size integer NOT NULL,
    record_index integer NOT NULL,
    payload jsonb NOT NULL,
    record_hash text NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (ingestion_id, page_number, record_index)
);

CREATE TABLE IF NOT EXISTS bronze.obrasgov_commitment_raw (
    ingestion_id uuid NOT NULL REFERENCES bronze.ingestion_run (ingestion_id),
    page_number integer NOT NULL,
    page_size integer NOT NULL,
    record_index integer NOT NULL,
    payload jsonb NOT NULL,
    record_hash text NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (ingestion_id, page_number, record_index)
);

CREATE TABLE IF NOT EXISTS bronze.obrasgov_physical_execution_raw (
    ingestion_id uuid NOT NULL REFERENCES bronze.ingestion_run (ingestion_id),
    page_number integer NOT NULL,
    page_size integer NOT NULL,
    record_index integer NOT NULL,
    payload jsonb NOT NULL,
    record_hash text NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (ingestion_id, page_number, record_index)
);

CREATE TABLE IF NOT EXISTS bronze.obrasgov_status_history_raw (
    ingestion_id uuid NOT NULL REFERENCES bronze.ingestion_run (ingestion_id),
    page_number integer NOT NULL,
    page_size integer NOT NULL,
    record_index integer NOT NULL,
    payload jsonb NOT NULL,
    record_hash text NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (ingestion_id, page_number, record_index)
);

CREATE TABLE IF NOT EXISTS bronze.obrasgov_feasibility_study_raw (
    ingestion_id uuid NOT NULL REFERENCES bronze.ingestion_run (ingestion_id),
    page_number integer NOT NULL,
    page_size integer NOT NULL,
    record_index integer NOT NULL,
    payload jsonb NOT NULL,
    record_hash text NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (ingestion_id, page_number, record_index)
);

GRANT SELECT, INSERT ON bronze.obrasgov_contract_raw TO obrasgov_ingestion;
GRANT SELECT, INSERT ON bronze.obrasgov_commitment_raw TO obrasgov_ingestion;
GRANT SELECT, INSERT ON bronze.obrasgov_physical_execution_raw TO obrasgov_ingestion;
GRANT SELECT, INSERT ON bronze.obrasgov_status_history_raw TO obrasgov_ingestion;
GRANT SELECT, INSERT ON bronze.obrasgov_feasibility_study_raw TO obrasgov_ingestion;
GRANT SELECT ON bronze.obrasgov_contract_raw TO obrasgov_dbt;
GRANT SELECT ON bronze.obrasgov_commitment_raw TO obrasgov_dbt;
GRANT SELECT ON bronze.obrasgov_physical_execution_raw TO obrasgov_dbt;
GRANT SELECT ON bronze.obrasgov_status_history_raw TO obrasgov_dbt;
GRANT SELECT ON bronze.obrasgov_feasibility_study_raw TO obrasgov_dbt;
REVOKE ALL ON SCHEMA bronze, silver FROM obrasgov_frontend;
GRANT USAGE ON SCHEMA gold TO obrasgov_frontend;
