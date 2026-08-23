{{ config(materialized='view', grants={'select': ['obrasgov_frontend', 'obrasgov_chat']}) }}

with current as (
    select ingestion_id
    from {{ ref('int_obrasgov_current_ingestion') }}
),
projects as (
    select project.project_id, project.ingestion_id, project.feasibility_study_indicator,
        project.source_updated_at, project.ingested_at
    from {{ ref('fct_project_snapshot') }} as project
    inner join current using (ingestion_id)
),
status_source as (
    select event.project_id, event.ingestion_id, count(*)::bigint as source_record_count
    from {{ ref('fct_status_event') }} as event
    inner join current using (ingestion_id)
    group by event.project_id, event.ingestion_id
),
status_display as (
    select history.project_id, history.ingestion_id, count(*)::bigint as display_record_count
    from {{ ref('vw_project_status_history_current') }} as history
    group by history.project_id, history.ingestion_id
),
counts as (
    select contract.project_id, contract.ingestion_id, 'contract'::text as section_name,
        count(*)::bigint as source_record_count, count(*)::bigint as display_record_count
    from {{ ref('fct_contract') }} as contract
    inner join current using (ingestion_id)
    group by contract.project_id, contract.ingestion_id

    union all

    select commitment.project_id, commitment.ingestion_id, 'commitment'::text,
        count(*)::bigint, count(*)::bigint
    from {{ ref('fct_commitment') }} as commitment
    inner join current using (ingestion_id)
    group by commitment.project_id, commitment.ingestion_id

    union all

    select execution.project_id, execution.ingestion_id, 'physical_execution'::text,
        sum(execution.source_record_count)::bigint, count(*)::bigint
    from {{ ref('fct_physical_execution') }} as execution
    inner join current using (ingestion_id)
    group by execution.project_id, execution.ingestion_id

    union all

    select source.project_id, source.ingestion_id, 'status_history'::text,
        source.source_record_count, coalesce(display.display_record_count, 0)::bigint
    from status_source as source
    left join status_display as display
        on display.project_id = source.project_id
        and display.ingestion_id = source.ingestion_id

    union all

    select study.project_id, study.ingestion_id, 'feasibility_study'::text,
        count(*)::bigint, count(*)::bigint
    from {{ ref('fct_feasibility_study') }} as study
    inner join current using (ingestion_id)
    group by study.project_id, study.ingestion_id
),
sections as (
    select *
    from (values
        ('contract'::text),
        ('commitment'::text),
        ('physical_execution'::text),
        ('status_history'::text),
        ('feasibility_study'::text)
    ) as values_table(section_name)
)
select projects.project_id::text,
    sections.section_name,
    coalesce(counts.source_record_count, 0)::bigint as source_record_count,
    coalesce(counts.display_record_count, 0)::bigint as display_record_count,
    (coalesce(counts.display_record_count, 0) > 0) as has_data,
    case when coalesce(counts.display_record_count, 0) > 0
        then 'available' else 'not_informed_by_source' end::text as coverage_status,
    projects.feasibility_study_indicator::text as project_feasibility_study_indicator,
    projects.source_updated_at::timestamptz,
    projects.ingested_at::timestamptz,
    projects.ingestion_id::uuid
from projects
cross join sections
left join counts
    on counts.project_id = projects.project_id
    and counts.ingestion_id = projects.ingestion_id
    and counts.section_name = sections.section_name
