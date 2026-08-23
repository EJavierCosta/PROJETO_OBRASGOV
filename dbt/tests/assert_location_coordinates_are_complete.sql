select
    project_id,
    municipality_name,
    ibge_code,
    ingestion_id,
    latitude,
    longitude
from {{ ref('vw_project_location_current') }}
where (latitude is not null and (latitude < -90 or latitude > 90))
   or (longitude is not null and (longitude < -180 or longitude > 180))
