select project_snapshot_key, participant_role
from {{ ref('int_obrasgov_project_participant') }}
where nullif(trim(coalesce(organization_name, '')), '') is null
  and nullif(trim(coalesce(organization_cnpj, '')), '') is null
