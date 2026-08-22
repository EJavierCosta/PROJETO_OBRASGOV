select *
from {{ source('bronze', 'ingestion_run') }}
where status in ('succeeded', 'skipped')
  and source_updated_at is null
