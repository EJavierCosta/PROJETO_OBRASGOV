with raw_projects as (
    select distinct
        ingestion_id,
        nullif(trim(payload ->> 'id_projeto_investimento'), '') as project_id
    from {{ source('bronze', 'obrasgov_project_raw') }}
    where nullif(trim(payload ->> 'id_projeto_investimento'), '') is not null
)

select
    raw_projects.ingestion_id,
    raw_projects.project_id
from raw_projects
left join {{ ref('stg_obrasgov_project') }} as staged
    on raw_projects.ingestion_id = staged.ingestion_id
   and raw_projects.project_id = staged.project_id
where staged.project_snapshot_key is null
