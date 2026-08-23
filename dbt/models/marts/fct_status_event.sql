select event.status_event_key::text, project.project_snapshot_key::text, event.ingestion_id::uuid, event.project_id::text, event.status_event_source_id::text,
    event.event_date::date, event.source_status::text, event.justification::text, event.treatment_indicator::text, event.treatment_phase::text,
    project.source_updated_at::timestamptz, project.ingested_at::timestamptz
from {{ ref('stg_obrasgov_status_history') }} as event inner join {{ ref('fct_project_snapshot') }} as project using (ingestion_id, project_id)
