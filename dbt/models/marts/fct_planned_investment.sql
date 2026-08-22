with scoped_investments as (
    select
        investment.project_snapshot_key,
        project.ingestion_id,
        project.project_id,
        investment.funding_source_name,
        investment.planned_investment_amount,
        project.source_updated_at,
        project.ingested_at
    from {{ ref('int_obrasgov_project_investment') }} as investment
    inner join {{ ref('fct_project_snapshot') }} as project
        on investment.project_snapshot_key = project.project_snapshot_key
)

select
    md5(
        concat_ws(
            '||',
            project_snapshot_key,
            coalesce(funding_source_name, '∅')
        )
    )::text as project_funding_source_key,
    project_snapshot_key::text as project_snapshot_key,
    ingestion_id::uuid as ingestion_id,
    project_id::text as project_id,
    md5(coalesce(funding_source_name, '∅'))::text as funding_source_key,
    funding_source_name::text as funding_source_name,
    sum(planned_investment_amount)::numeric as planned_investment_amount,
    count(*)::bigint as source_investment_record_count,
    source_updated_at::timestamp with time zone as source_updated_at,
    ingested_at::timestamp with time zone as ingested_at
from scoped_investments
group by
    project_snapshot_key,
    ingestion_id,
    project_id,
    funding_source_name,
    source_updated_at,
    ingested_at
