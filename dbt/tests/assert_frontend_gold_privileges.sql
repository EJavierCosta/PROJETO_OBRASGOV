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
          'vw_status_distribution_current',
          'vw_snapshot_metadata_current'
      )
  )
