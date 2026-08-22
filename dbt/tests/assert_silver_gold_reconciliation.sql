with silver_project_counts as (
    select
        ingestion_id,
        count(*)::bigint as project_count
    from {{ ref('stg_obrasgov_project') }}
    where project_id is not null
      and uf_principal = 'CE'
      and nature_intervention = 'Obra'
      and species_intervention = 'Construção'
    group by ingestion_id
),

gold_project_counts as (
    select
        ingestion_id,
        count(*)::bigint as project_count
    from {{ ref('fct_project_snapshot') }}
    group by ingestion_id
),

project_count_failures as (
    select
        coalesce(silver.ingestion_id, gold.ingestion_id) as ingestion_id,
        silver.project_count as silver_value,
        gold.project_count as gold_value
    from silver_project_counts as silver
    full outer join gold_project_counts as gold using (ingestion_id)
    where coalesce(silver.project_count, 0) <> coalesce(gold.project_count, 0)
),

silver_investment_amounts as (
    select
        project.ingestion_id,
        coalesce(sum(investment.planned_investment_amount), 0::numeric) as planned_investment_amount
    from {{ ref('stg_obrasgov_project') }} as project
    left join {{ ref('int_obrasgov_project_investment') }} as investment
        on project.project_snapshot_key = investment.project_snapshot_key
    where project.project_id is not null
      and project.uf_principal = 'CE'
      and project.nature_intervention = 'Obra'
      and project.species_intervention = 'Construção'
    group by project.ingestion_id
),

gold_investment_amounts as (
    select
        ingestion_id,
        coalesce(sum(planned_investment_amount), 0::numeric) as planned_investment_amount
    from {{ ref('fct_planned_investment') }}
    group by ingestion_id
),

investment_amount_failures as (
    select
        coalesce(silver.ingestion_id, gold.ingestion_id) as ingestion_id,
        silver.planned_investment_amount as silver_value,
        gold.planned_investment_amount as gold_value
    from silver_investment_amounts as silver
    full outer join gold_investment_amounts as gold using (ingestion_id)
    where coalesce(silver.planned_investment_amount, 0::numeric)
        is distinct from coalesce(gold.planned_investment_amount, 0::numeric)
)

select
    'project_count'::text as reconciliation_name,
    ingestion_id,
    silver_value::numeric as silver_value,
    gold_value::numeric as gold_value
from project_count_failures

union all

select
    'planned_investment_amount'::text as reconciliation_name,
    ingestion_id,
    silver_value::numeric as silver_value,
    gold_value::numeric as gold_value
from investment_amount_failures
