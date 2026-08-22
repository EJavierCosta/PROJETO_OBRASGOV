select
    location.location_key::text as location_key,
    location.ingestion_id::uuid as ingestion_id,
    location.geometry_id::integer as geometry_id,
    location.municipality_name::text as municipality_name,
    location.ibge_code::bigint as ibge_code,
    location.uf::text as uf,
    location.geometry_origin::text as geometry_origin
from {{ ref('stg_obrasgov_geometry') }} as location
inner join {{ ref('fct_project_snapshot') }} as project
    on location.ingestion_id = project.ingestion_id
   and location.project_id = project.project_id
