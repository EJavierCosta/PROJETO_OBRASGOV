with ranked as (
    select *, row_number() over (
        partition by ingestion_id, nullif(trim(payload ->> 'id_projeto_investimento'), ''),
            coalesce(nullif(trim(payload ->> 'id_contrato'), ''), record_hash)
        order by fetched_at desc, page_number desc, record_index desc
    ) as dedupe_rank
    from {{ source('bronze', 'obrasgov_contract_raw') }}
)
select
    md5(concat_ws('||', ingestion_id::text, payload ->> 'id_projeto_investimento', coalesce(payload ->> 'id_contrato', record_hash)))::text as contract_key,
    ingestion_id::uuid, nullif(trim(payload ->> 'id_projeto_investimento'), '')::text as project_id,
    nullif(trim(payload ->> 'id_contrato'), '')::text as contract_source_id,
    nullif(trim(payload ->> 'numero_contrato'), '')::text as contract_number,
    nullif(trim(payload ->> 'fornecedor_contrato'), '')::text as supplier_name,
    nullif(trim(payload ->> 'cnpj_fornecedor_contrato'), '')::text as supplier_cnpj,
    nullif(trim(payload ->> 'situacao_contrato'), '')::text as contract_status,
    nullif(trim(payload ->> 'objeto_contrato'), '')::text as contract_object,
    nullif(trim(payload ->> 'processo'), '')::text as process_number,
    nullif(trim(payload ->> 'modalidade_contrato'), '')::text as modality,
    nullif(trim(payload ->> 'orgao_contrato'), '')::text as organization_name,
    nullif(trim(payload ->> 'categoria_contrato'), '')::text as category,
    nullif(trim(payload ->> 'licitacao_numero'), '')::text as procurement_number,
    nullif(trim(payload ->> 'link_transparencia'), '')::text as transparency_link,
    case when payload ->> 'vigencia_inicio_contrato' ~ '^\d{4}-\d{2}-\d{2}$' then (payload ->> 'vigencia_inicio_contrato')::date end as validity_start_date,
    case when payload ->> 'vigencia_fim_contrato' ~ '^\d{4}-\d{2}-\d{2}$' then (payload ->> 'vigencia_fim_contrato')::date end as validity_end_date,
    case when payload ->> 'valor_global_contrato' ~ '^[+-]?\d+(\.\d+)?$' then (payload ->> 'valor_global_contrato')::numeric end as valor_global_contrato,
    case when payload ->> 'valor_acumulado_contrato' ~ '^[+-]?\d+(\.\d+)?$' then (payload ->> 'valor_acumulado_contrato')::numeric end as valor_acumulado_contrato,
    case when payload ->> 'valor_utilizado_pi_contrato' ~ '^[+-]?\d+(\.\d+)?$' then (payload ->> 'valor_utilizado_pi_contrato')::numeric end as valor_utilizado_pi_contrato,
    case when payload ->> 'valor_incluido_contrato' ~ '^[+-]?\d+(\.\d+)?$' then (payload ->> 'valor_incluido_contrato')::numeric end as valor_incluido_contrato,
    record_hash::text as source_record_hash, fetched_at::timestamptz as source_fetched_at
from ranked where dedupe_rank = 1
