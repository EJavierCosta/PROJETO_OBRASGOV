{{ config(materialized='view', grants={'select': ['obrasgov_frontend', 'obrasgov_chat']}) }}

with current_ingestion as (
    select ingestion_id
    from {{ ref('int_obrasgov_current_ingestion') }}
)

select
    project.source_status::text as source_status,
    count(*)::bigint as project_count
from {{ ref('fct_project_snapshot') }} as project
inner join current_ingestion using (ingestion_id)
group by project.source_status
