select
    md5(concat_ws('||', project.project_snapshot_key, location.location_key))::text
        as project_location_key,
    project.project_snapshot_key::text as project_snapshot_key,
    project.ingestion_id::uuid as ingestion_id,
    project.project_id::text as project_id,
    location.location_key::text as location_key
from {{ ref('fct_project_snapshot') }} as project
inner join {{ ref('stg_obrasgov_geometry') }} as location
    on project.ingestion_id = location.ingestion_id
   and project.project_id = location.project_id
