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

    union

    select 'vw_project_detail_current'::text, ingestion_id from {{ ref('vw_project_detail_current') }}
    union
    select 'vw_project_contract_current'::text, ingestion_id from {{ ref('vw_project_contract_current') }}
    union
    select 'vw_project_commitment_current'::text, ingestion_id from {{ ref('vw_project_commitment_current') }}
    union
    select 'vw_project_execution_current'::text, ingestion_id from {{ ref('vw_project_execution_current') }}
    union
    select 'vw_project_status_history_current'::text, ingestion_id from {{ ref('vw_project_status_history_current') }}
    union
    select 'vw_project_feasibility_study_current'::text, ingestion_id from {{ ref('vw_project_feasibility_study_current') }}
    union
    select 'vw_project_participant_current'::text, ingestion_id from {{ ref('vw_project_participant_current') }}
    union
    select 'vw_project_axis_type_current'::text, ingestion_id from {{ ref('vw_project_axis_type_current') }}
    union
    select 'vw_project_ppa_current'::text, ingestion_id from {{ ref('vw_project_ppa_current') }}
    union
    select 'vw_project_restriction_area_current'::text, ingestion_id from {{ ref('vw_project_restriction_area_current') }}
    union
    select 'vw_project_photo_indicator_current'::text, ingestion_id from {{ ref('vw_project_photo_indicator_current') }}
    union
    select 'vw_project_commitment_totals_current'::text, ingestion_id from {{ ref('vw_project_commitment_totals_current') }}
    union
    select 'vw_project_coverage_current'::text, ingestion_id from {{ ref('vw_project_coverage_current') }}
)

select
    observed_current.view_name,
    observed_current.ingestion_id
from observed_current
left join expected_current using (ingestion_id)
where expected_current.ingestion_id is null
