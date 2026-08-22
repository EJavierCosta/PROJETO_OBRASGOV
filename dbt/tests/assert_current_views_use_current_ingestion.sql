with expected_current as (
    select ingestion_id
    from {{ ref('int_obrasgov_current_ingestion') }}
),

observed_current as (
    select 'vw_market_overview_current'::text as view_name, ingestion_id
    from {{ ref('vw_market_overview_current') }}

    union

    select 'vw_project_investment_current'::text as view_name, ingestion_id
    from {{ ref('vw_project_investment_current') }}

    union

    select 'vw_project_location_current'::text as view_name, ingestion_id
    from {{ ref('vw_project_location_current') }}

    union

    select 'vw_snapshot_metadata_current'::text as view_name, ingestion_id
    from {{ ref('vw_snapshot_metadata_current') }}
)

select
    observed_current.view_name,
    observed_current.ingestion_id
from observed_current
left join expected_current using (ingestion_id)
where expected_current.ingestion_id is null
