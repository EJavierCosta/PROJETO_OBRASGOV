with exploded_investments as (
    select
        project_snapshot_key,
        ingestion_id,
        project_id,
        investment_position,
        investment_payload
    from {{ ref('stg_obrasgov_project') }} as project
    cross join lateral jsonb_array_elements(project.planned_investments)
        with ordinality as investment_item(investment_payload, investment_position)
)

select
    md5(concat_ws('||', project_snapshot_key, investment_position::text)) as investment_item_key,
    project_snapshot_key,
    ingestion_id,
    project_id,
    investment_position::integer as investment_position,
    nullif(trim(investment_payload ->> 'desc_nome_fonte_recurso'), '')::text as funding_source_name,
    case
        when nullif(trim(investment_payload ->> 'vl_investimento_previsto'), '')
            ~ '^[+-]?[0-9]+([.][0-9]+)?$'
            then (investment_payload ->> 'vl_investimento_previsto')::numeric
    end as planned_investment_amount
from exploded_investments
