select
    ingestion_id::uuid as ingestion_id,
    started_at::timestamp with time zone as started_at,
    finished_at::timestamp with time zone as ingested_at,
    status::text as ingestion_status,
    source_updated_at::timestamp with time zone as source_updated_at,
    base_url::text as source_base_url,
    query_scope::jsonb as query_scope,
    scope_hash::text as scope_hash,
    error_message::text as error_message
from {{ source('bronze', 'ingestion_run') }}
