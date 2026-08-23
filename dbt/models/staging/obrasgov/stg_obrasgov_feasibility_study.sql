with typed as (
    select ingestion_id, payload, record_hash, fetched_at, nullif(trim(payload ->> 'id_projeto_investimento'), '') as project_id,
        nullif(trim(payload ->> 'tipo_estudo_viabilidade'), '') as study_type, nullif(trim(payload ->> 'especificacao_estudo_viabilidade'), '') as study_specification
    from {{ source('bronze', 'obrasgov_feasibility_study_raw') }}
), ranked as (
    select *, row_number() over (partition by ingestion_id, project_id, study_type, {{ obrasgov_normalize('study_specification') }} order by fetched_at desc, record_hash desc) as dedupe_rank from typed
)
select md5(concat_ws('||', ingestion_id::text, project_id, coalesce(study_type, '∅'), coalesce({{ obrasgov_normalize('study_specification') }}, '∅')))::text as study_key,
    ingestion_id::uuid, project_id::text, study_type::text, study_specification::text, record_hash::text as source_record_hash, fetched_at::timestamptz as source_fetched_at
from ranked where dedupe_rank = 1
