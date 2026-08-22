{{ config(materialized='view', grants={'select': ['obrasgov_frontend']}) }}

with current_ingestion as (
    select
        ingestion_id,
        source_updated_at,
        ingested_at
    from {{ ref('int_obrasgov_current_ingestion') }}
),

project_counts as (
    select
        project.ingestion_id,
        count(*)::bigint as project_count
    from {{ ref('fct_project_snapshot') }} as project
    inner join current_ingestion using (ingestion_id)
    group by project.ingestion_id
),

investment_counts as (
    select
        investment.ingestion_id,
        count(*)::bigint as planned_investment_count
    from {{ ref('fct_planned_investment') }} as investment
    inner join current_ingestion using (ingestion_id)
    group by investment.ingestion_id
),

investment_totals as (
    select
        investment.ingestion_id,
        sum(investment.planned_investment_amount)::numeric as planned_investment_amount
    from {{ ref('fct_planned_investment') }} as investment
    inner join current_ingestion using (ingestion_id)
    group by investment.ingestion_id
),

execution_counts as (
    select
        project.ingestion_id,
        count(*) filter (where project.source_status = 'Em execução')::bigint
            as execution_project_count
    from {{ ref('fct_project_snapshot') }} as project
    inner join current_ingestion using (ingestion_id)
    group by project.ingestion_id
),

location_counts as (
    select
        bridge.ingestion_id,
        count(*)::bigint as location_count,
        count(distinct location.ibge_code)::bigint as municipality_count
    from {{ ref('bridge_project_location') }} as bridge
    inner join current_ingestion
        on bridge.ingestion_id = current_ingestion.ingestion_id
    inner join {{ ref('dim_location') }} as location
        on bridge.location_key = location.location_key
    group by bridge.ingestion_id
)

select
    current_ingestion.ingestion_id::uuid as ingestion_id,
    current_ingestion.source_updated_at::timestamp with time zone as source_updated_at,
    current_ingestion.ingested_at::timestamp with time zone as ingested_at,
    coalesce(project_counts.project_count, 0)::bigint as project_count,
    coalesce(investment_counts.planned_investment_count, 0)::bigint as planned_investment_count,
    investment_totals.planned_investment_amount::numeric as planned_investment_amount,
    coalesce(location_counts.location_count, 0)::bigint as location_count,
    coalesce(location_counts.municipality_count, 0)::bigint as municipality_count,
    coalesce(execution_counts.execution_project_count, 0)::bigint as execution_project_count
from current_ingestion
left join project_counts using (ingestion_id)
left join investment_counts using (ingestion_id)
left join investment_totals using (ingestion_id)
left join execution_counts using (ingestion_id)
left join location_counts using (ingestion_id)
