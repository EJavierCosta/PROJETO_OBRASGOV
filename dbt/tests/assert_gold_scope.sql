select
    project_snapshot_key,
    ingestion_id,
    project_id,
    uf_principal,
    nature_intervention,
    species_intervention
from {{ ref('fct_project_snapshot') }}
where uf_principal is distinct from 'CE'
   or nature_intervention is distinct from 'Obra'
   or species_intervention is distinct from 'Construção'
