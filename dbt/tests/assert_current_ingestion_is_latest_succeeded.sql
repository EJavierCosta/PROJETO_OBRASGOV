with expected_current as (
    select
        ingestion_id,
        source_updated_at,
        ingested_at
    from {{ ref('stg_obrasgov_ingestion_run') }}
    where ingestion_status = 'succeeded'
    order by ingested_at desc, source_updated_at desc, ingestion_id desc
    limit 1
),

published_current as (
    select
        ingestion_id,
        source_updated_at,
        ingested_at
    from {{ ref('int_obrasgov_current_ingestion') }}
)

select
    coalesce(expected_current.ingestion_id, published_current.ingestion_id) as ingestion_id,
    expected_current.source_updated_at as expected_source_updated_at,
    published_current.source_updated_at as published_source_updated_at,
    expected_current.ingested_at as expected_ingested_at,
    published_current.ingested_at as published_ingested_at
from expected_current
full outer join published_current on true
where expected_current.ingestion_id is distinct from published_current.ingestion_id
   or expected_current.source_updated_at is distinct from published_current.source_updated_at
   or expected_current.ingested_at is distinct from published_current.ingested_at
