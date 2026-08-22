select
    'planned_investment_without_same_snapshot_project' as failure_type,
    investment.project_snapshot_key,
    investment.ingestion_id,
    investment.project_id
from {{ ref('fct_planned_investment') }} as investment
left join {{ ref('fct_project_snapshot') }} as project
    on investment.project_snapshot_key = project.project_snapshot_key
   and investment.ingestion_id = project.ingestion_id
   and investment.project_id = project.project_id
where project.project_snapshot_key is null

union all

select
    'axis_bridge_without_same_snapshot_project' as failure_type,
    bridge.project_snapshot_key,
    bridge.ingestion_id,
    null::text as project_id
from {{ ref('bridge_project_axis_type') }} as bridge
left join {{ ref('fct_project_snapshot') }} as project
    on bridge.project_snapshot_key = project.project_snapshot_key
   and bridge.ingestion_id = project.ingestion_id
where project.project_snapshot_key is null

union all

select
    'location_bridge_without_same_snapshot_project' as failure_type,
    bridge.project_snapshot_key,
    bridge.ingestion_id,
    bridge.project_id
from {{ ref('bridge_project_location') }} as bridge
left join {{ ref('fct_project_snapshot') }} as project
    on bridge.project_snapshot_key = project.project_snapshot_key
   and bridge.ingestion_id = project.ingestion_id
   and bridge.project_id = project.project_id
where project.project_snapshot_key is null

union all

select
    'pin_bridge_without_same_snapshot_project' as failure_type,
    bridge.project_snapshot_key,
    bridge.ingestion_id,
    null::text as project_id
from {{ ref('bridge_project_pin') }} as bridge
left join {{ ref('fct_project_snapshot') }} as project
    on bridge.project_snapshot_key = project.project_snapshot_key
   and bridge.ingestion_id = project.ingestion_id
where project.project_snapshot_key is null
