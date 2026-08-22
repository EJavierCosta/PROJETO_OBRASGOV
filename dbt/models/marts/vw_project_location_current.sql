{{ config(materialized='view', grants={'select': ['obrasgov_frontend']}) }}

with current_ingestion as (
    select ingestion_id
    from {{ ref('int_obrasgov_current_ingestion') }}
),

locations_by_municipality as (
    select
        bridge.project_snapshot_key,
        location.municipality_name,
        location.ibge_code,
        location.uf
    from {{ ref('bridge_project_location') }} as bridge
    inner join current_ingestion
        on bridge.ingestion_id = current_ingestion.ingestion_id
    inner join {{ ref('dim_location') }} as location
        on bridge.location_key = location.location_key
    group by
        bridge.project_snapshot_key,
        location.municipality_name,
        location.ibge_code,
        location.uf
),

coordinates_by_project as (
    select
        bridge.project_snapshot_key,
        case
            when count(distinct concat_ws('|', pin.latitude::text, pin.longitude::text))
                filter (where pin.latitude is not null and pin.longitude is not null) = 1
                then max(pin.latitude) filter (where pin.latitude is not null and pin.longitude is not null)
        end::numeric as latitude,
        case
            when count(distinct concat_ws('|', pin.latitude::text, pin.longitude::text))
                filter (where pin.latitude is not null and pin.longitude is not null) = 1
                then max(pin.longitude) filter (where pin.latitude is not null and pin.longitude is not null)
        end::numeric as longitude
    from {{ ref('bridge_project_pin') }} as bridge
    inner join current_ingestion
        on bridge.ingestion_id = current_ingestion.ingestion_id
    inner join {{ ref('dim_pin') }} as pin
        on bridge.pin_key = pin.pin_key
    group by bridge.project_snapshot_key
),

investments_by_project as (
    select
        project_snapshot_key,
        sum(planned_investment_amount) as planned_investment_amount
    from {{ ref('fct_planned_investment') }}
    inner join current_ingestion using (ingestion_id)
    group by project_snapshot_key
),

current_projects as (
    select project.*
    from {{ ref('fct_project_snapshot') }} as project
    inner join current_ingestion using (ingestion_id)
)

select
    project.project_id::text as project_id,
    location.municipality_name::text as municipality_name,
    location.ibge_code::bigint as ibge_code,
    location.uf::text as uf,
    coordinates.latitude::numeric as latitude,
    coordinates.longitude::numeric as longitude,
    investment.planned_investment_amount::numeric as planned_investment_amount,
    project.source_updated_at::timestamp with time zone as source_updated_at,
    project.ingested_at::timestamp with time zone as ingested_at,
    project.ingestion_id::uuid as ingestion_id
from locations_by_municipality as location
inner join current_projects as project
    on location.project_snapshot_key = project.project_snapshot_key
left join coordinates_by_project as coordinates
    on project.project_snapshot_key = coordinates.project_snapshot_key
left join investments_by_project as investment
    on project.project_snapshot_key = investment.project_snapshot_key
