with failures as (
    select 'contract_without_project_snapshot' as failure_type, contract.contract_key as record_key
    from {{ ref('fct_contract') }} as contract
    left join {{ ref('fct_project_snapshot') }} as project
        on project.project_snapshot_key = contract.project_snapshot_key
    where project.project_snapshot_key is null

    union all

    select 'commitment_without_project_snapshot', commitment.commitment_key
    from {{ ref('fct_commitment') }} as commitment
    left join {{ ref('fct_project_snapshot') }} as project
        on project.project_snapshot_key = commitment.project_snapshot_key
    where project.project_snapshot_key is null

    union all

    select 'physical_execution_without_project_snapshot', execution.physical_execution_key
    from {{ ref('fct_physical_execution') }} as execution
    left join {{ ref('fct_project_snapshot') }} as project
        on project.project_snapshot_key = execution.project_snapshot_key
    where project.project_snapshot_key is null

    union all

    select 'status_event_without_project_snapshot', event.status_event_key
    from {{ ref('fct_status_event') }} as event
    left join {{ ref('fct_project_snapshot') }} as project
        on project.project_snapshot_key = event.project_snapshot_key
    where project.project_snapshot_key is null

    union all

    select 'feasibility_study_without_project_snapshot', study.study_key
    from {{ ref('fct_feasibility_study') }} as study
    left join {{ ref('fct_project_snapshot') }} as project
        on project.project_snapshot_key = study.project_snapshot_key
    where project.project_snapshot_key is null

    union all

    select 'participant_without_project_snapshot', participant.project_participant_key
    from {{ ref('bridge_project_participant') }} as participant
    left join {{ ref('fct_project_snapshot') }} as project
        on project.project_snapshot_key = participant.project_snapshot_key
    where project.project_snapshot_key is null

    union all

    select 'ppa_without_project_snapshot', ppa.project_ppa_key
    from {{ ref('bridge_project_ppa') }} as ppa
    left join {{ ref('fct_project_snapshot') }} as project
        on project.project_snapshot_key = ppa.project_snapshot_key
    where project.project_snapshot_key is null

    union all

    select 'restriction_without_project_snapshot', restriction.project_restriction_area_key
    from {{ ref('bridge_project_restriction_area') }} as restriction
    left join {{ ref('fct_project_snapshot') }} as project
        on project.project_snapshot_key = restriction.project_snapshot_key
    where project.project_snapshot_key is null

    union all

    select 'photo_indicator_without_project_snapshot', photo.project_photo_indicator_key
    from {{ ref('bridge_project_photo_indicator') }} as photo
    left join {{ ref('fct_project_snapshot') }} as project
        on project.project_snapshot_key = photo.project_snapshot_key
    where project.project_snapshot_key is null

    union all

    select 'contract_without_supplier_dimension', contract.contract_key
    from {{ ref('fct_contract') }} as contract
    left join {{ ref('dim_supplier') }} as supplier using (supplier_key)
    where supplier.supplier_key is null

    union all

    select 'ppa_without_dimension', ppa.project_ppa_key
    from {{ ref('bridge_project_ppa') }} as ppa
    left join {{ ref('dim_ppa') }} as dimension using (ppa_key)
    where dimension.ppa_key is null

    union all

    select 'restriction_without_dimension', restriction.project_restriction_area_key
    from {{ ref('bridge_project_restriction_area') }} as restriction
    left join {{ ref('dim_restriction_area') }} as dimension using (restriction_area_key)
    where dimension.restriction_area_key is null

    union all

    select 'physical_execution_invalid_source_count', execution.physical_execution_key
    from {{ ref('fct_physical_execution') }} as execution
    where execution.source_record_count < 1

    union all

    select 'physical_execution_percentage_out_of_range', execution.physical_execution_key
    from {{ ref('fct_physical_execution') }} as execution
    where execution.physical_execution_percentage < 0
        or execution.physical_execution_percentage > 100

    union all

    select 'coverage_display_exceeds_source', coverage.project_id || ':' || coverage.section_name
    from {{ ref('vw_project_coverage_current') }} as coverage
    where coverage.display_record_count > coverage.source_record_count

    union all

    select 'coverage_has_data_mismatch', coverage.project_id || ':' || coverage.section_name
    from {{ ref('vw_project_coverage_current') }} as coverage
    where coverage.has_data is distinct from (coverage.display_record_count > 0)

    union all

    select 'status_history_semantic_duplicate', history.project_id || ':' || history.semantic_key
    from {{ ref('vw_project_status_history_current') }} as history
    group by history.project_id, history.semantic_key, history.ingestion_id
    having count(*) > 1
)
select failure_type, record_key
from failures
