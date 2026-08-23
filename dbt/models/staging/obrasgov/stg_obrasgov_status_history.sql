with ranked as (
    select *, row_number() over (partition by ingestion_id, payload ->> 'id_projeto_investimento', coalesce(payload ->> 'id_historico_situacao_investimento', record_hash) order by fetched_at desc, record_hash desc) as dedupe_rank
    from {{ source('bronze', 'obrasgov_status_history_raw') }}
)
select md5(concat_ws('||', ingestion_id::text, payload ->> 'id_historico_situacao_investimento', record_hash))::text as status_event_key,
    ingestion_id::uuid, nullif(trim(payload ->> 'id_projeto_investimento'), '')::text as project_id,
    nullif(trim(payload ->> 'id_historico_situacao_investimento'), '')::text as status_event_source_id,
    case when payload ->> 'data_historico_situacao_investimento' ~ '^\d{4}-\d{2}-\d{2}$' then (payload ->> 'data_historico_situacao_investimento')::date end as event_date,
    nullif(trim(payload ->> 'descricao_historico_situacao_investimento'), '')::text as source_status, nullif(trim(payload ->> 'justificativa_cancelada_paralisada'), '')::text as justification,
    nullif(trim(payload ->> 'possui_tratativas_situacao_investimento'), '')::text as treatment_indicator, nullif(trim(payload ->> 'fase_tratativas_situacao_investimento'), '')::text as treatment_phase,
    record_hash::text as source_record_hash, fetched_at::timestamptz as source_fetched_at
from ranked where dedupe_rank = 1
