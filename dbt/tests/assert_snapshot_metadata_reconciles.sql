with current_ingestion as (
    select ingestion_id
    from {{ ref('int_obrasgov_current_ingestion') }}
),

expected_metadata as (
    select
        current_ingestion.ingestion_id,
        count(project.project_snapshot_key)::bigint as project_count,
        (
            select count(*)::bigint
            from {{ ref('fct_planned_investment') }} as investment
            where investment.ingestion_id = current_ingestion.ingestion_id
        ) as planned_investment_count,
        (
            select count(*)::bigint
            from {{ ref('bridge_project_location') }} as bridge
            where bridge.ingestion_id = current_ingestion.ingestion_id
        ) as location_count,
        (
            select count(distinct location.ibge_code)::bigint
            from {{ ref('bridge_project_location') }} as bridge
            inner join {{ ref('dim_location') }} as location
                on bridge.location_key = location.location_key
            where bridge.ingestion_id = current_ingestion.ingestion_id
        ) as municipality_count
    from current_ingestion
    left join {{ ref('fct_project_snapshot') }} as project
        on current_ingestion.ingestion_id = project.ingestion_id
    group by current_ingestion.ingestion_id
)

select
    expected.ingestion_id,
    expected.project_count as expected_project_count,
    metadata.project_count as actual_project_count,
    expected.planned_investment_count as expected_planned_investment_count,
    metadata.planned_investment_count as actual_planned_investment_count,
    expected.location_count as expected_location_count,
    metadata.location_count as actual_location_count,
    expected.municipality_count as expected_municipality_count,
    metadata.municipality_count as actual_municipality_count
from expected_metadata as expected
left join {{ ref('vw_snapshot_metadata_current') }} as metadata
    on expected.ingestion_id = metadata.ingestion_id
where metadata.ingestion_id is null
   or expected.project_count is distinct from metadata.project_count
   or expected.planned_investment_count is distinct from metadata.planned_investment_count
   or expected.location_count is distinct from metadata.location_count
   or expected.municipality_count is distinct from metadata.municipality_count
