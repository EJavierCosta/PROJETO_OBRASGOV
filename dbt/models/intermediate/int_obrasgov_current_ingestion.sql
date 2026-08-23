with expected_resources as (
    select unnest(array[
        'data-atualizacao', 'projeto-investimento', 'geometria', 'contrato', 'empenho',
        'execucao-fisica', 'historico-situacao-cancelada-paralisada', 'estudo-viabilidade'
    ])::text as resource_name
),

complete_runs as (
    select run.ingestion_id, run.source_updated_at, run.ingested_at
    from {{ ref('stg_obrasgov_ingestion_run') }} as run
    where run.ingestion_status = 'succeeded'
      and not exists (
          select 1
          from expected_resources
          left join {{ source('bronze', 'ingestion_resource') }} as resource
            on resource.ingestion_id = run.ingestion_id
           and resource.resource_name = expected_resources.resource_name
           and resource.status = 'succeeded'
          where resource.resource_name is null
      )
),

ranked_runs as (
    select
        ingestion_id,
        source_updated_at,
        ingested_at,
        row_number() over (
            order by ingested_at desc, source_updated_at desc, ingestion_id desc
        ) as current_rank
    from complete_runs
)

select
    ingestion_id,
    source_updated_at,
    ingested_at
from ranked_runs
where current_rank = 1
