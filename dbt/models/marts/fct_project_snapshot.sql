with scoped_projects as (
    select
        project.*,
        run.source_updated_at,
        run.ingested_at
    from {{ ref('stg_obrasgov_project') }} as project
    inner join {{ ref('stg_obrasgov_ingestion_run') }} as run
        on project.ingestion_id = run.ingestion_id
    where project.project_id is not null
      and run.ingestion_status = 'succeeded'
      and project.uf_principal = 'CE'
      and project.nature_intervention = 'Obra'
      and project.species_intervention = 'Construção'
)

select
    project_snapshot_key::text as project_snapshot_key,
    ingestion_id::uuid as ingestion_id,
    project_id::text as project_id,
    {{ obrasgov_organization_key('organization_cnpj', 'organization_name') }}::text as organization_key,
    md5(
        concat_ws(
            '||',
            coalesce(nature_intervention, '∅'),
            coalesce(species_intervention, '∅')
        )
    )::text as intervention_key,
    project_name::text as project_name,
    project_description::text as project_description,
    source_status::text as source_status,
    uf_principal::text as uf_principal,
    nature_intervention::text as nature_intervention,
    species_intervention::text as species_intervention,
    nature_intervention_id::integer as nature_intervention_id,
    species_intervention_id::integer as species_intervention_id,
    organization_name::text as organization_name,
    organization_cnpj::text as organization_cnpj,
    registration_date::date as registration_date,
    registration_year::integer as registration_year,
    expected_start_date::date as expected_start_date,
    expected_end_date::date as expected_end_date,
    actual_start_date::date as actual_start_date,
    actual_end_date::date as actual_end_date,
    structural_project_indicator::text as structural_project_indicator,
    postal_code::text as postal_code,
    address_description::text as address_description,
    social_function_description::text as social_function_description,
    global_goal_description::text as global_goal_description,
    benefited_population::integer as benefited_population,
    benefited_population_description::text as benefited_population_description,
    jobs_created_count::integer as jobs_created_count,
    bim_indicator::integer as bim_indicator,
    intervention_notes::text as intervention_notes,
    source_system::text as source_system,
    feasibility_study_indicator::text as feasibility_study_indicator,
    source_updated_at::timestamp with time zone as source_updated_at,
    ingested_at::timestamp with time zone as ingested_at
from scoped_projects
