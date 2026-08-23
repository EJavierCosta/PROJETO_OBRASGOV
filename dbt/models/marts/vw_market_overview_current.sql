{{ config(materialized='view', grants={'select': ['obrasgov_frontend', 'obrasgov_chat']}) }}

with current_ingestion as (
    select ingestion_id
    from {{ ref('int_obrasgov_current_ingestion') }}
),

current_projects as (
    select project.*
    from {{ ref('fct_project_snapshot') }} as project
    inner join current_ingestion using (ingestion_id)
),

investments_by_project as (
    select
        investment.project_snapshot_key,
        sum(investment.planned_investment_amount) as planned_investment_amount
    from {{ ref('fct_planned_investment') }} as investment
    inner join current_ingestion using (ingestion_id)
    group by investment.project_snapshot_key
),

axis_types_by_project as (
    select
        bridge.project_snapshot_key,
        string_agg(distinct axis_type.axis_name, ' | ' order by axis_type.axis_name)::text as axis_name,
        string_agg(distinct axis_type.type_name, ' | ' order by axis_type.type_name)::text as type_name,
        string_agg(distinct axis_type.subtype_name, ' | ' order by axis_type.subtype_name)::text as subtype_name
    from {{ ref('bridge_project_axis_type') }} as bridge
    inner join current_ingestion
        on bridge.ingestion_id = current_ingestion.ingestion_id
    inner join {{ ref('dim_axis_type') }} as axis_type
        on bridge.axis_type_key = axis_type.axis_type_key
    group by bridge.project_snapshot_key
),

locations_by_project as (
    select
        bridge.project_snapshot_key,
        string_agg(
            distinct location.municipality_name,
            ' | '
            order by location.municipality_name
        )::text as municipality_names,
        string_agg(
            distinct location.ibge_code::text,
            ' | '
            order by location.ibge_code::text
        )::text as ibge_codes
    from {{ ref('bridge_project_location') }} as bridge
    inner join current_ingestion
        on bridge.ingestion_id = current_ingestion.ingestion_id
    inner join {{ ref('dim_location') }} as location
        on bridge.location_key = location.location_key
    group by bridge.project_snapshot_key
)

select
    project.project_id::text as project_id,
    project.project_name::text as project_name,
    project.project_description::text as description,
    project.organization_name::text as organization_name,
    project.organization_cnpj::text as organization_cnpj,
    project.source_status::text as source_status,
    project.uf_principal::text as uf_principal,
    project.nature_intervention::text as nature_intervention,
    project.species_intervention::text as species_intervention,
    axis_types.axis_name::text as axis_name,
    axis_types.type_name::text as type_name,
    axis_types.subtype_name::text as subtype_name,
    project.registration_date::date as registration_date,
    project.registration_year::integer as registration_year,
    project.expected_start_date::date as expected_start_date,
    project.expected_end_date::date as expected_end_date,
    investments.planned_investment_amount::numeric as planned_investment_amount,
    locations.municipality_names::text as municipality_names,
    locations.ibge_codes::text as ibge_codes,
    project.source_updated_at::timestamp with time zone as source_updated_at,
    project.ingested_at::timestamp with time zone as ingested_at,
    project.ingestion_id::uuid as ingestion_id
from current_projects as project
left join investments_by_project as investments
    on project.project_snapshot_key = investments.project_snapshot_key
left join axis_types_by_project as axis_types
    on project.project_snapshot_key = axis_types.project_snapshot_key
left join locations_by_project as locations
    on project.project_snapshot_key = locations.project_snapshot_key
