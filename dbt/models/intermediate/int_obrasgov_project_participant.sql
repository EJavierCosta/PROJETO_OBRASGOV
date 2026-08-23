with participant_arrays as (
    select project_snapshot_key, ingestion_id, project_id, 'responsible'::text as participant_role,
        jsonb_build_array(jsonb_build_object('name', organization_name, 'cnpj', organization_cnpj)) as participants
    from {{ ref('stg_obrasgov_project') }}
    union all
    select project_snapshot_key, ingestion_id, project_id, 'transferor', coalesce(case when jsonb_typeof(repassadores) = 'array' then repassadores end, '[]'::jsonb)
    from {{ ref('stg_obrasgov_project') }}
    union all
    select project_snapshot_key, ingestion_id, project_id, 'recipient', coalesce(case when jsonb_typeof(tomadores) = 'array' then tomadores end, '[]'::jsonb)
    from {{ ref('stg_obrasgov_project') }}
    union all
    select project_snapshot_key, ingestion_id, project_id, 'executor', coalesce(case when jsonb_typeof(executores) = 'array' then executores end, '[]'::jsonb)
    from {{ ref('stg_obrasgov_project') }}
), exploded as (
    select *,
        coalesce(
            nullif(trim(participant ->> 'nome'), ''),
            nullif(trim(participant ->> 'name'), ''),
            nullif(trim(participant ->> 'organizacao_repassador'), ''),
            nullif(trim(participant ->> 'organizacao_tomador'), ''),
            nullif(trim(participant ->> 'organizacao_executor'), '')
        ) as organization_name,
        coalesce(
            nullif(trim(participant ->> 'cnpj'), ''),
            nullif(trim(participant ->> 'cnpj_repassador'), ''),
            nullif(trim(participant ->> 'cnpj_tomador'), ''),
            nullif(trim(participant ->> 'cnpj_executor'), '')
        ) as organization_cnpj
    from participant_arrays cross join lateral jsonb_array_elements(participants) as item(participant)
), ranked as (
    select *, row_number() over (partition by project_snapshot_key, participant_role, {{ obrasgov_organization_key('organization_cnpj', 'organization_name') }} order by organization_name) as dedupe_rank,
        count(*) over (partition by project_snapshot_key, participant_role, {{ obrasgov_organization_key('organization_cnpj', 'organization_name') }}) as source_participant_count
    from exploded where organization_name is not null or organization_cnpj is not null
)
select md5(concat_ws('||', project_snapshot_key, participant_role, {{ obrasgov_organization_key('organization_cnpj', 'organization_name') }}))::text as project_participant_key,
    project_snapshot_key::text, ingestion_id::uuid, project_id::text, participant_role::text,
    {{ obrasgov_organization_key('organization_cnpj', 'organization_name') }}::text as organization_key,
    organization_name::text, organization_cnpj::text, source_participant_count::bigint
from ranked where dedupe_rank = 1
