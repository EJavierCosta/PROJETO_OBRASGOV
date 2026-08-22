select
    pin.pin_key::text as pin_key,
    pin.ingestion_id::uuid as ingestion_id,
    pin.pin_name::text as pin_name,
    pin.latitude::numeric as latitude,
    pin.longitude::numeric as longitude
from {{ ref('int_obrasgov_project_pin') }} as pin
inner join {{ ref('fct_project_snapshot') }} as project
    on pin.project_snapshot_key = project.project_snapshot_key
