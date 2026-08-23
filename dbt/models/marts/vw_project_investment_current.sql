{{ config(materialized='view', grants={'select': ['obrasgov_frontend', 'obrasgov_chat']}) }}

with current_ingestion as (
    select ingestion_id
    from {{ ref('int_obrasgov_current_ingestion') }}
)

select
    investment.project_id::text as project_id,
    investment.funding_source_name::text as funding_source_name,
    investment.planned_investment_amount::numeric as planned_investment_amount,
    investment.source_updated_at::timestamp with time zone as source_updated_at,
    investment.ingested_at::timestamp with time zone as ingested_at,
    investment.ingestion_id::uuid as ingestion_id
from {{ ref('fct_planned_investment') }} as investment
inner join current_ingestion using (ingestion_id)
