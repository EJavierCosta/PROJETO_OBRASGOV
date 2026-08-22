select distinct
    intervention_key::text as intervention_key,
    nature_intervention_id::integer as nature_intervention_id,
    nature_intervention::text as nature_intervention,
    species_intervention_id::integer as species_intervention_id,
    species_intervention::text as species_intervention
from {{ ref('fct_project_snapshot') }}
