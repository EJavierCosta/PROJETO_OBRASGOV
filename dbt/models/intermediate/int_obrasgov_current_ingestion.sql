with ranked_runs as (
    select
        ingestion_id,
        source_updated_at,
        ingested_at,
        row_number() over (
            order by ingested_at desc, source_updated_at desc, ingestion_id desc
        ) as current_rank
    from {{ ref('stg_obrasgov_ingestion_run') }}
    where ingestion_status = 'succeeded'
)

select
    ingestion_id,
    source_updated_at,
    ingested_at
from ranked_runs
where current_rank = 1
