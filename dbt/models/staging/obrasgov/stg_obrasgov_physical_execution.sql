with ranked as (
    select *,
        row_number() over (
            partition by ingestion_id, payload ->> 'id_projeto_investimento',
                coalesce(payload ->> 'id_execucao_fisica', record_hash)
            order by fetched_at desc, record_hash desc
        ) as dedupe_rank,
        count(*) over (
            partition by ingestion_id, payload ->> 'id_projeto_investimento',
                coalesce(payload ->> 'id_execucao_fisica', record_hash)
        ) as source_record_count
    from {{ source('bronze', 'obrasgov_physical_execution_raw') }}
)
select md5(concat_ws('||', ingestion_id::text, payload ->> 'id_projeto_investimento', coalesce(payload ->> 'id_execucao_fisica', record_hash)))::text as physical_execution_key,
    ingestion_id::uuid, nullif(trim(payload ->> 'id_projeto_investimento'), '')::text as project_id,
    nullif(trim(payload ->> 'id_execucao_fisica'), '')::text as id_execucao_fisica,
    nullif(trim(payload ->> 'tipo_instrumento'), '')::text as instrument, nullif(trim(payload ->> 'tipo_forma_execucao'), '')::text as execution_form,
    case when payload ->> 'percentual_execucao_fisica' ~ '^[+-]?\d+(\.\d+)?$' then (payload ->> 'percentual_execucao_fisica')::numeric end as physical_execution_percentage,
    case when payload ->> 'dt_cadastro_execucao' ~ '^\d{4}-\d{2}-\d{2}T' then (payload ->> 'dt_cadastro_execucao')::timestamp end as execution_registration_at,
    case when payload ->> 'dt_inicial_execucao' ~ '^\d{4}-\d{2}-\d{2}$' then (payload ->> 'dt_inicial_execucao')::date end as execution_start_date,
    case when payload ->> 'dt_final_execucao' ~ '^\d{4}-\d{2}-\d{2}$' then (payload ->> 'dt_final_execucao')::date end as execution_end_date,
    case when payload ->> 'dt_criacao_instrumento' ~ '^\d{4}-\d{2}-\d{2}$' then (payload ->> 'dt_criacao_instrumento')::date end as instrument_creation_date,
    case when payload ->> 'dt_atualizacao_execucao' ~ '^\d{4}-\d{2}-\d{2}$' then (payload ->> 'dt_atualizacao_execucao')::date end as source_update_date,
    coalesce(payload -> 'indicativos', '[]'::jsonb) as indicators, coalesce(payload -> 'motivos', '[]'::jsonb) as reasons,
    source_record_count::bigint, record_hash::text as source_record_hash, fetched_at::timestamptz as source_fetched_at
from ranked where dedupe_rank = 1
