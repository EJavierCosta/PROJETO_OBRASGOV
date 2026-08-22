select
    md5(concat_ws('||', project.project_snapshot_key, pin.pin_key))::text as project_pin_key,
    project.project_snapshot_key::text as project_snapshot_key,
    project.ingestion_id::uuid as ingestion_id,
    pin.pin_key::text as pin_key
from {{ ref('fct_project_snapshot') }} as project
inner join {{ ref('int_obrasgov_project_pin') }} as pin
    on project.project_snapshot_key = pin.project_snapshot_key
