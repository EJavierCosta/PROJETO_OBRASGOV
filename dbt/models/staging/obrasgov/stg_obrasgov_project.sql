with raw_projects as (
    select
        ingestion_id,
        page_number,
        page_size,
        record_index,
        payload,
        record_hash,
        fetched_at,
        nullif(trim(payload ->> 'id_projeto_investimento'), '') as project_id
    from {{ source('bronze', 'obrasgov_project_raw') }}
),

ranked_projects as (
    select
        *,
        row_number() over (
            partition by ingestion_id, coalesce(project_id, record_hash)
            order by fetched_at desc, page_number desc, record_index desc
        ) as dedupe_rank
    from raw_projects
)

select
    md5(concat_ws('||', ingestion_id::text, coalesce(project_id, record_hash))) as project_snapshot_key,
    ingestion_id::uuid as ingestion_id,
    project_id::text as project_id,
    nullif(trim(payload ->> 'desc_nome'), '')::text as project_name,
    nullif(trim(payload ->> 'desc_projeto'), '')::text as project_description,
    nullif(trim(payload ->> 'situacao'), '')::text as source_status,
    nullif(trim(payload ->> 'uf_principal'), '')::text as uf_principal,
    nullif(trim(payload ->> 'natureza_intervencao'), '')::text as nature_intervention,
    nullif(trim(payload ->> 'especie_intervencao'), '')::text as species_intervention,
    case
        when nullif(trim(payload ->> 'id_natureza_intervencao'), '') ~ '^[+-]?[0-9]+$'
            then (payload ->> 'id_natureza_intervencao')::integer
    end as nature_intervention_id,
    case
        when nullif(trim(payload ->> 'id_especie_intervencao'), '') ~ '^[+-]?[0-9]+$'
            then (payload ->> 'id_especie_intervencao')::integer
    end as species_intervention_id,
    nullif(trim(payload ->> 'organizacao_resp'), '')::text as organization_name,
    nullif(trim(payload ->> 'cnpj_organizacao_resp'), '')::text as organization_cnpj,
    case
        when nullif(trim(payload ->> 'dt_cadastro'), '') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
            then (payload ->> 'dt_cadastro')::date
    end as registration_date,
    case
        when nullif(trim(payload ->> 'ano_cadastro'), '') ~ '^[0-9]{4}$'
            then (payload ->> 'ano_cadastro')::integer
    end as registration_year,
    case
        when nullif(trim(payload ->> 'dt_inicial_prevista'), '') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
            then (payload ->> 'dt_inicial_prevista')::date
    end as expected_start_date,
    case
        when nullif(trim(payload ->> 'dt_final_prevista'), '') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
            then (payload ->> 'dt_final_prevista')::date
    end as expected_end_date,
    case
        when nullif(trim(payload ->> 'dt_inicial_efetiva'), '') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
            then (payload ->> 'dt_inicial_efetiva')::date
    end as actual_start_date,
    case
        when nullif(trim(payload ->> 'dt_final_efetiva'), '') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
            then (payload ->> 'dt_final_efetiva')::date
    end as actual_end_date,
    nullif(trim(payload ->> 'projeto_estruturante'), '')::text as structural_project_indicator,
    nullif(trim(payload ->> 'nr_cep'), '')::text as postal_code,
    nullif(trim(payload ->> 'desc_endereco'), '')::text as address_description,
    nullif(trim(payload ->> 'desc_funcao_social'), '')::text as social_function_description,
    nullif(trim(payload ->> 'desc_meta_global'), '')::text as global_goal_description,
    case
        when nullif(trim(payload ->> 'populacao_beneficiada'), '') ~ '^[+-]?[0-9]+$'
            then (payload ->> 'populacao_beneficiada')::integer
    end as benefited_population,
    nullif(trim(payload ->> 'desc_populacao_beneficiada'), '')::text as benefited_population_description,
    case
        when nullif(trim(payload ->> 'qtd_empregos_gerados'), '') ~ '^[+-]?[0-9]+$'
            then (payload ->> 'qtd_empregos_gerados')::integer
    end as jobs_created_count,
    case
        when nullif(trim(payload ->> 'ind_bim'), '') ~ '^[+-]?[0-9]+$'
            then (payload ->> 'ind_bim')::integer
    end as bim_indicator,
    nullif(trim(payload ->> 'obs_pertinentes_intervencao'), '')::text as intervention_notes,
    nullif(trim(payload ->> 'sistema_resp'), '')::text as source_system,
    nullif(trim(payload ->> 'possui_estudo_viabilidade'), '')::text as feasibility_study_indicator,
    case
        when jsonb_typeof(payload -> 'investimentos_previstos') = 'array'
            then payload -> 'investimentos_previstos'
        else '[]'::jsonb
    end as planned_investments,
    case
        when jsonb_typeof(payload -> 'eixos_tipos') = 'array'
            then payload -> 'eixos_tipos'
        else '[]'::jsonb
    end as axis_types,
    case
        when jsonb_typeof(payload -> 'pins') = 'array'
            then payload -> 'pins'
        else '[]'::jsonb
    end as pins,
    record_hash::text as source_record_hash,
    page_number::integer as source_page_number,
    page_size::integer as source_page_size,
    record_index::integer as source_record_index,
    fetched_at::timestamp with time zone as source_fetched_at
from ranked_projects
where dedupe_rank = 1
