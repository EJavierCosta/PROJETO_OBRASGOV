select distinct
    organization_key::text as organization_key,
    organization_name::text as organization_name,
    organization_cnpj::text as organization_cnpj
from {{ ref('fct_project_snapshot') }}
