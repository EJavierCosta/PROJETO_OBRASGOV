select
    table_name,
    privilege_type
from information_schema.role_table_grants
where grantee = 'obrasgov_frontend'
  and table_schema = 'gold'
  and (
      privilege_type <> 'SELECT'
      or table_name not in (
          'vw_market_overview_current',
          'vw_project_investment_current',
          'vw_project_location_current',
          'vw_project_detail_current',
          'vw_project_participant_current',
          'vw_project_axis_type_current',
          'vw_project_ppa_current',
          'vw_project_restriction_area_current',
          'vw_project_photo_indicator_current',
          'vw_project_contract_current',
          'vw_project_commitment_current',
          'vw_project_commitment_totals_current',
          'vw_project_execution_current',
          'vw_project_status_history_current',
          'vw_project_feasibility_study_current',
          'vw_project_coverage_current',
          'vw_status_distribution_current',
          'vw_snapshot_metadata_current'
      )
  )
