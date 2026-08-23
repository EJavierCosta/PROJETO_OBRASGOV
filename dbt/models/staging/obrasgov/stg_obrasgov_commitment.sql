with typed as (
    select ingestion_id, payload, record_hash, fetched_at,
        nullif(trim(payload ->> 'id_projeto_investimento'), '') as project_id,
        nullif(trim(payload ->> 'sistema_origem_empenho'), '') as source_system,
        nullif(trim(payload ->> 'bd_origem_empenho'), '') as source_base,
        nullif(trim(payload ->> 'ug_emitente'), '') as issuing_ug,
        nullif(trim(payload ->> 'nr_empenho'), '') as commitment_number,
        nullif(trim(payload ->> 'id_minuta'), '') as minuta,
        nullif(trim(payload ->> 'data_emissao'), '') as emission_value
    from {{ source('bronze', 'obrasgov_commitment_raw') }}
), ranked as (
    select *, row_number() over (partition by ingestion_id, project_id, source_system, source_base, issuing_ug, commitment_number, minuta, emission_value order by fetched_at desc, record_hash desc) as dedupe_rank
    from typed
)
select
    md5(concat_ws('||', ingestion_id::text, project_id, source_system, source_base, issuing_ug, commitment_number, minuta, emission_value))::text as commitment_key,
    ingestion_id::uuid, project_id::text, commitment_number::text, source_system::text, source_base::text, issuing_ug::text,
    case when emission_value ~ '^\d{4}-\d{2}-\d{2}$' then emission_value::date end as emission_date,
    nullif(trim(payload ->> 'natureza_despesa'), '')::text as expense_nature, nullif(trim(payload ->> 'credor'), '')::text as creditor_name,
    nullif(trim(payload ->> 'descricao_empenho'), '')::text as commitment_description,
    case when payload ->> 'valor_empenho' ~ '^[+-]?\d+(\.\d+)?$' then (payload ->> 'valor_empenho')::numeric end as valor_empenho,
    case when payload ->> 'aliquidar' ~ '^[+-]?\d+(\.\d+)?$' then (payload ->> 'aliquidar')::numeric end as aliquidar,
    case when payload ->> 'liquidado' ~ '^[+-]?\d+(\.\d+)?$' then (payload ->> 'liquidado')::numeric end as liquidado,
    case when payload ->> 'pago' ~ '^[+-]?\d+(\.\d+)?$' then (payload ->> 'pago')::numeric end as pago,
    case when payload ->> 'rpinscrito' ~ '^[+-]?\d+(\.\d+)?$' then (payload ->> 'rpinscrito')::numeric end as rpinscrito,
    case when payload ->> 'rpaliquidar' ~ '^[+-]?\d+(\.\d+)?$' then (payload ->> 'rpaliquidar')::numeric end as rpaliquidar,
    case when payload ->> 'rpaliquidado' ~ '^[+-]?\d+(\.\d+)?$' then (payload ->> 'rpaliquidado')::numeric end as rpaliquidado,
    case when payload ->> 'rppago' ~ '^[+-]?\d+(\.\d+)?$' then (payload ->> 'rppago')::numeric end as rppago,
    record_hash::text as source_record_hash, fetched_at::timestamptz as source_fetched_at
from ranked where dedupe_rank = 1
