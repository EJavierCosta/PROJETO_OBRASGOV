{{ config(materialized='view', grants={'select': ['obrasgov_frontend', 'obrasgov_chat']}) }}

with current as (select ingestion_id from {{ ref('int_obrasgov_current_ingestion') }}),
investments as (
    select project_snapshot_key, sum(planned_investment_amount)::numeric as planned_investment_amount
    from {{ ref('fct_planned_investment') }} inner join current using (ingestion_id)
    group by 1
),
locations as (
    select project.project_id, location.geometry_id, location.municipality_name, location.ibge_code, location.uf,
        location.geometry_origin,
        investments.planned_investment_amount, project.source_updated_at, project.ingested_at, project.ingestion_id
    from {{ ref('bridge_project_location') }} bridge
    inner join {{ ref('dim_location') }} location using (location_key)
    inner join {{ ref('fct_project_snapshot') }} project using (project_snapshot_key)
    inner join current on project.ingestion_id = current.ingestion_id
    left join investments using (project_snapshot_key)
), pins as (
    select project.project_id, pin.pin_name, pin.latitude, pin.longitude, investments.planned_investment_amount, project.source_updated_at, project.ingested_at, project.ingestion_id
    from {{ ref('bridge_project_pin') }} bridge inner join {{ ref('dim_pin') }} pin using (pin_key)
    inner join {{ ref('fct_project_snapshot') }} project using (project_snapshot_key) inner join current on project.ingestion_id = current.ingestion_id left join investments using (project_snapshot_key)
)
select project_id::text, geometry_id::integer, municipality_name::text, ibge_code::bigint, uf::text,
    geometry_origin::text, null::numeric as latitude, null::numeric as longitude, null::text as pin_name, planned_investment_amount::numeric, source_updated_at::timestamptz, ingested_at::timestamptz, ingestion_id::uuid
from locations
union all
select project_id::text, null::integer, null::text, null::bigint, null::text, null::text, latitude::numeric, longitude::numeric, pin_name::text, planned_investment_amount::numeric, source_updated_at::timestamptz, ingested_at::timestamptz, ingestion_id::uuid
from pins
