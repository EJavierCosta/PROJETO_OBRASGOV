select
    project_id,
    municipality_name,
    ibge_code,
    ingestion_id,
    latitude,
    longitude
from {{ ref('vw_project_location_current') }}
where (latitude is null) <> (longitude is null)
